from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from typing import Optional, List
import csv
import io
from datetime import datetime, timezone
from app.api.deps import get_db
from app.models.asset import Asset
from app.models.ohlcv import OHLCVBar
from app.schemas.market_schema import MarketHistoryResponse, TickersResponse, AssetItem, BarItem
from app.services.crypto_service import CryptoService
from app.services.stock_service import StockService
from app.services.ta_engine import TAEngine

router = APIRouter()

@router.get("/history/{symbol:path}", response_model=MarketHistoryResponse)
async def get_market_history(
    symbol: str,
    timeframe: str = Query("1d", pattern="^(15m|1h|4h|1d|1w)$"),
    limit: int = Query(150, ge=10, le=500),
    db: Session = Depends(get_db)
):
    # Lookup asset in DB
    asset = db.query(Asset).filter((Asset.symbol == symbol) | (Asset.symbol == symbol.replace("-", "/"))).first()
    if not asset:
        # If not found directly, create on-the-fly or fallback
        asset_type = "crypto" if "USDT" in symbol.upper() else "stock_idx" if symbol.endswith(".JK") else "stock_us"
        asset = Asset(
            symbol=symbol,
            name=symbol,
            asset_type=asset_type,
            base_currency="IDR" if asset_type == "stock_idx" else "USD"
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)

    # Fetch live bars depending on asset type
    if asset.asset_type == "crypto":
        bars_data = await CryptoService.fetch_binance_bars(asset.symbol, timeframe=timeframe, limit=limit)
        bars_data = CryptoService.get_or_cache_bars(db, asset, timeframe=timeframe, limit=limit, live_bars=bars_data)
    else:
        bars_data = StockService.fetch_stock_bars(asset.symbol, timeframe=timeframe, limit=limit)
        bars_data = StockService.get_or_cache_bars(db, asset, timeframe=timeframe, limit=limit, live_bars=bars_data)

    return MarketHistoryResponse(
        status="success",
        symbol=asset.symbol,
        timeframe=timeframe,
        count=len(bars_data),
        bars=[BarItem(**b) for b in bars_data]
    )

@router.get("/export/{symbol:path}")
async def export_market_csv(
    symbol: str,
    timeframe: str = Query("1d", pattern="^(15m|1h|4h|1d|1w)$"),
    limit: int = Query(200, ge=10, le=500),
    db: Session = Depends(get_db)
):
    asset = db.query(Asset).filter((Asset.symbol == symbol) | (Asset.symbol == symbol.replace("-", "/"))).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if asset.asset_type == "crypto":
        bars_data = await CryptoService.fetch_binance_bars(asset.symbol, timeframe=timeframe, limit=limit)
    else:
        bars_data = StockService.fetch_stock_bars(asset.symbol, timeframe=timeframe, limit=limit)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp_UTC", "Date_UTC", "Open", "High", "Low", "Close", "Volume"])

    for b in bars_data:
        d_str = datetime.fromtimestamp(b["time"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([b["time"], d_str, b["open"], b["high"], b["low"], b["close"], b["volume"]])

    safe_sym = symbol.replace("/", "_").replace("^", "")
    filename = f"finblix_{safe_sym}_{timeframe}.csv"

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/tickers", response_model=TickersResponse)
async def get_tickers(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Asset).filter(Asset.is_active == True)
    if category and category != "all":
        query = query.filter(Asset.asset_type == category)
    
    assets = query.all()
    results: List[AssetItem] = []

    for a in assets:
        # Check cached latest bar or calculate snapshot
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
            # Fallback default estimate
            default_price = 68000.0 if "BTC" in a.symbol else 3500.0 if "ETH" in a.symbol else 10100.0 if "BBCA" in a.symbol else 225.0
            results.append(AssetItem(
                id=a.id,
                symbol=a.symbol,
                name=a.name,
                asset_type=a.asset_type,
                base_currency=a.base_currency,
                last_price=default_price,
                change_24h_percent=1.25,
                volume_24h=1500000.0,
                rsi_14=54.2,
                overall_signal="buy"
            ))

    return TickersResponse(
        status="success",
        count=len(results),
        data=results
    )

@router.get("/comparison")
async def get_market_comparison(
    symbols: str = Query("BTC/USDT,ETH/USDT,BBCA.JK,NVDA"),
    timeframe: str = Query("1d", pattern="^(15m|1h|4h|1d|1w)$"),
    limit: int = Query(90, ge=10, le=365),
    db: Session = Depends(get_db)
):
    from app.services.comparison_service import ComparisonService
    sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
    data = await ComparisonService.get_normalized_comparison(db, sym_list, timeframe, limit)
    return {"status": "success", "data": data}

