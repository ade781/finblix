import os
import sys
import time
import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import joblib

from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.models.ohlcv import OHLCVBar
from app.services.market_data import binance_klines, yf_history, is_crypto, is_idx, frame_to_bars, DataUnavailable
from app.services.quant_ml import fit_direction_model, conviction_tier
from app.services.scraper_service import ScraperService

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models_storage")
os.makedirs(MODELS_DIR, exist_ok=True)


class MLTrainingEngine:
    @staticmethod
    def _slugify(symbol: str) -> str:
        return symbol.replace("/", "_").replace(".", "_").replace("-", "_")

    _fng_cache = {}
    _loaded_models = {}

    @classmethod
    def load_historical_fng_series(cls) -> Dict[str, float]:
        if cls._fng_cache:
            return cls._fng_cache
        local_fng_all = os.path.join(MODELS_DIR, "fng_all.json")
        if os.path.exists(local_fng_all):
            try:
                with open(local_fng_all, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    if isinstance(raw_data, list):
                        fng_map = {}
                        for item in raw_data:
                            ts = int(item["timestamp"])
                            dt_str = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")
                            fng_map[dt_str] = float(item["value"])
                        cls._fng_cache = fng_map
                        return cls._fng_cache
                    elif isinstance(raw_data, dict):
                        cls._fng_cache = raw_data
                        return cls._fng_cache
            except Exception as e:
                print(f"[MLTrainingEngine] Error loading fng_all.json: {e}")
        return {}

    @classmethod
    def _compute_features_core(cls, df: pd.DataFrame, fng_map: Dict[str, float], news_map: Optional[Dict[str, float]]) -> pd.DataFrame:
        df = df.copy()
        
        # Handle time
        if "date_obj" not in df.columns:
            df["date_obj"] = pd.to_datetime(df["time"], unit="s", utc=True)
            df["date_str"] = df["date_obj"].dt.strftime("%Y-%m-%d")

        close = df["close"]
        high = df["high"]
        low = df["low"]
        open_p = df["open"]
        vol = df["volume"].replace(0, 1)

        c_range = (high - low).replace(0, 1e-9)
        df["upper_wick"] = (high - np.maximum(close, open_p)) / c_range
        df["lower_wick"] = (np.minimum(close, open_p) - low) / c_range
        df["body_ratio"] = (close - open_p).abs() / c_range

        df["ret_1d"] = close.pct_change(1)
        df["ret_3d"] = close.pct_change(3)
        df["ret_7d"] = close.pct_change(7)
        df["ret_14d"] = close.pct_change(14)
        df["ret_30d"] = close.pct_change(30)

        ema9 = close.ewm(span=9, adjust=False).mean()
        ema20 = close.ewm(span=20, adjust=False).mean()
        ema50 = close.ewm(span=50, adjust=False).mean()
        ema100 = close.ewm(span=100, adjust=False).mean()

        df["price_to_ema20"] = (close / ema20) - 1.0
        df["price_to_ema50"] = (close / ema50) - 1.0
        df["ema20_to_ema50"] = (ema20 / ema50) - 1.0
        df["price_to_weekly_ema"] = (close / ema100) - 1.0
        df["ema9_slope"] = ema9.diff() / (close + 1e-9)

        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        df["rsi_14"] = 100 - (100 / (1 + rs))
        df["rsi_delta"] = df["rsi_14"].diff(3)

        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        macd_signal = macd_line.ewm(span=9, adjust=False).mean()
        macd_raw_hist = macd_line - macd_signal
        df["macd_hist"] = macd_raw_hist / (close + 1e-9)
        df["macd_accel"] = df["macd_hist"].diff()

        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        upper = sma20 + (std20 * 2)
        lower = sma20 - (std20 * 2)
        df["bb_percent_b"] = (close - lower) / ((upper - lower) + 1e-9)
        df["bb_width"] = (upper - lower) / (sma20 + 1e-9)

        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr14 = tr.rolling(14).mean()
        df["atr_norm"] = atr14 / (close + 1e-9)

        vol_sma20 = vol.rolling(20).mean()
        df["volume_ratio"] = vol / (vol_sma20 + 1e-9)

        atr_sum14 = tr.rolling(14).sum()
        max_h14 = high.rolling(14).max()
        min_l14 = low.rolling(14).min()
        chop = 100 * np.log10(atr_sum14 / ((max_h14 - min_l14) + 1e-9)) / np.log10(14)
        df["choppiness_index"] = chop / 100.0

        mfm = ((close - low) - (high - close)) / c_range
        mfv = mfm * vol
        df["cmf_20"] = mfv.rolling(20).sum() / (vol.rolling(20).sum() + 1e-9)

        dir_sign = np.sign(close.diff()).fillna(0)
        obv = (dir_sign * vol).cumsum()
        df["obv_slope"] = obv.diff(5) / (vol_sma20 * 5 + 1e-9)

        up_move = high.diff()
        down_move = -low.diff()
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
        plus_di = 100 * pd.Series(plus_dm, index=df.index).rolling(14).mean() / (atr14 + 1e-9)
        minus_di = 100 * pd.Series(minus_dm, index=df.index).rolling(14).mean() / (atr14 + 1e-9)
        dx = 100 * (plus_di - minus_di).abs() / ((plus_di + minus_di) + 1e-9)
        df["adx_14"] = dx.rolling(14).mean() / 100.0

        df["fng_val"] = df["date_str"].map(fng_map).fillna(50.0) / 100.0
        df["fng_delta"] = df["fng_val"].diff(7).fillna(0.0)

        if news_map:
            raw_news = df["date_str"].map(news_map)
        else:
            raw_news = pd.Series(np.nan, index=df.index)

        base_fng_sent = (df["fng_val"] - 0.5) * 2.0
        df["news_sentiment"] = raw_news.fillna(base_fng_sent)
        df["news_sentiment_7d"] = df["news_sentiment"].ewm(span=7, adjust=False).mean()

        day_of_week = df["date_obj"].dt.weekday
        df["day_of_week"] = day_of_week / 6.0

        return df

    @classmethod
    def build_ml_features(
        cls, 
        df: pd.DataFrame, 
        fng_map: Dict[str, float], 
        news_map: Optional[Dict[str, float]] = None,
    ) -> Tuple[pd.DataFrame, List[str], pd.Series, pd.Series]:
        """
        Builds features and targets for the quant_ml engine pipeline.
        """
        df = cls._compute_features_core(df, fng_map, news_map)
        
        feature_cols_all = [
            "upper_wick", "lower_wick", "body_ratio",
            "ret_1d", "ret_3d", "ret_7d", "ret_14d", "ret_30d",
            "price_to_ema20", "price_to_ema50", "ema20_to_ema50",
            "price_to_weekly_ema", "ema9_slope",
            "rsi_14", "rsi_delta", "macd_hist", "macd_accel",
            "bb_percent_b", "bb_width", "atr_norm", "volume_ratio",
            "choppiness_index", "cmf_20", "obv_slope", "adx_14",
            "fng_val", "fng_delta", "news_sentiment", "news_sentiment_7d",
            "day_of_week"
        ]

        fwd_ret = (df["close"].shift(-1) / df["close"]) - 1.0
        scale = df["atr_norm"]

        return df, feature_cols_all, fwd_ret, scale

    @classmethod
    def build_feature_dataset(
        cls, 
        bars: List[Dict[str, Any]], 
        fng_map: Dict[str, float], 
        news_map: Optional[Dict[str, float]] = None,
        is_training: bool = True
    ) -> pd.DataFrame:
        """
        Backward-compatible feature builder for legacy callers like PredictionEngine.
        """
        df = pd.DataFrame(bars)
        df = cls._compute_features_core(df, fng_map, news_map)
        
        feature_cols_all = [
            "upper_wick", "lower_wick", "body_ratio",
            "ret_1d", "ret_3d", "ret_7d", "ret_14d", "ret_30d",
            "price_to_ema20", "price_to_ema50", "ema20_to_ema50",
            "price_to_weekly_ema", "ema9_slope",
            "rsi_14", "rsi_delta", "macd_hist", "macd_accel",
            "bb_percent_b", "bb_width", "atr_norm", "volume_ratio",
            "choppiness_index", "cmf_20", "obv_slope", "adx_14",
            "fng_val", "fng_delta", "news_sentiment", "news_sentiment_7d",
            "day_of_week"
        ]
        
        if is_training:
            df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)
            clean_df = df.dropna(subset=feature_cols_all + ["target"]).iloc[:-1].reset_index(drop=True)
        else:
            clean_df = df.dropna(subset=feature_cols_all).reset_index(drop=True)

        return clean_df

    @classmethod
    async def train_model_for_asset(
        cls, 
        db: Session, 
        symbol: str, 
        n_estimators_rf: int = 500, 
        n_estimators_gb: int = 400,
        n_estimators_et: int = 300,
        bars_limit: int = 1500
    ) -> Dict[str, Any]:
        """
        Refactored: Uses MarketDataService and quant_ml.py leakage-safe pipeline.
        The old hyperparams are kept in the signature for backward compatibility but ignored,
        since candidate_models in quant_ml handles the ensemble design.
        """
        start_time = time.time()
        slug = cls._slugify(symbol)
        
        # 1. Disk-cached robust data ingestion
        if is_crypto(symbol):
            df = binance_klines(symbol, interval="1d", lookback_bars=bars_limit)
        else:
            df = yf_history(symbol, period="5y", interval="1d")
            df = df.tail(bars_limit).reset_index(drop=True)
            
        if len(df) < 100:
            raise ValueError(f"Data historis tidak mencukupi untuk training (hanya {len(df)} bar)")

        # 2. Sentimen dll
        fng_map = cls.load_historical_fng_series()
        news_sentiment_map = ScraperService.get_date_sentiment_map(db, symbol)

        # 3. Fitur
        feat_df, feature_cols, fwd_ret, scale = cls.build_ml_features(df, fng_map, news_sentiment_map)
        
        # 4. Training (quant_ml)
        fit_result = fit_direction_model(
            feat=feat_df,
            candidate_cols=feature_cols,
            fwd_ret=fwd_ret,
            scale=scale,
            horizon=1,
            k_deadband=0.25, # Deadband scaling
            test_frac=0.2,
            n_splits=5,
            max_features=15,
            times=feat_df["time"],
            random_state=42
        )
        
        metrics = fit_result["metrics"]
        duration = round(time.time() - start_time, 2)
        
        # 5. Save model
        model_payload = {
            "model": fit_result["model"],
            "features": fit_result["features"],
            "symbol": symbol,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
            "hc_threshold": fit_result["hc_threshold"]
        }
        model_path = os.path.join(MODELS_DIR, f"{slug}_model.joblib")
        joblib.dump(model_payload, model_path)

        # Build meta to align with previous API
        meta_data = {
            "symbol": symbol,
            "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "dataset_bars": len(df),
            "samples_trained": metrics.get("samples_trained"),
            "samples_tested": metrics.get("samples_tested"),
            "training_duration_seconds": duration,
            "metrics": {
                "train_accuracy_pct": metrics.get("train_accuracy_pct"),
                "cv_5fold_mean_pct": metrics.get("cv_accuracy_pct"),
                "test_accuracy_pct": metrics.get("test_accuracy_pct"),
                "roc_auc_pct": metrics.get("test_auc_pct"),
                "hc_test_accuracy_pct": metrics.get("hc_test_accuracy_pct"),
                "hc_test_coverage_pct": metrics.get("hc_test_coverage_pct"),
            },
            "top_features": fit_result["feature_ranking"][:8],
            "model_architecture": metrics.get("model_name"),
            "status": "DEPLOYED_ACTIVE",
            "is_validated": metrics.get("is_validated", False)
        }

        meta_path = os.path.join(MODELS_DIR, f"{slug}_meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, indent=2)

        cls._loaded_models[slug] = model_payload
        return meta_data

    @classmethod
    def get_trained_model_status(cls, symbol: str) -> Optional[Dict[str, Any]]:
        slug = cls._slugify(symbol)
        meta_path = os.path.join(MODELS_DIR, f"{slug}_meta.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    @classmethod
    async def predict_with_ml_model(cls, db: Session, symbol: str) -> Optional[Dict[str, Any]]:
        slug = cls._slugify(symbol)
        model_path = os.path.join(MODELS_DIR, f"{slug}_model.joblib")
        if not os.path.exists(model_path):
            return None

        try:
            if slug in cls._loaded_models:
                payload = cls._loaded_models[slug]
            else:
                payload = joblib.load(model_path)
                cls._loaded_models[slug] = payload
                
            model = payload["model"]
            features = payload["features"]
            hc_threshold = payload.get("hc_threshold", 0.55)

            if is_crypto(symbol):
                df = binance_klines(symbol, interval="1d", lookback_bars=150)
            else:
                df = yf_history(symbol, period="1y", interval="1d")
                df = df.tail(150).reset_index(drop=True)
                
            if len(df) < 50:
                return None

            fng_map = cls.load_historical_fng_series()
            news_map = ScraperService.get_date_sentiment_map(db, symbol)
            
            feat_df, _, _, _ = cls.build_ml_features(df, fng_map, news_map)
            latest_features = feat_df[features].iloc[-1:].replace([np.inf, -np.inf], np.nan)
            
            if latest_features.isna().any().any():
                return None
                
            pred_class = int(model.predict(latest_features.values)[0])
            pred_prob = model.predict_proba(latest_features.values)[0]
            
            direction = "NAIK" if pred_class == 1 else "TURUN"
            prob_up = float(pred_prob[1])
            prob = prob_up if pred_class == 1 else float(pred_prob[0])
            
            tier = conviction_tier(prob_up, hc_threshold)

            return {
                "is_ml_powered": True,
                "direction": direction,
                "confidence_percent": round(prob * 100, 1),
                "prob_up": round(prob_up * 100, 1),
                "prob_down": round(float(pred_prob[0]) * 100, 1),
                "conviction_tier": tier,
                "model_date": payload.get("trained_at")
            }
        except Exception as e:
            print(f"[MLTrainingEngine] Inference error: {e}")
            return None
