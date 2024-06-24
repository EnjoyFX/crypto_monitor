# app/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Currency(Base):
    __tablename__ = "currencies"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)


class CurrencyRate(Base):
    __tablename__ = "currency_rates"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String)
    price = Column(Float)
    timestamp = Column(DateTime)


class CurrencyRateAll(Base):
    __tablename__ = "currency_rates_all"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String)
    price = Column(Float)
    timestamp = Column(DateTime)
