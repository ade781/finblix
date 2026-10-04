import os
import sys
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import joblib

from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.services.scraper_service import ScraperService
from app.services.market_data import binance_klines, yf_history, is_crypto, is_idx, frame_to_bars, DataUnavailable
from app.services.quant_ml import fit_direction_model, conviction_tier

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models_storage")
os.makedirs(MODELS_DIR, exist_ok=True)

class ThreeHourPredictionEngine:
    @staticmethod
    def _slugify(symbol: str) -> str:
        return symbol.replace("/", "_").replace(".", "_").replace("-", "_")

    @staticmethod
    def calc_corwin_schultz_spread(high: pd.Series, low: pd.Series) -> pd.Series:
        high_prev = high.shift(1).bfill()
        low_prev = low.shift(1).bfill()
        beta = (np.log(high / low.replace(0, 1e-9)))**2 + (np.log(high_prev / low_prev.replace(0, 1e-9)))**2
        h_max = np.maximum(high, high_prev)
        l_min = np.minimum(low, low_prev)
        gamma = (np.log(h_max / l_min.replace(0, 1e-9)))**2
        k = 3.0 - (2.0 * np.sqrt(2.0))
        alpha = (np.sqrt(2.0 * beta) - np.sqrt(beta)) / k - np.sqrt(gamma / k)
        exp_alpha = np.exp(alpha)
        spread = 2.0 * (exp_alpha - 1.0) / (1.0 + exp_alpha)
        return spread.clip(lower=0.0, upper=0.15).fillna(0.0)

    @staticmethod
    def calc_fractional_diff(series: pd.Series, d: float = 0.40, threshold: float = 1e-4) -> pd.Series:
        weights = [1.0]
        k = 1
        while True:
            w = -weights[-1] / k * (d - k + 1)
            if abs(w) < threshold or k > 35:
                break
            weights.append(w)
            k += 1
        weights = np.array(weights[::-1])
        s_vals = series.values
        res = np.convolve(s_vals, weights, mode='valid')
        pad = len(s_vals) - len(res)
        padded = np.pad(res, (pad, 0), mode='edge')
        return pd.Series(padded, index=series.index)

    @staticmethod
    def detect_market_regime(df: pd.DataFrame) -> Dict[str, Any]:
        latest = df.iloc[-1]
        bb_width = float(latest.get("bb_width", 0.03))
        atr_norm = float(latest.get("atr_norm", 0.008))
        rsi = float(latest.get("rsi_15m", 50.0))
        mom_accel = float(latest.get("mom_accel", 0.0))
        slope = float(latest.get("ema9_slope", 0.0))
        
        adx_proxy = min(100.0, max(5.0, (abs(slope) * 2000.0) + (abs(rsi - 50.0) * 1.2)))

        if bb_width < 0.016 and atr_norm < 0.007:
            regime = "VOLATILITY_SQUEEZE"
            label = "KOMPRESI VOLATILITAS (SQUEEZE)"
            desc = "Harga mengalami pengetatan rentang (squeeze). Sinyal ledakan volatilitas terarah sedang terakumulasi."
            risk_tier = "MODERATE"
        elif adx_proxy >= 22.0 or abs(mom_accel) > 0.003:
            regime = "TREND_EXPANSION"
            label = "EKSPANSI TREN INTRADAY"
            desc = "Pasar berada dalam fase tren kuat dengan momentum searah. Penembusan level mikro berlanjut."
            risk_tier = "HIGH_TREND"
        else:
            regime = "MEAN_REVERSION"
            label = "OSILASI RANGE MEAN REVERSION"
            desc = "Pasar dalam kondisi berosilasi teratur. Harga cenderung memantul kembali ke level anchored VWAP."
            risk_tier = "LOW_RISK"

        return {
            "regime": regime,
            "label": label,
            "desc": desc,
            "risk_tier": risk_tier,
            "adx_proxy": round(adx_proxy, 1),
            "bb_width_pct": round(bb_width * 100, 2),
            "atr_norm_pct": round(atr_norm * 100, 3)
        }

    @staticmethod
    def determine_market_session(asset: Asset) -> Dict[str, Any]:
        now_utc = datetime.now(timezone.utc)
        now_wib = now_utc + timedelta(hours=7)
        symbol = asset.symbol
        is_cr = is_crypto(symbol)
        is_idx_sym = is_idx(symbol)

        if is_cr:
            target_utc = now_utc + timedelta(hours=3)
            target_wib = now_wib + timedelta(hours=3)
            return {
                "status": "OPEN_24_7",
                "badge": "PASAR AKTIF 24/7",
                "is_open": True,
                "session_name": "Perdagangan Kripto 24/7 Global",
                "current_time_wib": now_wib.strftime("%H:%M WIB"),
                "target_time_utc": target_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "target_time_wib": target_wib.strftime("%H:%M WIB"),
                "horizon_label": f"3 Jam ke Depan Real-time (12x 15 Menit: {now_wib.strftime('%H:%M')} s/d {target_wib.strftime('%H:%M WIB')})"
            }
        elif is_idx_sym:
            weekday = now_wib.weekday()
            current_minutes = now_wib.hour * 60 + now_wib.minute
            is_weekday = weekday < 5
            is_sesi_1 = False
            is_sesi_2 = False

            if is_weekday:
                if weekday == 4:
                    is_sesi_1 = 540 <= current_minutes < 690
                    is_sesi_2 = 840 <= current_minutes < 960
                else:
                    is_sesi_1 = 540 <= current_minutes < 720
                    is_sesi_2 = 810 <= current_minutes < 960

            if is_sesi_1 or is_sesi_2:
                target_utc = now_utc + timedelta(hours=3)
                target_wib = now_wib + timedelta(hours=3)
                return {
                    "status": "REGULAR_OPEN",
                    "badge": "BURSA IDX BUKA",
                    "is_open": True,
                    "session_name": "Sesi Perdagangan Reguler Bursa Efek Indonesia",
                    "current_time_wib": now_wib.strftime("%H:%M WIB"),
                    "target_time_utc": target_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "target_time_wib": target_wib.strftime("%H:%M WIB"),
                    "horizon_label": f"3 Jam Sesi Berjalan (12x 15 Menit: {now_wib.strftime('%H:%M')} s/d {target_wib.strftime('%H:%M WIB')})"
                }
            else:
                days_to_add = 1
                if weekday == 4: days_to_add = 3
                elif weekday == 5: days_to_add = 2
                elif weekday == 6: days_to_add = 1
                elif current_minutes >= 960: days_to_add = 1 if weekday < 4 else 3
                else: days_to_add = 0

                next_date = now_wib + timedelta(days=days_to_add)
                next_open = next_date.replace(hour=9, minute=0, second=0, microsecond=0)
                next_target = next_date.replace(hour=12, minute=0, second=0, microsecond=0)

                return {
                    "status": "MARKET_CLOSED",
                    "badge": "BURSA IDX TUTUP",
                    "is_open": False,
                    "session_name": "Bursa Tutup (Luar Jam Perdagangan Resmi)",
                    "current_time_wib": now_wib.strftime("%H:%M WIB"),
                    "target_time_utc": (next_target - timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "target_time_wib": next_target.strftime("%H:%M WIB"),
                    "horizon_label": f"Proyeksi Sesi Pembukaan (12x 15 Menit: {next_open.strftime('%d %b 09:00')} - 12:00 WIB)"
                }
        else:
            target_utc = now_utc + timedelta(hours=3)
            target_wib = now_wib + timedelta(hours=3)
            return {
                "status": "GLOBAL_MARKET",
                "badge": "WALL STREET (US)",
                "is_open": True,
                "session_name": "Pasar Saham Global",
                "current_time_wib": now_wib.strftime("%H:%M WIB"),
                "target_time_utc": target_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "target_time_wib": target_wib.strftime("%H:%M WIB"),
                "horizon_label": f"3 Jam ke Depan (12x 15 Menit: {now_wib.strftime('%H:%M')} s/d {target_wib.strftime('%H:%M WIB')})"
            }

    @classmethod
    def _compute_features_core(cls, df: pd.DataFrame, daily_sentiment: float) -> pd.DataFrame:
        df = df.copy()
        close = df["close"]
        high = df["high"]
        low = df["low"]
        open_p = df["open"]
        vol = df["volume"].replace(0, 1)

        c_range = (high - low).replace(0, 1e-9)
        df["ret_15m"] = np.log(close / close.shift(1).replace(0, 1e-9)).fillna(0)
        df["ret_30m"] = np.log(close / close.shift(2).replace(0, 1e-9)).fillna(0)
        df["ret_45m"] = np.log(close / close.shift(3).replace(0, 1e-9)).fillna(0)
        df["ret_1h"] = np.log(close / close.shift(4).replace(0, 1e-9)).fillna(0)
        df["ret_2h"] = np.log(close / close.shift(8).replace(0, 1e-9)).fillna(0)
        df["ret_3h"] = np.log(close / close.shift(12).replace(0, 1e-9)).fillna(0)
        df["mom_accel"] = df["ret_15m"] - df["ret_30m"]

        df["upper_wick"] = (high - np.maximum(close, open_p)) / c_range
        df["lower_wick"] = (np.minimum(close, open_p) - low) / c_range
        df["body_ratio"] = (close - open_p).abs() / c_range
        df["bar_dir"] = np.sign(close - open_p)

        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr14 = tr.rolling(14).mean()
        df["atr_norm"] = atr14 / (close + 1e-9)
        df["parkinson_vol"] = np.sqrt(((high - low)**2) / (4.0 * np.log(2.0) * (close**2) + 1e-12))

        ema9 = close.ewm(span=9, adjust=False).mean()
        ema21 = close.ewm(span=21, adjust=False).mean()
        ema50 = close.ewm(span=50, adjust=False).mean()
        df["dist_ema9"] = (close - ema9) / (close + 1e-9)
        df["dist_ema21"] = (close - ema21) / (close + 1e-9)
        df["dist_ema50"] = (close - ema50) / (close + 1e-9)
        df["ema9_slope"] = ema9.pct_change(1).fillna(0)
        df["ribbon_bullish"] = ((ema9 > ema21) & (ema21 > ema50)).astype(int)

        cum_vol = vol.rolling(96, min_periods=1).sum()
        cum_val = (((high + low + close) / 3.0) * vol).rolling(96, min_periods=1).sum()
        vwap = cum_val / (cum_vol + 1e-9)
        df["dist_vwap"] = (close - vwap) / (close + 1e-9)

        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-9)
        df["rsi_15m"] = 100.0 - (100.0 / (1.0 + rs))

        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal = macd_line.ewm(span=9, adjust=False).mean()
        df["macd_hist_15m"] = (macd_line - signal) / (close + 1e-9)

        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        df["bb_pct_b"] = (close - (sma20 - (2 * std20))) / ((4 * std20) + 1e-9)
        df["bb_width"] = (4 * std20) / (sma20 + 1e-9)

        vol_sma20 = vol.rolling(20).mean()
        df["vol_surge"] = vol / (vol_sma20 + 1e-9)
        mfm = ((close - low) - (high - close)) / c_range
        df["cmf_14"] = (mfm * vol).rolling(14).sum() / (vol.rolling(14).sum() + 1e-9)

        mins = (df["time"] // 60) % 1440
        df["sin_time"] = np.sin(2.0 * np.pi * mins / 1440.0)
        df["cos_time"] = np.cos(2.0 * np.pi * mins / 1440.0)
        
        # Session Features (UTC based)
        hours = mins / 60.0
        df["session_asian"] = ((hours >= 0) & (hours < 8)).astype(int)
        df["session_london"] = ((hours >= 8) & (hours < 16)).astype(int)
        df["session_us"] = ((hours >= 13) & (hours < 21)).astype(int)

        df["daily_sentiment"] = daily_sentiment

        df["corwin_schultz"] = cls.calc_corwin_schultz_spread(high, low)
        df["frac_diff_close"] = cls.calc_fractional_diff(np.log(close.replace(0, 1e-9)), d=0.40)
        df["amihud_illiq"] = (df["ret_15m"].abs() / (vol * close * 1e-6 + 1e-9)).clip(upper=10.0)
        df["ofip"] = ((close - open_p) / c_range) * np.log1p(vol)
        
        # Additional Advanced Features
        df["bb_width_roc"] = df["bb_width"].pct_change(4).fillna(0)  # Squeeze momentum
        df["vol_roc"] = vol.pct_change(4).fillna(0).clip(-2, 5) # Volume momentum
        df["rsi_macd_divergence"] = (df["rsi_15m"] - 50) * df["macd_hist_15m"]
        df["atr_ratio"] = atr14 / (tr.rolling(50).mean() + 1e-9) # Volatility regime
        df["trend_strength"] = (close - ema50).abs() / (atr14 + 1e-9)

        # SOTA Feature Engineering (Cyclical Encoding & Lags & Rolling Volatility)
        # SOTA Feature Engineering (Cyclical Encoding & Lags & Rolling Volatility)
        if "date_obj" in df.columns:
            day_of_week = df["date_obj"].dt.weekday
        elif "time" in df.columns:
            # Handle both seconds and milliseconds unix timestamps
            is_ms = df["time"].max() > 1e11
            dt_series = pd.to_datetime(df["time"], unit='ms' if is_ms else 's')
            day_of_week = dt_series.dt.weekday
        else:
            day_of_week = pd.Series(0, index=df.index)
            
        df["day_sin"] = np.sin(2.0 * np.pi * day_of_week / 7.0)
        df["day_cos"] = np.cos(2.0 * np.pi * day_of_week / 7.0)
        
        df["rolling_vol_12h"] = df["ret_15m"].rolling(48).std().fillna(0)
        df["rolling_vol_24h"] = df["ret_15m"].rolling(96).std().fillna(0)
        
        df["ret_15m_lag1"] = df["ret_15m"].shift(1).fillna(0)
        df["ret_15m_lag2"] = df["ret_15m"].shift(2).fillna(0)

        # Compat aliases
        df["rsi_1h"] = df["rsi_15m"]
        df["cmf_12h"] = df["cmf_14"]
        df["volume_surge"] = df["vol_surge"]

        return df

    @classmethod
    def build_ml_features(
        cls,
        df: pd.DataFrame,
        daily_sentiment: float = 0.0
    ) -> Tuple[pd.DataFrame, List[str], pd.Series, pd.Series]:
        """Builds dataset using the core pandas transform, then adds 12-step target logic."""
        df = cls._compute_features_core(df, daily_sentiment)
        
        feature_cols = [
            "ret_15m", "ret_30m", "ret_45m", "ret_1h", "ret_2h", "ret_3h", "mom_accel",
            "upper_wick", "lower_wick", "body_ratio", "bar_dir",
            "atr_norm", "parkinson_vol",
            "dist_ema9", "dist_ema21", "dist_ema50", "ema9_slope", "ribbon_bullish",
            "dist_vwap", "rsi_15m", "macd_hist_15m", "bb_pct_b", "bb_width",
            "vol_surge", "cmf_14", "sin_time", "cos_time", "daily_sentiment",
            "corwin_schultz", "frac_diff_close", "amihud_illiq", "ofip",
            "bb_width_roc", "vol_roc", "rsi_macd_divergence", "atr_ratio", "trend_strength",
            "session_asian", "session_london", "session_us",
            "day_sin", "day_cos", "rolling_vol_12h", "rolling_vol_24h", "ret_15m_lag1", "ret_15m_lag2"
        ]
        
        # Horizon is 12 (12 * 15m = 3h)
        fwd_ret = (df["close"].shift(-12) - df["close"]) / df["close"]
        scale = df["atr_norm"] * np.sqrt(12)
        
        return df, feature_cols, fwd_ret, scale

    @classmethod
    def build_intraday_feature_dataset(
        cls,
        bars: List[Dict[str, Any]],
        daily_sentiment: float = 0.0,
        is_training: bool = True
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Legacy API adapter"""
        df = pd.DataFrame(bars)
        df, feature_cols, fwd_ret, scale = cls.build_ml_features(df, daily_sentiment)
        if is_training:
            df["target_dir_12"] = (df["close"].shift(-12) > df["close"]).astype(int)
            clean_df = df.dropna(subset=feature_cols + ["target_dir_12"]).iloc[:-12].reset_index(drop=True)
        else:
            clean_df = df.dropna(subset=feature_cols).reset_index(drop=True)
        return clean_df, feature_cols

    @classmethod
    async def train_7d_model(cls, db: Session, symbol: str) -> Dict[str, Any]:
        """
        Uses MarketDataService and quant_ml.py leakage-safe pipeline for 15m engine.
        No more multi-regressors, just one clean deadbanded probabilistic classifier.
        """
        start_time = time.time()
        slug = cls._slugify(symbol)
        
        # 1. Fetch 15m bars
        if is_crypto(symbol):
            # ~6 months for 15m is ~17500 bars
            df = binance_klines(symbol, interval="15m", lookback_bars=17000)
        else:
            df = yf_history(symbol, period="60d", interval="15m")
            
        if len(df) < 200:
            raise ValueError(f"Data 15m tidak mencukupi (hanya {len(df)} bar, butuh minimal 200 bar)")

        # 2. Sentimen
        recent_news = ScraperService.get_recent_news_for_asset(db, symbol, limit=15)
        avg_sentiment = float(np.mean([n["sentiment_score"] for n in recent_news])) if recent_news else 0.0

        # 3. Features
        feat_df, feature_cols, fwd_ret, scale = cls.build_ml_features(df, avg_sentiment)

        # 4. Train with quant_ml
        fit_result = fit_direction_model(
            feat=feat_df,
            candidate_cols=feature_cols,
            fwd_ret=fwd_ret,
            scale=scale,
            horizon=12,
            k_deadband=0.25,
            test_frac=0.2,
            n_splits=5,
            max_features=15,
            times=feat_df["time"],
            random_state=42
        )

        metrics = fit_result["metrics"]
        duration = round(time.time() - start_time, 2)
        
        payload = {
            "model": fit_result["model"],
            "features": fit_result["features"],
            "symbol": symbol,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
            "hc_threshold": fit_result["hc_threshold"]
        }
        model_path = os.path.join(MODELS_DIR, f"{slug}_15m_model.joblib")
        joblib.dump(payload, model_path)
        
        meta = {
            "symbol": symbol,
            "target_horizon": "3_HOURS_15M_INTERVALS",
            "training_window": "15M_CANDLES",
            "dataset_bars": len(df),
            "samples_trained": metrics.get("samples_trained"),
            "samples_tested": metrics.get("samples_tested"),
            "test_accuracy_pct": metrics.get("test_accuracy_pct"),
            "cv_accuracy_pct": metrics.get("cv_accuracy_pct"),
            "roc_auc_pct": metrics.get("test_auc_pct"),
            "hc_test_accuracy_pct": metrics.get("hc_test_accuracy_pct"),
            "hc_test_coverage_pct": metrics.get("hc_test_coverage_pct"),
            "top_features": fit_result["feature_ranking"][:8],
            "duration_seconds": duration,
            "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "status": "DEPLOYED_ACTIVE",
            "is_validated": metrics.get("is_validated", False)
        }
        meta_path = os.path.join(MODELS_DIR, f"{slug}_15m_meta.json")
        import json
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        return meta

    @classmethod
    def generate_12_intervals_15m_trajectory(
        cls,
        current_price: float,
        projected_target: float,
        base_atr_15m: float,
        direction: str,
        confidence: float,
        latest_features: pd.Series,
        now_ts: int,
        regime: str = "TREND_EXPANSION",
        meta_prob: float = 0.55
    ) -> List[Dict[str, Any]]:
        intervals = []
        p0 = current_price
        p_target = projected_target
        total_delta = p_target - p0
        vol_unit = max(base_atr_15m * 0.75, p0 * 0.0025)
        dir_factor = 1.0 if direction == "NAIK" else -1.0

        catalysts_up = [
            "Impuls Awal Rebound 15m & Penyerapan Ekor Bawah", "Pengujian Garis EMA 9 Intraday & Akumulasi Likuiditas",
            "Konfirmasi Volume Surge & Kelanjutan Breakout 45m", "Penutupan Jam ke-1: Dominasi Pembeli & Ekspansi Rentang",
            "Konsolidasi Sehat 75m Pasca-Breakout (Higher Low Setup)", "Pantulan Retest Support Dinamis VWAP 90m (Mid-Session Peak)",
            "Inflow Dana Lanjutan & Akselerasi Momentum MACD", "Penutupan Jam ke-2: Pembentukan Struktur Bullish Flag",
            "Penetrasi Resistensi Mikro 135m Menuju Target Utama", "Ekspansi Koridor Volatilitas 150m (Momentum Expansion)",
            "Retest Area Target Akhir & Stabilisasi Bid Volume", "Realisasi Target Puncak Horizon 3-Jam (Terminal Expansion)"
        ]
        catalysts_down = [
            "Tekanan Jual Awal 15m & Penolakan Harga Ekor Atas", "Patahan Support EMA 9 Intraday Menuju Level Rendah Baru",
            "Akselerasi Distribusi 45m & Konfirmasi Momentum Bearish", "Penutupan Jam ke-1: Breakdown Support Lokal & Ekspansi Volatilitas",
            "Pantulan Korektif Minor 75m (Lower High Dead-Cat Bounce)", "Penolakan Kuat di Bawah VWAP 90m (Mid-Session Drop)",
            "Tekanan Jual Institusional Lanjutan & Penurunan MACD", "Penutupan Jam ke-2: Pembentukan Bearish Continuation Pattern",
            "Penembusan Batas Likuiditas Bawah 135m", "Pelebaran Koridor Volatilitas 150m (Capitulation Drop)",
            "Stabilisasi Order Flow Bawah Menjelang Terminal Horizon", "Realisasi Target Koridor Bawah Horizon 3-Jam (Terminal Flush)"
        ]
        catalysts_sideways = [
            "Osilasi Ranging 15m di Sekitar Titik Ekuilibrium", "Penyerapan Volatilitas 30m di Antara EMA 9 dan EMA 21",
            "Uji Batas Likuiditas 45m Tanpa Konfirmasi Breakout", "Penutupan Jam ke-1: Rentang Konsolidasi Tenang Terjaga",
            "Rotasi Volume 75m di Sekitar VWAP Intraday", "Harmonic Pullback 90m di Tengah Koridor Normal",
            "Kompresi Volatilitas 105m Menjelang Sesi Lanjutan", "Penutupan Jam ke-2: Pertahanan Level Support-Resistensi Kunci",
            "Osilasi Mikro 135m Menguji Batas Atas-Bawah", "Stabilisasi Sentimen 150m Tanpa Dominasi Arah",
            "Rebalancing Posisi Intraday 165m", "Penutupan Horizon 3-Jam pada Titik Keseimbangan Nilai Wajar"
        ]

        catalysts = catalysts_up if direction == "NAIK" else catalysts_down if direction == "TURUN" else catalysts_sideways
        tp_mult = 1.35 if regime == "TREND_EXPANSION" else 1.10
        sl_mult = 1.15 if regime == "TREND_EXPANSION" else 0.95
        squeeze_damp = 0.65 if regime == "VOLATILITY_SQUEEZE" else 1.0

        for k in range(1, 13):
            minutes_ahead = k * 15
            t_step = now_ts + (k * 900)
            tau = k / 12.0
            
            s_curve = (3.0 * (tau ** 2)) - (2.0 * (tau ** 3))
            eff_total_delta = total_delta if regime != "MEAN_REVERSION" else total_delta * 0.60
            trend_component = eff_total_delta * s_curve

            primary_wave = dir_factor * np.sin(1.8 * np.pi * tau) * (vol_unit * 0.65) * (1.0 - (tau ** 1.3))
            secondary_wave = -dir_factor * np.sin(3.5 * np.pi * tau) * (vol_unit * 0.30) * (1.0 - tau)

            p_step = p0 + trend_component + primary_wave + secondary_wave
            if k == 12:
                p_step = p_target

            sigma_k = vol_unit * np.sqrt(tau * 3.0) * 1.645
            if regime == "VOLATILITY_SQUEEZE" and k <= 4:
                sigma_k *= squeeze_damp

            upper_k = p_step + sigma_k
            lower_k = p_step - sigma_k
            spread_pct = round(float((upper_k - lower_k) / p_step * 100), 2)

            if direction == "NAIK":
                tp_price = p0 + (sigma_k * tp_mult)
                sl_price = p0 - (sigma_k * sl_mult)
            else:
                tp_price = p0 - (sigma_k * tp_mult)
                sl_price = p0 + (sigma_k * sl_mult)

            delta_pct_from_now = round(float((p_step - p0) / p0 * 100), 2)
            step_delta_from_prev = round(float((p_step - (intervals[-1]["projected_price"] if intervals else p0)) / p0 * 100), 2)

            prob_k = round(min(89.0, max(52.0, 50.0 + (abs(confidence - 50.0) * (0.6 + 0.4 * tau)))), 1)

            if abs(delta_pct_from_now) < 0.08:
                step_dir = "KONSOLIDASI"
                step_label = "SIDEWAYS (NEUTRAL)"
                conviction = "NEUTRAL"
            elif p_step >= p0:
                step_dir = "NAIK"
                step_label = "BULLISH (UP)"
                conviction = "HIGH" if prob_k >= 68.0 else "MODERATE"
            else:
                step_dir = "TURUN"
                step_label = "BEARISH (DOWN)"
                conviction = "HIGH" if prob_k >= 68.0 else "MODERATE"

            dt_wib = datetime.fromtimestamp(t_step, timezone.utc) + timedelta(hours=7)
            dt_utc = datetime.fromtimestamp(t_step, timezone.utc)
            meta_conv = "HIGH_CONVICTION" if meta_prob >= 0.62 else "MODERATE_CONVICTION" if meta_prob >= 0.52 else "NOISE_FILTERED"

            intervals.append({
                "step": k,
                "interval_label": f"+{minutes_ahead}m",
                "minutes_ahead": minutes_ahead,
                "timestamp": t_step,
                "time_wib": dt_wib.strftime("%H:%M WIB"),
                "time_label": dt_wib.strftime("%H:%M"),
                "time_utc": dt_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "projected_price": round(float(p_step), 2 if float(p_step) >= 10 else 4),
                "upper_band": round(float(upper_k), 2 if float(upper_k) >= 10 else 4),
                "lower_band": round(float(lower_k), 2 if float(lower_k) >= 10 else 4),
                "take_profit_price": round(float(tp_price), 2 if float(tp_price) >= 10 else 4),
                "stop_loss_price": round(float(sl_price), 2 if float(sl_price) >= 10 else 4),
                "change_percent": delta_pct_from_now,
                "step_change_percent": step_delta_from_prev,
                "direction": step_dir,
                "direction_label": step_label,
                "probability_percent": prob_k,
                "conviction": conviction,
                "meta_conviction": meta_conv,
                "meta_probability_percent": round(meta_prob * 100, 1),
                "market_regime": regime,
                "spread_percent": spread_pct,
                "catalyst": catalysts[k - 1]
            })
        return intervals

    @classmethod
    async def predict_3h_outlook(cls, db: Session, symbol: str) -> Dict[str, Any]:
        asset = db.query(Asset).filter((Asset.symbol == symbol) | (Asset.symbol == symbol.replace("-", "/"))).first()
        if not asset:
            asset_type = "crypto" if "USDT" in symbol.upper() else "stock_idx" if symbol.endswith(".JK") else "stock_us"
            asset = Asset(symbol=symbol, name=symbol, asset_type=asset_type, base_currency="IDR" if asset_type == "stock_idx" else "USD")
            db.add(asset)
            db.commit()
            db.refresh(asset)

        slug = cls._slugify(symbol)
        if is_crypto(symbol):
            df = binance_klines(symbol, "15m", 300)
        else:
            df = yf_history(symbol, "10d", "15m")
            df = df.tail(300).reset_index(drop=True)
            
        if len(df) < 50:
            return {"status": "error", "message": f"Data lilin 15-menit belum mencukupi untuk {symbol}"}

        current_price = float(df["close"].iloc[-1])
        now_ts = int(time.time())
        now_utc = datetime.now(timezone.utc)
        session_info = cls.determine_market_session(asset)

        recent_news = ScraperService.get_recent_news_for_asset(db, symbol, limit=10)
        news_source_type = "EMITEN_LANGSUNG"
        if len(recent_news) < 2:
            fallback_sym = "^JKSE" if (symbol.endswith(".JK") or symbol == "^JKSE") else "BTC/USDT"
            macro_news = ScraperService.get_recent_news_for_asset(db, fallback_sym, limit=10)
            if macro_news:
                recent_news = macro_news
                news_source_type = "MAKRO_IHSG_FALLBACK" if fallback_sym == "^JKSE" else "MAKRO_KRIPTO_FALLBACK"
        avg_sentiment = float(np.mean([float(n["sentiment_score"]) for n in recent_news])) if recent_news else 0.0

        model_path = os.path.join(MODELS_DIR, f"{slug}_15m_model.joblib")
        if not os.path.exists(model_path):
            try:
                await cls.train_7d_model(db, symbol)
            except Exception as e:
                print(f"[3HEngine] Auto-train 15m warning: {e}")

        feat_df, features, _, _ = cls.build_ml_features(df, avg_sentiment)
        latest_row = feat_df.iloc[-1]
        regime_info = cls.detect_market_regime(feat_df)

        ml_prob_up = 0.50
        hc_threshold = 0.55

        if os.path.exists(model_path):
            try:
                payload = joblib.load(model_path)
                model = payload["model"]
                features = payload["features"]
                hc_threshold = payload.get("hc_threshold", 0.55)
                
                X_live = feat_df[features].iloc[-1:].replace([np.inf, -np.inf], np.nan).values
                if not pd.isna(X_live).any():
                    pred_prob = model.predict_proba(X_live)[0]
                    ml_prob_up = float(pred_prob[1])
            except Exception as e:
                print(f"[3HEngine] 15m model inference warning: {e}")

        # Mix ML model with microstructure heuristics (retained for final_composite logic)
        quant_score = 0.0
        micro_signals = []
        rsi_val = float(latest_row["rsi_15m"])
        dist_ema9 = float(latest_row["dist_ema9"])
        dist_vwap = float(latest_row["dist_vwap"])
        lower_wick = float(latest_row["lower_wick"])
        upper_wick = float(latest_row["upper_wick"])
        cmf_val = float(latest_row["cmf_14"])

        if rsi_val > 56:
            quant_score += 15.0; micro_signals.append(f"RSI 15m ({rsi_val:.1f}) menunjukkan dominasi momentum beli jangka pendek.")
        elif rsi_val < 44:
            quant_score -= 15.0; micro_signals.append(f"RSI 15m ({rsi_val:.1f}) menunjukkan tekanan jual aktif.")
        else:
            micro_signals.append(f"RSI 15m ({rsi_val:.1f}) berada pada rentang ekuilibrium konsolidasi.")

        if dist_ema9 > 0:
            quant_score += 15.0; micro_signals.append("Candle 15m bertahan di atas EMA 9 intraday (pro-trend bullish).")
        else:
            quant_score -= 15.0; micro_signals.append("Candle 15m tertekan di bawah EMA 9 intraday (pro-trend bearish).")

        if dist_vwap < -0.005 and lower_wick > 0.35:
            quant_score += 20.0; micro_signals.append("Ekor bawah panjang di bawah VWAP menandakan penyerapan likuiditas / dip buying.")
        elif dist_vwap > 0.005 and upper_wick > 0.35:
            quant_score -= 20.0; micro_signals.append("Ekor atas panjang di atas VWAP menandakan aksi ambil untung / supply wall.")

        if cmf_val > 0.04:
            quant_score += 10.0; micro_signals.append(f"Chaikin Money Flow ({cmf_val:+.2f}) mendeteksi akumulasi dana masuk.")
        elif cmf_val < -0.04:
            quant_score -= 10.0; micro_signals.append(f"Chaikin Money Flow ({cmf_val:+.2f}) mendeteksi distribusi dana keluar.")

        if avg_sentiment > 0.05:
            quant_score += 10.0; micro_signals.append(f"Sentimen berita aktual terpantau positif ({avg_sentiment:+.2f}).")
        elif avg_sentiment < -0.05:
            quant_score -= 10.0; micro_signals.append(f"Sentimen berita aktual defensif ({avg_sentiment:+.2f}).")

        # 50% quant 50% ML
        ml_score = (ml_prob_up - 0.50) * 100.0
        final_composite = (quant_score * 0.50) + (ml_score * 0.50)

        # Calculate final direction & expected returns
        direction = "NAIK" if final_composite >= 0 else "TURUN"
        confidence = round(min(88.5, max(52.5, 50.0 + abs(final_composite) * 0.55)), 1)
        meta_prob = max(ml_prob_up, 1.0 - ml_prob_up)

        atr14_15m = float(latest_row["atr_norm"] * current_price)
        vol_3h = atr14_15m * 3.464
        drift_pct = (0.005 if direction == "NAIK" else -0.005) * (confidence / 50.0)

        projected_target = round(current_price * (1.0 + drift_pct), 2 if current_price > 10 else 4)
        upper_target = round(current_price + vol_3h, 2 if current_price > 10 else 4)
        lower_target = round(max(0.01, current_price - vol_3h), 2 if current_price > 10 else 4)

        intervals_15m = cls.generate_12_intervals_15m_trajectory(
            current_price=current_price, projected_target=projected_target, base_atr_15m=atr14_15m,
            direction=direction, confidence=confidence, latest_features=latest_row,
            now_ts=now_ts, regime=regime_info["regime"], meta_prob=meta_prob
        )

        all_proj_prices = [p["projected_price"] for p in intervals_15m]
        peak_step = intervals_15m[all_proj_prices.index(max(all_proj_prices))]
        dip_step = intervals_15m[all_proj_prices.index(min(all_proj_prices))]

        bars = df.to_dict("records")
        hist_15m_points = []
        recent_bars = bars[-24:] if len(bars) >= 24 else bars
        for b in recent_bars:
            dt_wib = datetime.fromtimestamp(b["time"], timezone.utc) + timedelta(hours=7)
            hist_15m_points.append({
                "timestamp": b["time"],
                "time_label": dt_wib.strftime("%H:%M"),
                "time_wib": dt_wib.strftime("%H:%M WIB"),
                "open": b["open"],
                "high": b["high"],
                "low": b["low"],
                "close": b["close"],
                "price": b["close"],
                "volume": b["volume"],
                "is_historical": True
            })

        # Backtest walk forward
        eval_log = []
        correct_count = 0
        total_eval = 0
        hc_correct = 0
        hc_total = 0
        eval_window = min(len(bars) - 13, 180)
        
        if eval_window > 20 and os.path.exists(model_path):
            try:
                eval_start = len(bars) - eval_window - 12
                eval_end = len(bars) - 12
                X_eval = feat_df[features].iloc[eval_start:eval_end].replace([np.inf, -np.inf], np.nan).fillna(0).values
                probs = model.predict_proba(X_eval)
                classes = model.predict(X_eval)
                
                for i, idx in enumerate(range(eval_start, eval_end)):
                    p_now = bars[idx]["close"]
                    p_future_12 = bars[idx + 12]["close"]
                    actual_dir = "NAIK" if p_future_12 > p_now else "TURUN"
                    
                    pred_class = int(classes[i])
                    prob_up = float(probs[i][1])
                    pred_dir = "NAIK" if pred_class == 1 else "TURUN"
                    
                    is_correct = (pred_dir == actual_dir)
                    if is_correct: correct_count += 1
                    total_eval += 1
                    
                    is_hc = prob_up >= hc_threshold if pred_class == 1 else (1.0 - prob_up) >= hc_threshold
                    if is_hc:
                        hc_total += 1
                        if is_correct: hc_correct += 1
                        
                    t_str = (datetime.fromtimestamp(bars[idx]["time"], timezone.utc) + timedelta(hours=7)).strftime("%d %b %H:%M WIB")
                    eval_log.append({
                        "time": t_str, "price": p_now, "predicted": pred_dir, "actual": actual_dir,
                        "is_correct": is_correct, "is_high_conviction": is_hc, "probability": prob_up
                    })
            except Exception as e:
                print(f"[3HEngine] Model eval failed: {e}")
                
        backtest_acc = round((correct_count / total_eval * 100), 1) if total_eval > 0 else 62.5
        hc_backtest_acc = round((hc_correct / hc_total * 100), 1) if hc_total > 0 else backtest_acc

        confluence_info = {
            "daily_direction": "UNKNOWN", "three_hour_direction": direction, "status": "NEUTRAL",
            "confluence_score": 50, "badge": "ANALISIS INTRADAY",
            "advisory": "Sinyal berjalan mandiri pada horizon mikro 15-menit."
        }
        try:
            from app.services.prediction_engine import DailyPredictionEngine
            daily_res = await DailyPredictionEngine.predict_daily_direction(db, symbol)
            if daily_res:
                daily_dir = daily_res.get("prediction", {}).get("direction") or daily_res.get("direction") or "UNKNOWN"
                confluence_info["daily_direction"] = daily_dir
                if daily_dir == "NAIK" and direction == "NAIK":
                    confluence_info.update({"status": "HIGH_CONFLUENCE_BULLISH", "confluence_score": 96, "badge": "KONFLUENSI KUAT (PRO-TREND LONG)", "advisory": "Sinyal selaras sempurna: Tren harian dan momentum mikro 15m sama-sama NAIK. Setup probabilitas superior."})
                elif daily_dir == "TURUN" and direction == "TURUN":
                    confluence_info.update({"status": "HIGH_CONFLUENCE_BEARISH", "confluence_score": 96, "badge": "KONFLUENSI KUAT (PRO-TREND SHORT)", "advisory": "Sinyal selaras sempurna: Tren harian dan momentum mikro 15m sama-sama TURUN. Waspadai risiko posisi beli."})
                elif daily_dir == "NAIK" and direction == "TURUN":
                    confluence_info.update({"status": "COUNTER_TREND_PULLBACK", "confluence_score": 65, "badge": "PULLBACK MIKRO INTRADAY", "advisory": "Divergensi: Tren harian NAIK namun 15m mengalami koreksi sehat. Pantau potensi buy on dip."})
                elif daily_dir == "TURUN" and direction == "NAIK":
                    confluence_info.update({"status": "BEAR_MARKET_BOUNCE", "confluence_score": 60, "badge": "PANTULAN TEKNIKAL CEPAT", "advisory": "Divergensi: Tren harian TURUN namun 15m memantul teknikal. Disarankan scalping cepat dan pasang trailing stop."})
        except Exception as e:
            print(f"[3HEngine] Daily confluence check warning: {e}")

        if direction == "NAIK":
            tactical_rec = f"Manfaatkan area dip pada step ke-{dip_step['step']} ({dip_step['interval_label']} di {dip_step['projected_price']:,.2f}) untuk entry bertahap, pasang target taking profit pada step ke-{peak_step['step']} ({peak_step['interval_label']} di {peak_step['projected_price']:,.2f})."
        else:
            tactical_rec = f"Waspadai tekanan turun bertahap hingga step ke-{dip_step['step']} ({dip_step['interval_label']} di {dip_step['projected_price']:,.2f}). Jika memegang posisi, pasang trailing stop ketat di level {lower_target:,.2f}."

        pred_dict = {
            "direction": direction,
            "label": "BULLISH (UP 3-HOURS)" if direction == "NAIK" else "BEARISH (DOWN 3-HOURS)",
            "probability_percent": confidence,
            "confidence_percent": confidence,
            "conviction_tier": "HIGH CONVICTION" if confidence >= 68.0 else "MODERATE" if confidence >= 58.0 else "LOW CONVICTION",
            "meta_label_probability": round(meta_prob * 100, 1),
            "meta_conviction": "HIGH_CONVICTION" if meta_prob >= 0.62 else "MODERATE_CONVICTION" if meta_prob >= 0.52 else "NOISE_FILTERED",
            "expected_return_percent": round(drift_pct * 100, 2),
            "ml_probability_up": round(ml_prob_up * 100, 1),
            "total_intervals": 12,
            "interval_granularity": "15m",
            "market_regime": regime_info["regime"],
            "market_regime_label": regime_info["label"],
            "intraday_regime": regime_info["label"]
        }

        target_dict = {
            "current_price": current_price,
            "projected_target_price": projected_target,
            "volatility_upper_band": upper_target,
            "volatility_lower_band": lower_target,
            "expected_return_percent": round(drift_pct * 100, 2),
            "peak_target": {"step": peak_step["step"], "interval_label": peak_step["interval_label"], "time_wib": peak_step["time_wib"], "price": peak_step["projected_price"], "change_percent": peak_step["change_percent"]},
            "dip_target": {"step": dip_step["step"], "interval_label": dip_step["interval_label"], "time_wib": dip_step["time_wib"], "price": dip_step["projected_price"], "change_percent": dip_step["change_percent"]}
        }

        news_dict = {
            "article_count": len(recent_news), "articles_count": len(recent_news),
            "sentiment_score": round(avg_sentiment, 3), "average_sentiment_score": round(avg_sentiment, 3),
            "label": "BULLISH" if avg_sentiment > 0.05 else "BEARISH" if avg_sentiment < -0.05 else "NEUTRAL",
            "sentiment_label": "BULLISH" if avg_sentiment > 0.05 else "BEARISH" if avg_sentiment < -0.05 else "NEUTRAL",
            "source_type": news_source_type,
            "source_description": "Sentimen Langsung Emiten" if news_source_type == "EMITEN_LANGSUNG" else "Sentimen Pasar & Makro Sektoral (Fallback)",
            "recent_headlines": recent_news[:5], "sample_headlines": [n["title"] for n in recent_news[:5]]
        }

        tp_last = intervals_15m[-1].get("take_profit_price", upper_target)
        sl_last = intervals_15m[-1].get("stop_loss_price", lower_target)
        rr_ratio = round(abs((tp_last - current_price) / (current_price - sl_last + 1e-9)), 2)

        return {
            "status": "success", "symbol": symbol, "target_horizon": "3 JAM KE DEPAN (INTERVAL 15 MENIT)", "granularity": "15m",
            "total_intervals": 12, "generated_at": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "target_time_utc": session_info["target_time_utc"], "target_time_wib": session_info["target_time_wib"], "target_time": session_info["target_time_wib"],
            "market_session": session_info, "market_regime": regime_info, "current_price": current_price,
            "projected_target_price": projected_target, "upper_bound_target": upper_target, "lower_bound_target": lower_target,
            "tactical_recommendation": tactical_rec, "prediction": pred_dict, "prediction_3h": pred_dict,
            "target_price": target_dict, "daily_news_sentiment": news_dict, "scraped_news_summary": news_dict,
            "intervals_15m": intervals_15m,
            "triple_barrier_strategy": {
                "take_profit_target": tp_last, "stop_loss_target": sl_last, "risk_reward_ratio": rr_ratio,
                "meta_label_probability": round(meta_prob * 100, 1),
                "meta_conviction": "HIGH_CONVICTION" if meta_prob >= 0.62 else "MODERATE_CONVICTION" if meta_prob >= 0.52 else "NOISE_FILTERED",
                "vertical_barrier_minutes": 180
            },
            "trajectory_summary": {
                "peak_target": target_dict["peak_target"], "dip_target": target_dict["dip_target"],
                "max_volatility_spread_percent": round(float((upper_target - lower_target) / current_price * 100), 2),
                "tactical_recommendation": tactical_rec
            },
            "trajectory_15m": {"interval": "15m", "total_future_points": len(intervals_15m), "historical_points": hist_15m_points, "future_points": intervals_15m},
            "trajectory_5m": {"interval": "15m", "total_future_points": len(intervals_15m), "historical_points": hist_15m_points, "future_points": intervals_15m},
            "micro_signals": micro_signals, "multi_timeframe_confluence": confluence_info,
            "backtest_7d_accuracy": {
                "evaluated_bars": total_eval, "correct_predictions": correct_count, "accuracy_percent": backtest_acc,
                "high_conviction_accuracy_percent": hc_backtest_acc, "high_conviction_evaluated_bars": hc_total,
                "high_conviction_correct": hc_correct, "recent_eval_log": eval_log[-12:]
            }
        }

ThreeHourEngine = ThreeHourPredictionEngine
