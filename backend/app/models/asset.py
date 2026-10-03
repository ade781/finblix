from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    asset_type = Column(String(20), nullable=False, index=True)  # crypto, stock_idx, stock_us, index, forex
    base_currency = Column(String(10), default="USD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    ohlcv_bars = relationship("OHLCVBar", back_populates="asset", cascade="all, delete-orphan")
    technical_snapshots = relationship("TechnicalSnapshot", back_populates="asset", cascade="all, delete-orphan")
    watchlists = relationship("UserWatchlist", back_populates="asset", cascade="all, delete-orphan")
    virtual_trades = relationship("VirtualTrade", back_populates="asset", cascade="all, delete-orphan")
    alerts = relationship("AlertLog", back_populates="asset", cascade="all, delete-orphan")

class UserWatchlist(Base):
    __tablename__ = "user_watchlists"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_name = Column(String(50), default="default_trader")
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    asset = relationship("Asset", back_populates="watchlists")
