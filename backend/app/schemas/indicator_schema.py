from pydantic import BaseModel
from typing import Optional, Dict, Any

class MACDData(BaseModel):
    macd_line: Optional[float] = None
    signal_line: Optional[float] = None
    histogram: Optional[float] = None

class EMAData(BaseModel):
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None

class BollingerBandsData(BaseModel):
    upper: Optional[float] = None
    middle: Optional[float] = None
    lower: Optional[float] = None

class IndicatorResponse(BaseModel):
    symbol: str
    timeframe: str
    last_price: float
    change_24h_percent: Optional[float] = 0.0
    rsi_14: Optional[float] = None
    rsi_status: str = "neutral"
    macd: MACDData
    ema: EMAData
    bollinger: BollingerBandsData
    overall_signal: str = "neutral"  # strong_buy, buy, neutral, sell, strong_sell
    calculated_at: str
