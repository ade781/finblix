from pydantic import BaseModel
from typing import List, Optional

class BarItem(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float

class MarketHistoryResponse(BaseModel):
    status: str = "success"
    symbol: str
    timeframe: str
    count: int
    bars: List[BarItem]

class AssetItem(BaseModel):
    id: int
    symbol: str
    name: str
    asset_type: str
    base_currency: str
    last_price: Optional[float] = 0.0
    change_24h_percent: Optional[float] = 0.0
    volume_24h: Optional[float] = 0.0
    rsi_14: Optional[float] = None
    overall_signal: Optional[str] = "neutral"

class TickersResponse(BaseModel):
    status: str = "success"
    count: int
    data: List[AssetItem]
