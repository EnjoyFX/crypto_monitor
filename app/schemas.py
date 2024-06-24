# app/schemas.py
from pydantic import BaseModel
from datetime import datetime


class CurrencyCreate(BaseModel):
    symbol: str

    class Config:
        orm_mode = True


class CurrencyRateCreate(BaseModel):
    symbol: str
    price: float
    timestamp: datetime

    class Config:
        orm_mode = True
