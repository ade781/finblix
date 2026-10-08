"""
Canonical Market Snapshot Service for Finblix.

Provides a unified, verified market data snapshot mechanism across Daily,
Intraday, and API consumers. Ensures:
1. No synthetic/random-walk data is ever injected into production.
2. Consistent BTC and asset prices across all horizons.
3. Explicit timestamp audit trails, data freshness verification, and staleness warnings.
4. Consistent symbol normalization.
"""
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.models.ohlcv import OHLCVBar
from app.services.market_data import (
    binance_klines,
    yf_history,
    is_crypto,
    DataUnavailable,
    BINANCE_SPOT_ENDPOINTS,
)
import httpx


class MarketSnapshotService:
    SNAPSHOT_VERSION = "2.0.0_canonical"

    # Staleness tolerance thresholds (in seconds)
    STALE_THRESHOLDS = {
        "15m": 3600,       # 1 hour
        "1h": 7200,        # 2 hours
        "4h": 28800,       # 8 hours
        "1d": 86400 * 2,   # 48 hours
        "1w": 86400 * 14,  # 14 days
    }

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """Converts any symbol variant to canonical display format (e.g. BTC/USDT or AAPL)."""
        clean = symbol.strip().upper()
        if "/" in clean:
            return clean
        if clean.endswith("USDT"):
            base = clean[:-4]
            return f"{base}/USDT"
        return clean

    @staticmethod
    def get_binance_ticker_price(symbol: str) -> Optional[float]:
        """Fetch real-time latest spot price from Binance."""
        clean = symbol.replace("/", "").replace("-", "").upper()
        for endpoint in BINANCE_SPOT_ENDPOINTS:
            try:
                with httpx.Client(timeout=4.0) as client:
                    r = client.get(f"{endpoint}/api/v3/ticker/price", params={"symbol": clean})
                    if r.status_code == 200:
                        return float(r.json()["price"])
            except Exception:
                continue
        return None

    @classmethod
    def get_canonical_snapshot(
        cls,
        symbol: str,
        timeframe: str = "1d",
        limit: int = 150,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Produce a canonical market snapshot.
        Guarantees:
        - symbol, timeframe, data_source
        - latest_candle_time, latest_candle_dt
        - latest_price
        - fetched_at, fetched_at_dt
        - data_freshness_seconds
        - is_stale, status, model_version
        - bars (list of real OHLCV dicts)
        """
        canonical_sym = cls.normalize_symbol(symbol)
        fetched_at = int(time.time())
        fetched_at_dt = datetime.fromtimestamp(fetched_at, tz=timezone.utc).isoformat()
        crypto = is_crypto(canonical_sym)
        data_source = "binance_spot" if crypto else "yfinance"

        bars_data: List[Dict[str, Any]] = []
        err_msg: Optional[str] = None

        if crypto:
            try:
                # Fetch real Binance klines without synthetic fallbacks
                df = binance_klines(
                    canonical_sym,
                    interval=timeframe,
                    lookback_bars=limit,
                    ttl_seconds=60 if timeframe == "15m" else 300,
                    closed_only=False
                )
                if df is not None and not df.empty:
                    bars_data = df[["time", "open", "high", "low", "close", "volume"]].to_dict("records")
            except Exception as e:
                err_msg = str(e)
        else:
            try:
                df = yf_history(canonical_sym, period="2y", interval=timeframe, ttl_seconds=600)
                if df is not None and not df.empty:
                    df = df.tail(limit).reset_index(drop=True)
                    bars_data = df[["time", "open", "high", "low", "close", "volume"]].to_dict("records")
            except Exception as e:
                err_msg = str(e)

        # If live fetch failed, check if we have legitimate bars in the DB (must have valid prices)
        if not bars_data and db is not None:
            asset = db.query(Asset).filter(
                (Asset.symbol == canonical_sym) | (Asset.symbol == symbol)
            ).first()
            if asset:
                db_bars = db.query(OHLCVBar).filter(
                    OHLCVBar.asset_id == asset.id,
                    OHLCVBar.timeframe == timeframe
                ).order_by(OHLCVBar.open_time.desc()).limit(limit).all()
                if db_bars:
                    # Reverse so ascending
                    db_bars = sorted(db_bars, key=lambda b: b.open_time)
                    # Exclude known synthetic values (e.g. BTC < 70000 in late 2024-2026)
                    filtered = [
                        {
                            "time": b.open_time,
                            "open": float(b.open_price),
                            "high": float(b.high_price),
                            "low": float(b.low_price),
                            "close": float(b.close_price),
                            "volume": float(b.volume or 0)
                        }
                        for b in db_bars
                        if not (crypto and "BTC" in canonical_sym and float(b.close_price) < 70000)
                    ]
                    if len(filtered) >= 10:
                        bars_data = filtered

        if not bars_data:
            raise DataUnavailable(
                f"Market data unavailable for {canonical_sym} ({timeframe}): {err_msg or 'No verified bars'}"
            )

        latest_bar = bars_data[-1]
        latest_candle_time = int(latest_bar["time"])
        latest_candle_dt = datetime.fromtimestamp(latest_candle_time, tz=timezone.utc).isoformat()
        latest_close = float(latest_bar["close"])

        # For crypto, attempt to get real-time tick price if available
        realtime_price = None
        if crypto:
            realtime_price = cls.get_binance_ticker_price(canonical_sym)
        latest_price = realtime_price if realtime_price is not None else latest_close

        freshness_seconds = max(0, fetched_at - latest_candle_time)
        threshold = cls.STALE_THRESHOLDS.get(timeframe, 86400 * 2)
        is_stale = freshness_seconds > threshold

        status = "OK"
        warning = None
        if is_stale:
            status = "WARNING_STALE"
            warning = f"Data is {freshness_seconds // 3600}h old (exceeds threshold of {threshold // 3600}h)."

        # Save verified bars to DB if session provided
        if db is not None:
            cls._sync_verified_bars_to_db(db, canonical_sym, timeframe, bars_data)

        return {
            "symbol": canonical_sym,
            "timeframe": timeframe,
            "data_source": data_source,
            "latest_candle_timestamp": latest_candle_time,
            "latest_candle_dt": latest_candle_dt,
            "latest_price": round(latest_price, 2),
            "close_price": round(latest_close, 2),
            "fetched_at": fetched_at,
            "fetched_at_dt": fetched_at_dt,
            "data_freshness_seconds": freshness_seconds,
            "is_stale": is_stale,
            "status": status,
            "warning": warning,
            "bar_count": len(bars_data),
            "bars": bars_data,
            "model_version": cls.SNAPSHOT_VERSION,
        }

    @classmethod
    def _sync_verified_bars_to_db(
        cls,
        db: Session,
        symbol: str,
        timeframe: str,
        bars: List[Dict[str, Any]]
    ) -> None:
        try:
            asset = db.query(Asset).filter(Asset.symbol == symbol).first()
            if not asset:
                return

            for bar in bars[-30:]:  # Keep recent synced
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
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[MarketSnapshotService] Error syncing bars to DB: {e}")

    @classmethod
    def verify_price_consistency(
        cls,
        daily_price: float,
        intraday_price: float,
        tolerance_pct: float = 0.08
    ) -> Tuple[bool, str]:
        """
        Verifies that daily and intraday prices do not exhibit an irreconcilable conflict.
        Returns (is_consistent, message).
        """
        if daily_price <= 0 or intraday_price <= 0:
            return False, "Non-positive price encountered"
        diff_pct = abs(daily_price - intraday_price) / max(daily_price, intraday_price)
        if diff_pct > tolerance_pct:
            return False, (
                f"Significant price divergence between horizons: "
                f"Daily=${daily_price:,.2f} vs Intraday=${intraday_price:,.2f} ({diff_pct*100:.1f}% delta)."
            )
        return True, f"Prices are consistent ({diff_pct*100:.2f}% intraday range delta)."
