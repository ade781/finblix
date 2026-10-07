import os
import sys
import time
import math
from typing import Tuple, List, Dict, Any, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timezone

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.market_data import binance_klines
from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score, f1_score, brier_score_loss
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier, VotingClassifier, StackingClassifier
from sklearn.preprocessing import RobustScaler
from sklearn.pipeline import make_pipeline
from sklearn.base import clone

import lightgbm as lgb
import xgboost as xgb

print("=" * 80)
print("FINBLIX DEEP RESEARCH: BITCOIN (BTC/USDT) DIRECTION ACCURACY UPGRADE")
print("Benchmarking 4 Method Variations with Walk-Forward Out-of-Sample Validation")
print("=" * 80)

# =============================================================================
# 1. ADVANCED MATHEMATICAL & MICROSTRUCTURE FEATURE FUNCTIONS
# =============================================================================

def calc_fractional_diff(series: pd.Series, d: float = 0.40, threshold: float = 1e-4) -> pd.Series:
    """Marcos Lopez de Prado's Fractional Differentiation (Preserves Memory while Stationary)"""
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

def calc_corwin_schultz(high: pd.Series, low: pd.Series) -> pd.Series:
    """Corwin-Schultz (2012) Bid-Ask Spread Estimator from High-Low Prices"""
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

def calc_garman_klass_vol(high: pd.Series, low: pd.Series, close: pd.Series, open_p: pd.Series, window: int = 14) -> pd.Series:
    """Garman-Klass (1980) Volatility Estimator (8x more efficient than close-to-close std)"""
    log_hl = np.log(high / low.replace(0, 1e-9))
    log_co = np.log(close / open_p.replace(0, 1e-9))
    rs = 0.5 * (log_hl ** 2) - (2.0 * np.log(2.0) - 1.0) * (log_co ** 2)
    return np.sqrt(rs.rolling(window).mean()).fillna(0.0)

def calc_parkinson_vol(high: pd.Series, low: pd.Series, window: int = 14) -> pd.Series:
    """Parkinson (1980) High-Low Volatility Estimator"""
    log_hl = np.log(high / low.replace(0, 1e-9))
    rs = (log_hl ** 2) / (4.0 * np.log(2.0))
    return np.sqrt(rs.rolling(window).mean()).fillna(0.0)

def calc_triple_barrier_labels(df: pd.DataFrame, horizon: int = 4, pt_mult: float = 1.2, sl_mult: float = 1.2) -> pd.Series:
    """
    Marcos Lopez de Prado's Triple Barrier Method:
    Barrier 1: Profit-Take (Upper = Close + pt_mult * ATR) -> Label 1
    Barrier 2: Stop-Loss (Lower = Close - sl_mult * ATR) -> Label 0
    Barrier 3: Vertical Time Barrier (t + horizon) -> Label based on sign of return
    """
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    atr = (df["high"] - df["low"]).rolling(14).mean().bfill().values
    n = len(df)
    labels = np.full(n, np.nan)
    
    for i in range(n - horizon):
        entry_p = close[i]
        curr_atr = max(atr[i], entry_p * 0.003)
        upper_barrier = entry_p + (pt_mult * curr_atr)
        lower_barrier = entry_p - (sl_mult * curr_atr)
        
        hit = None
        for step in range(1, horizon + 1):
            idx = i + step
            if high[idx] >= upper_barrier and low[idx] <= lower_barrier:
                # Both hit in same bar -> use bar direction
                hit = 1.0 if close[idx] >= entry_p else 0.0
                break
            elif high[idx] >= upper_barrier:
                hit = 1.0
                break
            elif low[idx] <= lower_barrier:
                hit = 0.0
                break
                
        if hit is None:
            # Vertical barrier reached
            fwd_ret = (close[i + horizon] - entry_p) / entry_p
            # Only label if return exceeded small noise threshold (0.2 * ATR)
            if abs(fwd_ret) >= (0.2 * curr_atr / entry_p):
                hit = 1.0 if fwd_ret > 0 else 0.0
            else:
                hit = np.nan # drop noise
                
        labels[i] = hit
        
    return pd.Series(labels, index=df.index)

