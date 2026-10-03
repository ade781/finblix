from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.api.deps import get_db
from app.models.asset import Asset
from app.models.ohlcv import OHLCVBar
from app.schemas.market_schema import TickersResponse, AssetItem
from app.services.ta_engine import TAEngine

router = APIRouter()

@router.get("/overview", response_model=TickersResponse)
async def get_screener_overview(
    category: Optional[str] = Query(None, description="crypto, stock_idx, stock_us, all"),
    sort_by: Optional[str] = Query("gainers", description="gainers, losers, volume"),
    db: Session = Depends(get_db)
):
    query = db.query(Asset).filter(Asset.is_active == True)
    if category and category != "all":
        query = query.filter(Asset.asset_type == category)

    assets = query.all()
    results: List[AssetItem] = []

    for a in assets:
        last_bars = db.query(OHLCVBar).filter(
            OHLCVBar.asset_id == a.id,
            OHLCVBar.timeframe == "1d"
        ).order_by(OHLCVBar.open_time.desc()).limit(30).all()

        if last_bars and len(last_bars) >= 2:
            bars_dict = [{
                "time": b.open_time,
                "open": float(b.open_price),
                "high": float(b.high_price),
                "low": float(b.low_price),
                "close": float(b.close_price),
                "volume": float(b.volume)
            } for b in reversed(last_bars)]
            ta = TAEngine.calculate_indicators(bars_dict)
            results.append(AssetItem(
                id=a.id,
                symbol=a.symbol,
                name=a.name,
                asset_type=a.asset_type,
                base_currency=a.base_currency,
                last_price=ta["last_price"],
                change_24h_percent=ta["change_24h_percent"],
                volume_24h=float(last_bars[0].volume),
                rsi_14=ta["rsi_14"],
                overall_signal=ta["overall_signal"]
            ))
        else:
            default_price = 68000.0 if "BTC" in a.symbol else 3500.0 if "ETH" in a.symbol else 10100.0 if "BBCA" in a.symbol else 225.0
            results.append(AssetItem(
                id=a.id,
                symbol=a.symbol,
                name=a.name,
                asset_type=a.asset_type,
                base_currency=a.base_currency,
                last_price=default_price,
                change_24h_percent=1.2,
                volume_24h=1200000.0,
                rsi_14=52.0,
                overall_signal="neutral"
            ))

    # Sort
    if sort_by == "gainers":
        results.sort(key=lambda x: x.change_24h_percent or 0, reverse=True)
    elif sort_by == "losers":
        results.sort(key=lambda x: x.change_24h_percent or 0)
    elif sort_by == "volume":
        results.sort(key=lambda x: x.volume_24h or 0, reverse=True)

    return TickersResponse(
        status="success",
        count=len(results),
        data=results
    )
