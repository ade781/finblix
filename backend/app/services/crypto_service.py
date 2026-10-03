import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.models.ohlcv import OHLCVBar

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
        cache_key = f"{symbol}_{timeframe}"
        now_ts = time.time()
        if cache_key in cls._crypto_cache:
            entry_time, cached_bars = cls._crypto_cache[cache_key]
            if (now_ts - entry_time) < 30 and len(cached_bars) >= min(limit, len(cached_bars)):
                return cached_bars[-limit:]

        binance_symbol = cls.normalize_symbol(symbol)
        interval = BINANCE_TIMEFRAMES.get(timeframe, "1d")
        url = f"https://api.binance.com/api/v3/klines?symbol={binance_symbol}&interval={interval}&limit={limit}"
        
        bars = []
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    for item in data:
                        # item: [open_time, open, high, low, close, volume, close_time, ...]
                        open_sec = int(item[0] // 1000)
                        bars.append({
                            "time": open_sec,
                            "open": float(item[1]),
                            "high": float(item[2]),
                            "low": float(item[3]),
                            "close": float(item[4]),
                            "volume": float(item[5])
                        })
                    if bars:
                        cls._crypto_cache[cache_key] = (now_ts, bars)
                        return bars
        except Exception as e:
            print(f"[CryptoService] Error fetching from Binance API: {e}")

        # Fallback to simulated data if Binance is unreachable
        fallback = cls._generate_fallback_bars(symbol, limit)
        cls._crypto_cache[cache_key] = (now_ts, fallback)
        return fallback

    @classmethod
    def get_or_cache_bars(cls, db: Session, asset: Asset, timeframe: str = "1d", limit: int = 150, live_bars: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        if not live_bars:
            return []

        # Upsert or save new bars into MySQL
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

    @staticmethod
    def _generate_fallback_bars(symbol: str, count: int = 150) -> List[Dict[str, Any]]:
        base_price = 68000.0 if "BTC" in symbol else 3500.0 if "ETH" in symbol else 150.0
        now = int(time.time())
        step = 86400  # 1 day in seconds
        start_time = now - (count * step)
        
        bars = []
        curr = base_price * 0.85
        import random
        for i in range(count):
            t = start_time + (i * step)
            pct = (random.random() - 0.48) * 0.04
            open_p = curr
            close_p = open_p * (1 + pct)
            high_p = max(open_p, close_p) * (1 + random.random() * 0.015)
            low_p = min(open_p, close_p) * (1 - random.random() * 0.015)
            vol = random.uniform(5000, 35000)
            bars.append({
                "time": t,
                "open": round(open_p, 2),
                "high": round(high_p, 2),
                "low": round(low_p, 2),
                "close": round(close_p, 2),
                "volume": round(vol, 2)
            })
            curr = close_p
        return bars
