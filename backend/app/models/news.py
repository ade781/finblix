from sqlalchemy import Column, Integer, BigInteger, String, Numeric, Text, Boolean, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    source = Column(String(100), nullable=False)
    article_url = Column(String(500), unique=True, nullable=False)
    published_at = Column(DateTime, nullable=False)
    summary = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    sentiment_score = Column(Numeric(5, 4), nullable=False)  # -1.0000 to +1.0000
    sentiment_label = Column(String(20), nullable=False)    # bearish, neutral, bullish
    related_symbols = Column(String(100), nullable=True)
    scraped_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_published", published_at.desc()),
        Index("idx_sentiment", "sentiment_label"),
    )

class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String(30), nullable=False)  # volume_spike, rsi_oversold, rsi_overbought, ma_cross, price_breakout
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="info")     # info, warning, critical
    triggered_at = Column(DateTime, server_default=func.now())
    is_read = Column(Boolean, default=False)

    asset = relationship("Asset", back_populates="alerts")

    __table_args__ = (
        Index("idx_unread_alerts", "is_read", triggered_at.desc()),
    )
