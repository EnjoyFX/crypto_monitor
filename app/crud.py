# app/crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy.sql import func
from app.models import Currency, CurrencyRate, CurrencyRateAll
from datetime import datetime


async def get_currency(db: AsyncSession, symbol: str):
    result = await db.execute(select(Currency).filter(Currency.symbol == symbol))
    return result.scalars().first()


async def create_currency(db: AsyncSession, symbol: str):
    db_currency = Currency(symbol=symbol)
    db.add(db_currency)
    await db.commit()
    await db.refresh(db_currency)
    return db_currency


async def get_currencies(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(Currency).offset(skip).limit(limit))
    return result.scalars().all()


async def delete_currency(db: AsyncSession, symbol: str):
    currency = await get_currency(db, symbol=symbol)
    if currency:
        await db.execute(delete(Currency).where(Currency.symbol == symbol))
        await db.commit()
    return currency


async def create_currency_rate(db: AsyncSession, symbol: str, price: float, timestamp: datetime):
    db_rate = CurrencyRate(symbol=symbol, price=price, timestamp=timestamp)
    db.add(db_rate)
    await db.commit()
    return db_rate


async def create_currency_rate_all(db: AsyncSession,
                                   symbol: str,
                                   price: float,
                                   timestamp: datetime):
    db_rate_all = CurrencyRateAll(symbol=symbol, price=price, timestamp=timestamp)
    db.add(db_rate_all)
    await db.commit()
    return db_rate_all


async def analyze_currency_rates(db: AsyncSession,
                                 start_time: datetime,
                                 end_time: datetime):
    result = await db.execute(select(CurrencyRate).filter(
        CurrencyRate.timestamp.between(start_time, end_time))
    )
    return result.scalars().all()


async def get_currency_rate_all_count(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(CurrencyRateAll.id)))
    return result.scalar()
