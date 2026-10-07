from sqlalchemy import Column, Integer, BigInteger, String, Numeric, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class OHLCVBar(Base):
    __tablename__ = "ohlcv_bars"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)  # 15m, 1h, 4h, 1d, 1w
    open_time = Column(BigInteger, nullable=False)   # Unix epoch seconds (TradingView format)
    open_time_dt = Column(DateTime, nullable=False)
    open_price = Column(Numeric(18, 8), nullable=False)
    high_price = Column(Numeric(18, 8), nullable=False)
    low_price = Column(Numeric(18, 8), nullable=False)
    close_price = Column(Numeric(18, 8), nullable=False)
    volume = Column(Numeric(24, 8), nullable=False)

    asset = relationship("Asset", back_populates="ohlcv_bars")

    __table_args__ = (
        UniqueConstraint("asset_id", "timeframe", "open_time", name="uq_asset_timeframe_bar"),
        Index("idx_fetch_bars", "asset_id", "timeframe", open_time.desc()),
    )
