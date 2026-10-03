from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import asyncio
from app.api.deps import get_db
from app.models.asset import Asset
from app.models.indicator import TechnicalSnapshot
from app.schemas.indicator_schema import IndicatorResponse, MACDData, EMAData, BollingerBandsData
from app.services.crypto_service import CryptoService
from app.services.stock_service import StockService
from app.services.ta_engine import TAEngine

router = APIRouter()

@router.get("/{symbol:path}", response_model=IndicatorResponse)
async def get_indicators(
    symbol: str,
    timeframe: str = Query("1d", pattern="^(15m|1h|4h|1d|1w)$"),
    db: Session = Depends(get_db)
):
    asset = db.query(Asset).filter((Asset.symbol == symbol) | (Asset.symbol == symbol.replace("-", "/"))).first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")

    # Fetch bars
    if asset.asset_type == "crypto":
        bars = await CryptoService.fetch_binance_bars(asset.symbol, timeframe=timeframe, limit=200)
    else:
        bars = await asyncio.to_thread(StockService.fetch_stock_bars, asset.symbol, timeframe=timeframe, limit=200)

    ta = TAEngine.calculate_indicators(bars)

    # Save to TechnicalSnapshot
    snapshot = TechnicalSnapshot(
        asset_id=asset.id,
        timeframe=timeframe,
        last_price=ta["last_price"],
        change_24h_percent=ta["change_24h_percent"],
        rsi_14=ta["rsi_14"],
        rsi_status=ta["rsi_status"],
        macd_line=ta["macd_line"],
        macd_signal=ta["macd_signal"],
        macd_hist=ta["macd_hist"],
        ema_20=ta["ema_20"],
        ema_50=ta["ema_50"],
        ema_200=ta["ema_200"],
        bollinger_upper=ta["bollinger_upper"],
        bollinger_middle=ta["bollinger_middle"],
        bollinger_lower=ta["bollinger_lower"],
        overall_signal=ta["overall_signal"]
    )
    db.add(snapshot)
    try:
        db.commit()
    except Exception:
        db.rollback()

    return IndicatorResponse(
        symbol=asset.symbol,
        timeframe=timeframe,
        last_price=ta["last_price"],
        change_24h_percent=ta["change_24h_percent"],
        rsi_14=ta["rsi_14"],
        rsi_status=ta["rsi_status"],
        macd=MACDData(
            macd_line=ta["macd_line"],
            signal_line=ta["macd_signal"],
            histogram=ta["macd_hist"]
        ),
        ema=EMAData(
            ema_20=ta["ema_20"],
            ema_50=ta["ema_50"],
            ema_200=ta["ema_200"]
        ),
        bollinger=BollingerBandsData(
            upper=ta["bollinger_upper"],
            middle=ta["bollinger_middle"],
            lower=ta["bollinger_lower"]
        ),
        overall_signal=ta["overall_signal"],
        calculated_at=datetime.now(timezone.utc).isoformat()
    )
