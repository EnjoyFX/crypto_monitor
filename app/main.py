import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta, timezone
import httpx

from app import crud, models, schemas
from app.database import engine, get_db
from app.settings import cfg


app = FastAPI()
scheduler = AsyncIOScheduler()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS support
origins = [
    "http://localhost",
    "http://localhost:8001",
    "http://localhost:63342",
    "http://192.168.0.60:8001"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)


async def fetch_and_store_rates():
    logger.info("Fetching and storing rates...")
    async with httpx.AsyncClient() as client:
        response = await client.get(cfg.API_URL)
        response.raise_for_status()
        data = response.json()
        async with AsyncSession(engine) as session:
            async with session.begin():
                timestamp = datetime.now(timezone.utc)
                all_rates = []
                selected_rates = []

                result = await session.execute(select(models.Currency))
                currencies = result.scalars().all()
                needed_symbols = {currency.symbol for currency in currencies}

                for item in data:
                    symbol = item['symbol']
                    price = float(item['price'])
                    all_rates.append(
                        models.CurrencyRateAll(symbol=symbol,
                                               price=price,
                                               timestamp=timestamp)
                    )
                    if symbol in needed_symbols:
                        selected_rates.append(
                            models.CurrencyRate(symbol=symbol,
                                                price=price,
                                                timestamp=timestamp)
                        )

                session.add_all(all_rates)
                session.add_all(selected_rates)

            await session.commit()
            logger.info("Stored all rates and selected rates")


@app.on_event("startup")
async def on_startup():
    await init_models()
    logger.info("Database initialized.")
    scheduler.start()
    logger.info("Scheduler started.")
    for job in scheduler.get_jobs():
        logger.info(f"Scheduled job: {job}")


@app.post("/currencies/", response_model=schemas.CurrencyCreate)
async def create_currency(currency: schemas.CurrencyCreate,
                          db: AsyncSession = Depends(get_db)):
    db_currency = await crud.get_currency(db, symbol=currency.symbol)
    if db_currency:
        raise HTTPException(status_code=400, detail="Currency already registered")
    return await crud.create_currency(db=db, symbol=currency.symbol)


@app.get("/currencies/", response_model=list[schemas.CurrencyCreate])
async def read_currencies(skip: int = 0, limit: int = 10,
                          db: AsyncSession = Depends(get_db)):
    currencies = await crud.get_currencies(db, skip=skip, limit=limit)
    return currencies


@app.delete("/currencies/{symbol}", response_model=schemas.CurrencyCreate)
async def delete_currency(symbol: str, db: AsyncSession = Depends(get_db)):
    db_currency = await crud.get_currency(db, symbol=symbol)
    if db_currency is None:
        raise HTTPException(status_code=404, detail="Currency not found")
    return await crud.delete_currency(db=db, symbol=symbol)


@app.get("/currency_rate_all/count", response_model=int)
async def get_currency_rate_all_count(db: AsyncSession = Depends(get_db)):
    count = await crud.get_currency_rate_all_count(db)
    return count


@app.get("/analysis/{period}", response_model=list[schemas.CurrencyRateCreate])
async def analyze_currency_rates(period: str, db: AsyncSession = Depends(get_db)):
    end_time = datetime.now(timezone.utc)
    if period == "hourly":
        start_time = end_time - timedelta(hours=1)
    elif period == "4hourly":
        start_time = end_time - timedelta(hours=4)
    elif period == "daily":
        start_time = end_time - timedelta(days=1)
    elif period == "weekly":
        start_time = end_time - timedelta(weeks=1)
    elif period == "yearly":
        start_time = end_time - timedelta(weeks=52)
    else:
        raise HTTPException(status_code=400, detail="Invalid period specified")

    rates = await crud.analyze_currency_rates(db,
                                              start_time=start_time,
                                              end_time=end_time)
    return rates


@app.get("/rates/{symbol}", response_model=list[schemas.CurrencyRateCreate])
async def get_exchange_rates(symbol: str, periods: int, db: AsyncSession = Depends(get_db)):
    query = text("""
        SELECT symbol, price, timestamp
        FROM currency_rates_all
        WHERE symbol = :symbol
        ORDER BY timestamp DESC
        LIMIT :periods
    """)

    rates = await db.execute(query, {'symbol': symbol, 'periods': periods})
    rows = rates.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="Symbol not found")

    rates = [schemas.CurrencyRateCreate(symbol=row[0],
                                        price=row[1],
                                        timestamp=row[2]) for row in rows]
    return rates


if __name__ == "__main__":
    now_is = datetime.now(timezone.utc)
    calc_start = (now_is + timedelta(seconds=60 - now_is.second)).replace(microsecond=0)
    rates_trigger = IntervalTrigger(
        minutes=cfg.INTERVAL_IN_MINUTES,
        start_date=calc_start
    )

    scheduler.add_job(fetch_and_store_rates, trigger=rates_trigger)
    logger.info("Job added to scheduler.")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
