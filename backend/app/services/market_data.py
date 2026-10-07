"""
Market data access for model training and inference.

Unlike CryptoService/StockService, nothing here falls back to synthetic data:
if a source is unreachable we raise DataUnavailable, so a model can never be
trained or evaluated on random bars.
"""
import os
import time
from typing import Callable, Optional

import httpx
import numpy as np
import pandas as pd

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models_storage", "data_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

BINANCE_SPOT = "https://api.binance.com"
BINANCE_FUTURES = "https://fapi.binance.com"
INTERVAL_MS = {"15m": 900_000, "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000}

KLINE_COLS = ["time", "open", "high", "low", "close", "volume", "quote_volume", "trades", "taker_buy_base"]
OHLCV_COLS = ["time", "open", "high", "low", "close", "volume"]


class DataUnavailable(RuntimeError):
    pass


def _slug(*parts: str) -> str:
    return "_".join(p.replace("/", "").replace(".", "_").replace("^", "_").replace("=", "_").replace("-", "_") for p in parts)


def _cached(key: str, ttl_seconds: int, fetch: Callable[[Optional[pd.DataFrame]], pd.DataFrame], min_bars: int = 0) -> pd.DataFrame:
    """Disk cache. `fetch` receives the cached frame (or None) so it can fetch incrementally."""
    path = os.path.join(CACHE_DIR, f"{key}.pkl")
    cached = None
    if os.path.exists(path):
        try:
            cached = pd.read_pickle(path)
            if (time.time() - os.path.getmtime(path) < ttl_seconds) and (len(cached) >= min_bars):
                return cached
        except Exception:
            cached = None
    try:
        fresh = fetch(cached)
    except Exception as e:
        if cached is not None and len(cached):
            print(f"[market_data] refresh failed for {key}, using stale cache: {e}")
            return cached
        raise DataUnavailable(f"{key}: {e}") from e
    if fresh is None or fresh.empty:
        if cached is not None and len(cached):
            return cached
        raise DataUnavailable(f"{key}: empty response")
    fresh.to_pickle(path)
    return fresh


# ---------------------------------------------------------------- Binance spot
def _binance_symbol(symbol: str) -> str:
    return symbol.replace("/", "").replace("-", "").upper()


def _fetch_klines_range(symbol: str, interval: str, start_ms: int) -> pd.DataFrame:
    rows = []
    step = INTERVAL_MS[interval]
    cursor = start_ms
    with httpx.Client(timeout=15.0) as client:
        while True:
            r = client.get(f"{BINANCE_SPOT}/api/v3/klines", params={
                "symbol": _binance_symbol(symbol), "interval": interval,
                "startTime": cursor, "limit": 1000,
            })
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            rows.extend(batch)
            last_open = batch[-1][0]
            if len(batch) < 1000:
                break
            cursor = last_open + step
    if not rows:
        return pd.DataFrame(columns=KLINE_COLS + ["close_time"])
    df = pd.DataFrame(rows).iloc[:, :11]
    df.columns = ["time", "open", "high", "low", "close", "volume", "close_time",
                  "quote_volume", "trades", "taker_buy_base", "taker_buy_quote"]
    df["time"] = (df["time"] // 1000).astype("int64")
    df["close_time"] = (df["close_time"] // 1000).astype("int64")
    for c in ["open", "high", "low", "close", "volume", "quote_volume", "taker_buy_base"]:
        df[c] = df[c].astype(float)
    df["trades"] = df["trades"].astype(float)
    return df[KLINE_COLS + ["close_time"]]


def binance_klines(symbol: str, interval: str, lookback_bars: int, ttl_seconds: int = 300,
                   closed_only: bool = True) -> pd.DataFrame:
    """Paginated Binance klines with taker-buy volume. Incrementally cached on disk."""
    step_ms = INTERVAL_MS[interval]
    key = _slug("binance", symbol, interval)

    def fetch(cached: Optional[pd.DataFrame]) -> pd.DataFrame:
        now_ms = int(time.time() * 1000)
        want_start = now_ms - lookback_bars * step_ms
        if cached is not None and len(cached) and int(cached["time"].iloc[0]) * 1000 <= want_start + step_ms:
            start = int(cached["time"].iloc[-1]) * 1000 - 2 * step_ms
            new = _fetch_klines_range(symbol, interval, start)
            out = pd.concat([cached, new]).drop_duplicates("time", keep="last")
        else:
            out = _fetch_klines_range(symbol, interval, max(0, want_start))
        return out.sort_values("time").reset_index(drop=True)

    df = _cached(key, ttl_seconds, fetch, min_bars=lookback_bars)
    if closed_only:
        df = df[df["close_time"] < time.time()]
    df = df.tail(lookback_bars).reset_index(drop=True)
    if len(df) == 0:
        raise DataUnavailable(f"no klines for {symbol} {interval}")
    return df


def binance_funding(symbol: str, lookback_days: int, ttl_seconds: int = 1800) -> pd.DataFrame:
    """Perpetual futures funding rate history (8h events). Columns: time, funding_rate."""
    key = _slug("funding", symbol)

    def fetch(cached: Optional[pd.DataFrame]) -> pd.DataFrame:
        now_ms = int(time.time() * 1000)
        start = now_ms - lookback_days * 86_400_000
        if cached is not None and len(cached) and int(cached["time"].iloc[0]) * 1000 <= start + 86_400_000:
            start = int(cached["time"].iloc[-1]) * 1000 + 1
        rows = []
        with httpx.Client(timeout=15.0) as client:
            while True:
                r = client.get(f"{BINANCE_FUTURES}/fapi/v1/fundingRate", params={
                    "symbol": _binance_symbol(symbol), "startTime": start, "limit": 1000,
                })
                r.raise_for_status()
                batch = r.json()
                if not batch:
                    break
                rows.extend(batch)
                if len(batch) < 1000:
                    break
                start = int(batch[-1]["fundingTime"]) + 1
        new = pd.DataFrame({
            "time": [int(x["fundingTime"]) // 1000 for x in rows],
            "funding_rate": [float(x["fundingRate"]) for x in rows],
        })
        out = new if cached is None else pd.concat([cached, new])
        return out.drop_duplicates("time").sort_values("time").reset_index(drop=True)

    return _cached(key, ttl_seconds, fetch)


# ---------------------------------------------------------------- yfinance
def yf_history(symbol: str, period: str, interval: str, ttl_seconds: int = 900) -> pd.DataFrame:
    """yfinance OHLCV. Adds `date` (exchange-local calendar date, YYYY-MM-DD)."""
    key = _slug("yf", symbol, period, interval)

    def fetch(_cached: Optional[pd.DataFrame]) -> pd.DataFrame:
        import yfinance as yf
        raw = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=True)
        if raw is None or raw.empty:
            return pd.DataFrame()
        idx = raw.index
        df = pd.DataFrame({
            "time": [int(d.timestamp()) for d in idx],
            "date": [d.strftime("%Y-%m-%d") for d in idx],
            "open": raw["Open"].astype(float).values,
            "high": raw["High"].astype(float).values,
            "low": raw["Low"].astype(float).values,
            "close": raw["Close"].astype(float).values,
            "volume": raw["Volume"].astype(float).values,
        })
        df = df[(df["high"] > 0) & (df["low"] > 0) & (df["close"] > 0)]
        return df.drop_duplicates("time").sort_values("time").reset_index(drop=True)

    return _cached(key, ttl_seconds, fetch)


def is_crypto(symbol: str) -> bool:
    return "/" in symbol or symbol.upper().endswith("USDT")


def frame_to_bars(df: pd.DataFrame) -> list:
    cols = [c for c in KLINE_COLS + ["date"] if c in df.columns]
    return df[cols].to_dict("records")


def safe(fn: Callable[[], pd.DataFrame]) -> Optional[pd.DataFrame]:
    """Optional exogenous series: return None instead of failing the whole model."""
    try:
        return fn()
    except Exception as e:
        print(f"[market_data] optional series unavailable: {e}")
        return None


def log_ret(s: pd.Series, n: int) -> pd.Series:
    return np.log(s / s.shift(n))
