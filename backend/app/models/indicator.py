from sqlalchemy import Column, Integer, BigInteger, String, Numeric, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class TechnicalSnapshot(Base):
    __tablename__ = "technical_snapshots"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)
    calculated_at = Column(DateTime, server_default=func.now())
    last_price = Column(Numeric(18, 8), nullable=False)
    change_24h_percent = Column(Numeric(8, 4))
    rsi_14 = Column(Numeric(6, 2))
    rsi_status = Column(String(20), default="neutral")  # oversold, neutral, overbought
    macd_line = Column(Numeric(18, 8))
    macd_signal = Column(Numeric(18, 8))
    macd_hist = Column(Numeric(18, 8))
    ema_20 = Column(Numeric(18, 8))
    ema_50 = Column(Numeric(18, 8))
    ema_200 = Column(Numeric(18, 8))
    bollinger_upper = Column(Numeric(18, 8))
    bollinger_middle = Column(Numeric(18, 8))
    bollinger_lower = Column(Numeric(18, 8))
    overall_signal = Column(String(20), default="neutral")  # strong_buy, buy, neutral, sell, strong_sell

    asset = relationship("Asset", back_populates="technical_snapshots")

    __table_args__ = (
        Index("idx_asset_snapshot", "asset_id", "timeframe"),
    )
