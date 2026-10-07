import os
import sys
import time
import math
from typing import Tuple, List, Dict, Any, Optional
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.market_data import binance_klines
from sklearn.metrics import accuracy_score, roc_auc_score, f1_score, precision_score, recall_score, brier_score_loss
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier, VotingClassifier, StackingClassifier
from sklearn.preprocessing import RobustScaler
from sklearn.pipeline import make_pipeline
from sklearn.base import clone

import lightgbm as lgb
import xgboost as xgb

print("=" * 85)
print("FINBLIX DEEP QUANT RESEARCH: OPTIMIZING BITCOIN (BTC/USDT) ACCURACY")
print("Evaluating Feature Engineering, Labeling Strategies, & Advanced ML Architectures")
print("=" * 85)

# -----------------------------------------------------------------------------
# 1. ADVANCED MATHEMATICAL INDICATORS
# -----------------------------------------------------------------------------
def calc_frac_diff(series: pd.Series, d: float = 0.40) -> pd.Series:
    weights = [1.0]
    k = 1
    while True:
        w = -weights[-1] / k * (d - k + 1)
        if abs(w) < 1e-4 or k > 35:
            break
        weights.append(w)
        k += 1
    weights = np.array(weights[::-1])
    s_vals = series.values
    res = np.convolve(s_vals, weights, mode='valid')
    pad = len(s_vals) - len(res)
    return pd.Series(np.pad(res, (pad, 0), mode='edge'), index=series.index)

def calc_gk_vol(h: pd.Series, l: pd.Series, c: pd.Series, o: pd.Series) -> pd.Series:
    log_hl = np.log(h / l.replace(0, 1e-9))
    log_co = np.log(c / o.replace(0, 1e-9))
    rs = 0.5 * (log_hl ** 2) - (2.0 * np.log(2.0) - 1.0) * (log_co ** 2)
    return np.sqrt(rs.rolling(14).mean()).fillna(0.0)

def calc_cs_spread(h: pd.Series, l: pd.Series) -> pd.Series:
    h_prev = h.shift(1).bfill()
    l_prev = l.shift(1).bfill()
    beta = (np.log(h / l.replace(0, 1e-9)))**2 + (np.log(h_prev / l_prev.replace(0, 1e-9)))**2
    h_max = np.maximum(h, h_prev)
    l_min = np.minimum(l, l_prev)
    gamma = (np.log(h_max / l_min.replace(0, 1e-9)))**2
    k = 3.0 - (2.0 * np.sqrt(2.0))
    alpha = (np.sqrt(2.0 * beta) - np.sqrt(beta)) / k - np.sqrt(gamma / k)
    exp_alpha = np.exp(alpha)
    return (2.0 * (exp_alpha - 1.0) / (1.0 + exp_alpha)).clip(lower=0.0, upper=0.15).fillna(0.0)