# =============================================================================
# 2. FEATURE PIPELINES FOR VARIATIONS
# =============================================================================

def build_features_baseline(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Variasi 0: Fitur Teknikal Standar (Single Timeframe)"""
    d = df.copy()
    close, high, low, open_p, vol = d["close"], d["high"], d["low"], d["open"], d["volume"].replace(0, 1)
    c_range = (high - low).replace(0, 1e-9)
    
    d["ret_1"] = close.pct_change(1)
    d["ret_3"] = close.pct_change(3)
    d["ret_7"] = close.pct_change(7)
    
    d["upper_wick"] = (high - np.maximum(close, open_p)) / c_range
    d["lower_wick"] = (np.minimum(close, open_p) - low) / c_range
    d["body_ratio"] = (close - open_p).abs() / c_range
    
    # RSI 14
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    d["rsi_14"] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    d["macd_hist"] = (macd_line - signal) / (close + 1e-9)
    
    # Bollinger Bands
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    d["bb_pct_b"] = (close - (sma20 - 2 * std20)) / (4 * std20 + 1e-9)
    d["bb_width"] = (4 * std20) / (sma20 + 1e-9)
    
    # ATR
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    d["atr_norm"] = tr.rolling(14).mean() / (close + 1e-9)
    d["vol_ratio"] = vol / (vol.rolling(20).mean() + 1e-9)
    
    cols = ["ret_1", "ret_3", "ret_7", "upper_wick", "lower_wick", "body_ratio", "rsi_14", "macd_hist", "bb_pct_b", "bb_width", "atr_norm", "vol_ratio"]
    return d, cols

def build_features_v1(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Variasi 1: Multi-Timeframe Alignment + Microstructure Volatility"""
    d, base_cols = build_features_baseline(df)
    close, high, low, open_p, vol = d["close"], d["high"], d["low"], d["open"], d["volume"].replace(0, 1)
    
    # Microstructure
    d["garman_klass_vol"] = calc_garman_klass_vol(high, low, close, open_p, window=14)
    d["parkinson_vol"] = calc_parkinson_vol(high, low, window=14)
    d["corwin_schultz"] = calc_corwin_schultz(high, low)
    d["amihud_illiq"] = (d["ret_1"].abs() / (vol * close * 1e-6 + 1e-9)).clip(upper=10.0)
    
    # Multi-Timeframe Trend Proxies (EMA 9, 21, 50, 100, 200)
    ema9 = close.ewm(span=9, adjust=False).mean()
    ema21 = close.ewm(span=21, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    ema100 = close.ewm(span=100, adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()
    
    d["dist_ema9"] = (close - ema9) / (close + 1e-9)
    d["dist_ema21"] = (close - ema21) / (close + 1e-9)
    d["dist_ema50"] = (close - ema50) / (close + 1e-9)
    d["dist_ema200"] = (close - ema200) / (close + 1e-9)
    d["ema_alignment"] = ((ema9 > ema21).astype(int) + (ema21 > ema50).astype(int) + (ema50 > ema100).astype(int) + (ema100 > ema200).astype(int)) / 4.0
    d["ema9_slope"] = ema9.pct_change(2).fillna(0)
    
    cols = base_cols + ["garman_klass_vol", "parkinson_vol", "corwin_schultz", "amihud_illiq", "dist_ema9", "dist_ema21", "dist_ema50", "dist_ema200", "ema_alignment", "ema9_slope"]
    return d, cols

def build_features_v2(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Variasi 2: Fractional Differentiation + Squeeze Breakout Momentum"""
    d, v1_cols = build_features_v1(df)
    close, high, low, open_p, vol = d["close"], d["high"], d["low"], d["open"], d["volume"].replace(0, 1)
    
    # Fractional Differentiation on log price (d=0.40)
    d["frac_diff_close"] = calc_fractional_diff(np.log(close.replace(0, 1e-9)), d=0.40)
    d["frac_diff_mom"] = d["frac_diff_close"].diff(3).fillna(0)
    
    # Bollinger Band Squeeze Rate of Change (Breakout indicator)
    d["bb_width_roc"] = d["bb_width"].pct_change(4).fillna(0)
    d["vol_roc"] = vol.pct_change(4).fillna(0).clip(-2, 5)
    
    # Chande Momentum Oscillator (CMO)
    delta = close.diff()
    sum_up = delta.where(delta > 0, 0).rolling(14).sum()
    sum_dn = (-delta.where(delta < 0, 0)).rolling(14).sum()
    d["cmo_14"] = (100 * (sum_up - sum_dn) / (sum_up + sum_dn + 1e-9)).fillna(0) / 100.0
    
    # Order Flow Imbalance Proxy (OFIP)
    c_range = (high - low).replace(0, 1e-9)
    d["ofip"] = ((close - open_p) / c_range) * np.log1p(vol)
    
    cols = v1_cols + ["frac_diff_close", "frac_diff_mom", "bb_width_roc", "vol_roc", "cmo_14", "ofip"]
    return d, cols

def build_features_v3_hybrid(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Variasi 3 (SOTA): Multi-Scale Confluence + Microstructure + Volatility Regime Gating"""
    d, v2_cols = build_features_v2(df)
    close, high, low, open_p, vol = d["close"], d["high"], d["low"], d["open"], d["volume"].replace(0, 1)
    
    # Volatility Regime Feature (Ratio of short-term ATR to 50-period range)
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr14 = tr.rolling(14).mean()
    d["atr_regime_ratio"] = atr14 / (tr.rolling(50).mean() + 1e-9)
    d["trend_strength"] = (close - close.ewm(span=50, adjust=False).mean()).abs() / (atr14 + 1e-9)
    
    # RSI - MACD Interaction Divergence
    d["rsi_macd_divergence"] = (d["rsi_14"] - 50.0) * d["macd_hist"]
    
    # Cyclical Time Encoding (if time exists)
    if "time" in d.columns:
        dt = pd.to_datetime(d["time"], unit="s", utc=True)
        hours = dt.dt.hour + dt.dt.minute / 60.0
        d["hour_sin"] = np.sin(2.0 * np.pi * hours / 24.0)
        d["hour_cos"] = np.cos(2.0 * np.pi * hours / 24.0)
        d["day_sin"] = np.sin(2.0 * np.pi * dt.dt.weekday / 7.0)
        d["day_cos"] = np.cos(2.0 * np.pi * dt.dt.weekday / 7.0)
        time_cols = ["hour_sin", "hour_cos", "day_sin", "day_cos"]
    else:
        time_cols = []
        
    cols = v2_cols + ["atr_regime_ratio", "trend_strength", "rsi_macd_divergence"] + time_cols
    return d, cols

# =============================================================================
# 3. PURGED WALK-FORWARD CROSS-VALIDATION HARNESS
# =============================================================================

def purged_walk_forward_eval(
    X: np.ndarray, 
    y: np.ndarray, 
    model_builder_fn, 
    horizon: int = 4, 
    n_splits: int = 5,
    min_train_frac: float = 0.40
) -> Dict[str, Any]:
    """
    Expanding-Window Purged Walk-Forward Cross Validation:
    Strictly prevents lookahead leakage by purging overlap samples between train and test.
    """
    n = len(X)
    first_test_idx = int(n * min_train_frac)
    test_block_size = max(1, (n - first_test_idx) // n_splits)
    
    all_y_true = []
    all_y_pred = []
    all_y_prob = []
    
    for split in range(n_splits):
        t0 = first_test_idx + split * test_block_size
        t1 = n if split == n_splits - 1 else t0 + test_block_size
        
        # Purge training set: samples within horizon before t0 must be purged!
        train_end = t0 - horizon
        if train_end < 100:
            continue
            
        X_tr = X[:train_end]
        y_tr = y[:train_end]
        
        X_te = X[t0:t1]
        y_te = y[t0:t1]
        
        if len(np.unique(y_tr)) < 2 or len(y_te) == 0:
            continue
            
        clf = model_builder_fn()
        clf.fit(X_tr, y_tr)
        
        prob = clf.predict_proba(X_te)[:, 1]
        pred = (prob >= 0.5).astype(int)
        
        all_y_true.extend(y_te)
        all_y_pred.extend(pred)
        all_y_prob.extend(prob)
        
    y_true = np.array(all_y_true)
    y_pred = np.array(all_y_pred)
    y_prob = np.array(all_y_prob)
    
    # Calculate overall metrics
    acc = accuracy_score(y_true, y_pred)
    auc = roc_auc_score(y_true, y_prob) if len(np.unique(y_true)) > 1 else 0.5
    f1 = f1_score(y_true, y_pred, zero_division=0)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    brier = brier_score_loss(y_true, y_prob)
    
    # High Conviction filter (top confidence signals)
    conf = np.maximum(y_prob, 1 - y_prob)
    hc_mask = conf >= 0.60
    if hc_mask.sum() >= 20:
        hc_acc = accuracy_score(y_true[hc_mask], y_pred[hc_mask])
        hc_cov = hc_mask.mean()
        hc_count = int(hc_mask.sum())
    else:
        # Lower threshold slightly if sample count is small
        hc_mask = conf >= 0.55
        hc_acc = accuracy_score(y_true[hc_mask], y_pred[hc_mask]) if hc_mask.sum() > 0 else acc
        hc_cov = hc_mask.mean()
        hc_count = int(hc_mask.sum())
        
    # Simulated trading performance (PnL proxy)
    # Long when prob >= 0.55, Short when prob <= 0.45
    long_correct = ((y_prob >= 0.55) & (y_true == 1)).sum()
    long_total = (y_prob >= 0.55).sum()
    short_correct = ((y_prob <= 0.45) & (y_true == 0)).sum()
    short_total = (y_prob <= 0.45).sum()
    
    total_trades = long_total + short_total
    winning_trades = long_correct + short_correct
    trade_winrate = (winning_trades / total_trades) if total_trades > 0 else 0.0
    
    return {
        "samples_evaluated": len(y_true),
        "accuracy": round(acc * 100, 2),
        "roc_auc": round(auc * 100, 2),
        "f1_score": round(f1, 4),
        "precision": round(prec * 100, 2),
        "recall": round(rec * 100, 2),
        "brier_score": round(brier, 4),
        "hc_accuracy": round(hc_acc * 100, 2),
        "hc_coverage": round(hc_cov * 100, 2),
        "hc_count": hc_count,
        "trade_winrate": round(trade_winrate * 100, 2),
        "trade_count": int(total_trades)
    }

# =============================================================================
# 4. EXECUTION OF BENCHMARK EXPERIMENTS
# =============================================================================

def run_experiments():
    symbol = "BTC/USDT"
    print(f"\n[+] Mengunduh data historis Binance untuk {symbol}...")
    
    # We test on both:
    # 1. 15-Minute Intraday Horizon (Multi-bar 12-step / 3 hours forward)
    # 2. Daily Horizon (1-day / 3-days forward)
    
    for timeframe, bars_count, horizon in [("15m", 4500, 8), ("1d", 1500, 1)]:
        print("\n" + "=" * 80)
        print(f"BENCHMARK UNTUK TIMEFRAME: {timeframe.upper()} (HORIZON: {horizon} BAR)")
        print("=" * 80)
        
        raw_df = binance_klines(symbol, interval=timeframe, lookback_bars=bars_count)
        print(f"Total bar terkumpul: {len(raw_df)} bar ({timeframe})")
        
        # Prepare targets
        # Target A: Deadband label (k=0.25 ATR)
        fwd_ret = (raw_df["close"].shift(-horizon) - raw_df["close"]) / raw_df["close"]
        atr14 = (raw_df["high"] - raw_df["low"]).rolling(14).mean()
        thr = 0.25 * (atr14 / raw_df["close"]) * np.sqrt(horizon)
        y_deadband = pd.Series(np.nan, index=raw_df.index)
        y_deadband[fwd_ret > thr] = 1.0
        y_deadband[fwd_ret < -thr] = 0.0
        
        # Target B: Triple Barrier Label (Marcos Lopez de Prado)
        y_triple_barrier = calc_triple_barrier_labels(raw_df, horizon=horizon, pt_mult=1.1, sl_mult=1.1)
        
        results = {}
        
        # -------------------------------------------------------------
        # VARIASI 0: Baseline (Current Finblix System)
        # Features: Standard TA (12 features)
        # Target: Deadband (k=0.25)
        # Model: HistGradientBoosting + RandomForest (Soft Vote)
        # -------------------------------------------------------------
        print("Running Variasi 0: Baseline Finblix (HistGBM + RF, Basic TA)...")
        df_v0, cols_v0 = build_features_baseline(raw_df)
        valid_v0 = df_v0[cols_v0].notna().all(axis=1) & y_deadband.notna()
        X_v0 = df_v0.loc[valid_v0, cols_v0].values
        y_v0 = y_deadband[valid_v0].astype(int).values
        
        def model_v0():
            return VotingClassifier([
                ("hgb", HistGradientBoostingClassifier(learning_rate=0.03, max_iter=150, max_depth=3, random_state=42)),
                ("rf", RandomForestClassifier(n_estimators=150, max_depth=4, random_state=42, n_jobs=1))
            ], voting="soft")
            
        results["Variasi 0 (Baseline)"] = purged_walk_forward_eval(X_v0, y_v0, model_v0, horizon=horizon)
        
        # -------------------------------------------------------------
        # VARIASI 1: Multi-Timeframe Alignment + Microstructure Alpha
        # Features: Base + Garman-Klass + Parkinson + Corwin-Schultz + EMA Ribbon
        # Target: Deadband (k=0.25)
        # Model: LightGBM Classifier (fast, robust gradient boosted trees)
        # -------------------------------------------------------------
        print("Running Variasi 1: Multi-Timeframe + Microstructure (LightGBM)...")
        df_v1, cols_v1 = build_features_v1(raw_df)
        valid_v1 = df_v1[cols_v1].notna().all(axis=1) & y_deadband.notna()
        X_v1 = df_v1.loc[valid_v1, cols_v1].values
        y_v1 = y_deadband[valid_v1].astype(int).values
        
        def model_v1():
            return lgb.LGBMClassifier(
                n_estimators=150,
                learning_rate=0.03,
                max_depth=4,
                num_leaves=12,
                min_child_samples=30,
                subsample=0.85,
                colsample_bytree=0.85,
                reg_alpha=0.5,
                reg_lambda=2.0,
                random_state=42,
                verbosity=-1
            )
            
        results["Variasi 1 (MTF + LightGBM)"] = purged_walk_forward_eval(X_v1, y_v1, model_v1, horizon=horizon)
        
        # -------------------------------------------------------------
        # VARIASI 2: Lopez de Prado Fractional Differentiation + Triple Barrier Method
        # Features: V1 + FracDiff(d=0.40) + BB Squeeze ROC + Chande CMO + OFIP
        # Target: Dynamic Volatility Triple Barrier Labeling
        # Model: XGBoost + LightGBM Ensemble
        # -------------------------------------------------------------
        print("Running Variasi 2: Lopez de Prado (FracDiff + Triple Barrier + XGB/LGBM)...")
        df_v2, cols_v2 = build_features_v2(raw_df)
        valid_v2 = df_v2[cols_v2].notna().all(axis=1) & y_triple_barrier.notna()
        X_v2 = df_v2.loc[valid_v2, cols_v2].values
        y_v2 = y_triple_barrier[valid_v2].astype(int).values
        
        def model_v2():
            m_lgb = lgb.LGBMClassifier(
                n_estimators=150, learning_rate=0.03, max_depth=4, num_leaves=12,
                min_child_samples=25, subsample=0.85, reg_lambda=2.0, random_state=42, verbosity=-1
            )
            m_xgb = xgb.XGBClassifier(
                n_estimators=150, learning_rate=0.03, max_depth=3, subsample=0.85,
                colsample_bytree=0.85, reg_lambda=3.0, random_state=42, eval_metric="logloss"
            )
            return VotingClassifier([("lgb", m_lgb), ("xgb", m_xgb)], voting="soft")
            
        results["Variasi 2 (TripleBarrier + FracDiff)"] = purged_walk_forward_eval(X_v2, y_v2, model_v2, horizon=horizon)
        
        # -------------------------------------------------------------
        # VARIASI 3: SOTA Hybrid Quant System
        # Features: Multi-Scale Confluence + FracDiff + Microstructure + Volatility Regime Gating
        # Target: Dynamic Volatility Triple Barrier
        # Model: Stacking Meta-Classifier (LightGBM + XGBoost + HistGBM -> Logistic Regression Meta-Learner)
        # -------------------------------------------------------------
        print("Running Variasi 3: SOTA Hybrid Quant (Multi-Scale + Regime Gating + Stacking Ensemble)...")
        df_v3, cols_v3 = build_features_v3_hybrid(raw_df)
        valid_v3 = df_v3[cols_v3].notna().all(axis=1) & y_triple_barrier.notna()
        X_v3 = df_v3.loc[valid_v3, cols_v3].values
        y_v3 = y_triple_barrier[valid_v3].astype(int).values
        
        def model_v3():
            base_estimators = [
                ("lgb", lgb.LGBMClassifier(
                    n_estimators=160, learning_rate=0.025, max_depth=4, num_leaves=12,
                    min_child_samples=25, subsample=0.85, reg_lambda=2.5, random_state=42, verbosity=-1
                )),
                ("xgb", xgb.XGBClassifier(
                    n_estimators=160, learning_rate=0.025, max_depth=3, subsample=0.85,
                    colsample_bytree=0.85, reg_lambda=3.5, random_state=42, eval_metric="logloss"
                )),
                ("hgb", HistGradientBoostingClassifier(
                    learning_rate=0.025, max_iter=140, max_depth=3, l2_regularization=3.0, random_state=42
                ))
            ]
            meta_learner = LogisticRegression(C=0.1, penalty="l2", solver="lbfgs")
            return StackingClassifier(estimators=base_estimators, final_estimator=meta_learner, cv=3, n_jobs=1)
            
        results["Variasi 3 (SOTA Stacking Hybrid)"] = purged_walk_forward_eval(X_v3, y_v3, model_v3, horizon=horizon)
        
        # -------------------------------------------------------------
        # PRINT COMPARATIVE REPORT TABLE
        # -------------------------------------------------------------
        print("\n" + "=" * 105)
        print(f"HASIL PERBANDINGAN EMPIRIS - BITCOIN ({timeframe.upper()})")
        print("=" * 105)
        header = f"{'Model & Metode':<36} | {'Test Acc':<10} | {'HC Acc':<10} | {'HC Cov':<8} | {'ROC-AUC':<9} | {'F1':<7} | {'WinRate':<9}"
        print(header)
        print("-" * 105)
        
        for name, m in results.items():
            print(f"{name:<36} | {m['accuracy']:<9}% | {m['hc_accuracy']:<9}% | {m['hc_coverage']:<7}% | {m['roc_auc']:<8}% | {m['f1_score']:<7} | {m['trade_winrate']:<8}%")
        print("=" * 105)

if __name__ == "__main__":
    run_experiments()
