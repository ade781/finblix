from sqlalchemy import Column, Integer, BigInteger, String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class VirtualPortfolio(Base):
    __tablename__ = "virtual_portfolios"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_name = Column(String(50), default="default_trader")
    portfolio_name = Column(String(100), default="Main Simulation")
    initial_balance = Column(Numeric(18, 2), default=10000.00)
    cash_balance = Column(Numeric(18, 2), default=10000.00)
    currency = Column(String(10), default="USD")
    created_at = Column(DateTime, server_default=func.now())

    trades = relationship("VirtualTrade", back_populates="portfolio", cascade="all, delete-orphan")

class VirtualTrade(Base):
    __tablename__ = "virtual_trades"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("virtual_portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    trade_type = Column(String(10), nullable=False)   # buy, sell
    amount = Column(Numeric(18, 8), nullable=False)
    entry_price = Column(Numeric(18, 8), nullable=False)
    total_cost = Column(Numeric(18, 2), nullable=False)
    status = Column(String(10), default="open")       # open, closed
    closed_price = Column(Numeric(18, 8), nullable=True)
    pnl_amount = Column(Numeric(18, 2), nullable=True)
    pnl_percent = Column(Numeric(8, 4), nullable=True)
    executed_at = Column(DateTime, server_default=func.now())

    portfolio = relationship("VirtualPortfolio", back_populates="trades")
    asset = relationship("Asset", back_populates="virtual_trades")
