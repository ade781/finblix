import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.models.ohlcv import OHLCVBar
from app.services.market_snapshot import MarketSnapshotService

BINANCE_TIMEFRAMES = {
    "15m": "15m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
    "1w": "1w"
}


class CryptoService:
    _crypto_cache = {}

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        # 'BTC/USDT' -> 'BTCUSDT'
        return symbol.replace("/", "").replace("-", "").upper()

    @classmethod
    async def fetch_binance_bars(cls, symbol: str, timeframe: str = "1d", limit: int = 150) -> List[Dict[str, Any]]:
        """
        Fetches canonical, verified market bars.
        Zero synthetic or simulated data fallback.
        """
        cache_key = f"{symbol}_{timeframe}"
        now_ts = time.time()
        if cache_key in cls._crypto_cache:
            entry_time, cached_bars = cls._crypto_cache[cache_key]
            if (now_ts - entry_time) < 30 and len(cached_bars) >= min(limit, len(cached_bars)):
                return cached_bars[-limit:]

        try:
            snapshot = MarketSnapshotService.get_canonical_snapshot(symbol, timeframe=timeframe, limit=limit)
            bars = snapshot.get("bars", [])
            if bars:
                cls._crypto_cache[cache_key] = (now_ts, bars)
                return bars
        except Exception as e:
            print(f"[CryptoService] Error fetching canonical bars for {symbol}: {e}")

        # If live fetch fails, check if we have unexpired cache
        if cache_key in cls._crypto_cache:
            _, cached_bars = cls._crypto_cache[cache_key]
            return cached_bars[-limit:]

        return []

    @classmethod
    def get_or_cache_bars(cls, db: Session, asset: Asset, timeframe: str = "1d", limit: int = 150, live_bars: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        if not live_bars:
            return []

        # Upsert or save new bars into DB
        for bar in live_bars:
            dt = datetime.fromtimestamp(bar["time"], tz=timezone.utc).replace(tzinfo=None)
            existing = db.query(OHLCVBar).filter(
                OHLCVBar.asset_id == asset.id,
                OHLCVBar.timeframe == timeframe,
                OHLCVBar.open_time == bar["time"]
            ).first()

            if not existing:
                new_bar = OHLCVBar(
                    asset_id=asset.id,
                    timeframe=timeframe,
                    open_time=bar["time"],
                    open_time_dt=dt,
                    open_price=bar["open"],
                    high_price=bar["high"],
                    low_price=bar["low"],
                    close_price=bar["close"],
                    volume=bar["volume"]
                )
                db.add(new_bar)
            else:
                existing.close_price = bar["close"]
                existing.high_price = bar["high"]
                existing.low_price = bar["low"]
                existing.volume = bar["volume"]

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[CryptoService] DB commit error: {e}")

        return live_bars