# -----------------------------------------------------------------------------
# 2. FEATURE EXTRACTOR
# -----------------------------------------------------------------------------
def extract_all_crypto_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    d = df.copy()
    close, high, low, open_p = d["close"], d["high"], d["low"], d["open"]
    vol = d["volume"].replace(0, 1)
    c_range = (high - low).replace(0, 1e-9)

    # 1. Price action wicks
    d["upper_wick"] = (high - np.maximum(close, open_p)) / c_range
    d["lower_wick"] = (np.minimum(close, open_p) - low) / c_range
    d["body_ratio"] = (close - open_p).abs() / c_range

    # 2. Momentum & returns
    d["ret_1"] = close.pct_change(1)
    d["ret_3"] = close.pct_change(3)
    d["ret_7"] = close.pct_change(7)
    d["mom_accel"] = d["ret_1"] - d["ret_3"]

    # 3. Microstructure & volatility
    d["gk_vol"] = calc_gk_vol(high, low, close, open_p)
    d["cs_spread"] = calc_cs_spread(high, low)
    d["amihud"] = (d["ret_1"].abs() / (vol * close * 1e-6 + 1e-9)).clip(upper=10.0)
    d["ofip"] = ((close - open_p) / c_range) * np.log1p(vol)

    # 4. Moving Average Confluence Ribbon
    ema9 = close.ewm(span=9, adjust=False).mean()
    ema21 = close.ewm(span=21, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    ema100 = close.ewm(span=100, adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()

    d["dist_ema9"] = (close - ema9) / (close + 1e-9)
    d["dist_ema21"] = (close - ema21) / (close + 1e-9)
    d["dist_ema50"] = (close - ema50) / (close + 1e-9)
    d["ema_alignment"] = ((ema9 > ema21).astype(int) + (ema21 > ema50).astype(int) + (ema50 > ema100).astype(int) + (ema100 > ema200).astype(int)) / 4.0
    d["ema9_slope"] = ema9.pct_change(2).fillna(0)

    # 5. Technical oscillators
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    d["rsi_14"] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_raw = ema12 - ema26
    signal = macd_raw.ewm(span=9, adjust=False).mean()
    d["macd_hist"] = (macd_raw - signal) / (close + 1e-9)
    d["rsi_macd_divergence"] = (d["rsi_14"] - 50.0) * d["macd_hist"]

    # 6. Bollinger Squeeze & Range
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    d["bb_width"] = (4 * std20) / (sma20 + 1e-9)
    d["bb_pct_b"] = (close - (sma20 - 2 * std20)) / (4 * std20 + 1e-9)
    d["bb_squeeze_roc"] = d["bb_width"].pct_change(3).fillna(0)

    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr14 = tr.rolling(14).mean()
    d["atr_norm"] = atr14 / (close + 1e-9)
    d["atr_regime"] = atr14 / (tr.rolling(50).mean() + 1e-9)
    d["trend_strength"] = (close - ema50).abs() / (atr14 + 1e-9)

    # 7. Fractional Differentiation (d=0.40)
    d["frac_diff"] = calc_frac_diff(np.log(close.replace(0, 1e-9)), d=0.40)

    # 8. Volume Dynamics
    vol_sma20 = vol.rolling(20).mean()
    d["vol_ratio"] = vol / (vol_sma20 + 1e-9)
    d["vol_roc"] = vol.pct_change(3).fillna(0).clip(-2, 5)

    feature_cols = [
        "upper_wick", "lower_wick", "body_ratio",
        "ret_1", "ret_3", "ret_7", "mom_accel",
        "gk_vol", "cs_spread", "amihud", "ofip",
        "dist_ema9", "dist_ema21", "dist_ema50", "ema_alignment", "ema9_slope",
        "rsi_14", "macd_hist", "rsi_macd_divergence",
        "bb_width", "bb_pct_b", "bb_squeeze_roc",
        "atr_norm", "atr_regime", "trend_strength",
        "frac_diff", "vol_ratio", "vol_roc"
    ]
    return d, feature_cols

# -----------------------------------------------------------------------------
# 3. BENCHMARKING MULTIPLE ARCHITECTURES
# -----------------------------------------------------------------------------
def run_model_benchmark(X_tr, y_tr, X_te, y_te, name: str) -> Dict[str, Any]:
    models = {
        "HistGBM (Current)": HistGradientBoostingClassifier(
            learning_rate=0.03, max_iter=150, max_depth=3, l2_regularization=2.0, random_state=42
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=200, max_depth=4, min_samples_leaf=20, random_state=42, n_jobs=1
        ),
        "LightGBM": lgb.LGBMClassifier(
            n_estimators=180, learning_rate=0.03, max_depth=4, num_leaves=12,
            min_child_samples=25, subsample=0.85, colsample_bytree=0.85,
            reg_alpha=0.5, reg_lambda=2.0, random_state=42, verbosity=-1
        ),
        "XGBoost": xgb.XGBClassifier(
            n_estimators=180, learning_rate=0.03, max_depth=3, subsample=0.85,
            colsample_bytree=0.85, reg_alpha=0.5, reg_lambda=3.0, random_state=42, eval_metric="logloss"
        ),
        "Ensemble (LGBM+XGB+HistGBM)": VotingClassifier([
            ("lgb", lgb.LGBMClassifier(n_estimators=160, learning_rate=0.03, max_depth=4, num_leaves=12, min_child_samples=20, subsample=0.85, reg_lambda=2.0, random_state=42, verbosity=-1)),
            ("xgb", xgb.XGBClassifier(n_estimators=160, learning_rate=0.03, max_depth=3, subsample=0.85, reg_lambda=3.0, random_state=42, eval_metric="logloss")),
            ("hgb", HistGradientBoostingClassifier(learning_rate=0.03, max_iter=140, max_depth=3, random_state=42))
        ], voting="soft")
    }

    report = {}
    for m_name, clf in models.items():
        clf.fit(X_tr, y_tr)
        probs = clf.predict_proba(X_te)[:, 1]
        preds = (probs >= 0.5).astype(int)

        acc = accuracy_score(y_te, preds)
        auc = roc_auc_score(y_te, probs) if len(np.unique(y_te)) > 1 else 0.5
        brier = brier_score_loss(y_te, probs)

        # High-Conviction (Threshold >= 0.56 or <= 0.44)
        conf = np.maximum(probs, 1 - probs)
        hc_mask = conf >= 0.56
        if hc_mask.sum() >= 15:
            hc_acc = accuracy_score(y_te[hc_mask], preds[hc_mask])
            hc_cov = hc_mask.mean()
            hc_count = int(hc_mask.sum())
        else:
            hc_acc = acc
            hc_cov = 1.0
            hc_count = len(y_te)

        # Simulated Profit Factor / Win Rate
        trade_winrate = hc_acc

        report[m_name] = {
            "test_acc": round(acc * 100, 2),
            "hc_acc": round(hc_acc * 100, 2),
            "hc_cov": round(hc_cov * 100, 2),
            "hc_count": hc_count,
            "roc_auc": round(auc * 100, 2),
            "brier": round(brier, 4)
        }
    return report

def main():
    print("\n[+] Mengunduh data Binance BTC/USDT 1D & 15M...")
    
    # -------------------------------------------------------------
    # EXPERIMENT 1: DAILY HORIZON (1D)
    # -------------------------------------------------------------
    df_1d = binance_klines("BTC/USDT", interval="1d", lookback_bars=1500)
    print(f"Data Harian BTC/USDT: {len(df_1d)} bar")

    feat_1d, cols_1d = extract_all_crypto_features(df_1d)

    # Test two labeling strategies:
    # A. 1-day ahead deadband (k=0.25 ATR)
    fwd_ret_1d = df_1d["close"].pct_change().shift(-1)
    atr_norm = feat_1d["atr_norm"]
    thr_1d = 0.25 * atr_norm
    y_db = pd.Series(np.nan, index=df_1d.index)
    y_db[fwd_ret_1d > thr_1d] = 1.0
    y_db[fwd_ret_1d < -thr_1d] = 0.0

    valid_mask = feat_1d[cols_1d].notna().all(axis=1) & y_db.notna()
    X = feat_1d.loc[valid_mask, cols_1d].values
    y = y_db[valid_mask].astype(int).values

    # Chronological holdout 80/20
    split_idx = int(len(X) * 0.80)
    X_tr, y_tr = X[:split_idx], y[:split_idx]
    X_te, y_te = X[split_idx:], y[split_idx:]

    print("\n" + "=" * 90)
    print("HASIL EVALUASI MODEL HARIAN (DAILY 1D) - BTC/USDT:")
    print("=" * 90)
    rep_1d = run_model_benchmark(X_tr, y_tr, X_te, y_te, "Daily")
    print(f"{'Algoritma / Model':<32} | {'Test Acc':<10} | {'HC Acc':<10} | {'HC Coverage':<12} | {'ROC-AUC':<10}")
    print("-" * 90)
    for m_name, m in rep_1d.items():
        print(f"{m_name:<32} | {m['test_acc']:<9}% | {m['hc_acc']:<9}% | {m['hc_cov']:<11}% | {m['roc_auc']:<9}%")

    # -------------------------------------------------------------
    # EXPERIMENT 2: MULTI-STEP INTRADAY (15M HORIZON 12 BAR / 3 JAM)
    # -------------------------------------------------------------
    df_15m = binance_klines("BTC/USDT", interval="15m", lookback_bars=4500)
    print(f"\nData Intraday 15M BTC/USDT: {len(df_15m)} bar")
    feat_15m, cols_15m = extract_all_crypto_features(df_15m)

    # 12-bar ahead return (3 Hours)
    fwd_ret_15m = (df_15m["close"].shift(-12) - df_15m["close"]) / df_15m["close"]
    thr_15m = 0.20 * feat_15m["atr_norm"] * np.sqrt(12)
    y_15m = pd.Series(np.nan, index=df_15m.index)
    y_15m[fwd_ret_15m > thr_15m] = 1.0
    y_15m[fwd_ret_15m < -thr_15m] = 0.0

    valid_15m = feat_15m[cols_15m].notna().all(axis=1) & y_15m.notna()
    X_15 = feat_15m.loc[valid_15m, cols_15m].values
    y_15 = y_15m[valid_15m].astype(int).values

    split_15 = int(len(X_15) * 0.80)
    X_tr15, y_tr15 = X_15[:split_15], y_15[:split_15]
    X_te15, y_te15 = X_15[split_15:], y_15[split_15:]

    print("\n" + "=" * 90)
    print("HASIL EVALUASI MODEL INTRADAY 3-JAM (15M x 12 BARS) - BTC/USDT:")
    print("=" * 90)
    rep_15m = run_model_benchmark(X_tr15, y_tr15, X_te15, y_te15, "15m-3h")
    print(f"{'Algoritma / Model':<32} | {'Test Acc':<10} | {'HC Acc':<10} | {'HC Coverage':<12} | {'ROC-AUC':<10}")
    print("-" * 90)
    for m_name, m in rep_15m.items():
        print(f"{m_name:<32} | {m['test_acc']:<9}% | {m['hc_acc']:<9}% | {m['hc_cov']:<11}% | {m['roc_auc']:<9}%")

    print("\n" + "=" * 90)
    print("KESIMPULAN METODE TERBAIK UNTUK BITCOIN (BTC/USDT):")
    best_daily = max(rep_1d.items(), key=lambda x: (x[1]["hc_acc"], x[1]["test_acc"]))
    best_15m = max(rep_15m.items(), key=lambda x: (x[1]["hc_acc"], x[1]["test_acc"]))
    print(f"-> Model Terbaik Daily 1D      : {best_daily[0]} (HC Acc: {best_daily[1]['hc_acc']}%, Test Acc: {best_daily[1]['test_acc']}%)")
    print(f"-> Model Terbaik Intraday 3H   : {best_15m[0]} (HC Acc: {best_15m[1]['hc_acc']}%, Test Acc: {best_15m[1]['test_acc']}%)")
    print("=" * 90)

if __name__ == "__main__":
    main()
