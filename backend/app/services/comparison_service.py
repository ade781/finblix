from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.services.crypto_service import CryptoService
from app.services.stock_service import StockService

class ComparisonService:
    @classmethod
    async def get_normalized_comparison(cls, db: Session, symbols: List[str], timeframe: str = "1d", limit: int = 90) -> Dict[str, Any]:
        series_map = {}
        all_timestamps = set()

        for sym in symbols:
            clean_sym = sym.strip()
            asset = db.query(Asset).filter((Asset.symbol == clean_sym) | (Asset.symbol == clean_sym.replace("-", "/"))).first()
            if asset and asset.asset_type == "crypto":
                bars = await CryptoService.fetch_binance_bars(asset.symbol, timeframe=timeframe, limit=limit)
            elif asset:
                bars = StockService.fetch_stock_bars(asset.symbol, timeframe=timeframe, limit=limit)
            else:
                bars = await CryptoService.fetch_binance_bars(clean_sym, timeframe=timeframe, limit=limit)

            if bars:
                base_price = bars[0]["close"]
                norm_points = []
                for b in bars:
                    t = b["time"]
                    all_timestamps.add(t)
                    pct_change = ((b["close"] - base_price) / base_price) * 100.0 if base_price > 0 else 0.0
                    norm_points.append({
                        "time": t,
                        "date": datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d"),
                        "raw_price": b["close"],
                        "pct_return": round(pct_change, 2)
                    })
                series_map[clean_sym] = norm_points

        sorted_times = sorted(list(all_timestamps))

        return {
            "timeframe": timeframe,
            "symbols": symbols,
            "series": series_map,
            "timeline": sorted_times
        }
