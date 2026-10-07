import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.market_data import binance_klines
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.ensemble import HistGradientBoostingClassifier, VotingClassifier
import lightgbm as lgb
import xgboost as xgb

print("=" * 80)
print("TESTING MULTI-TIMEFRAME (15M + 1H + 4H) CONFLUENCE ON BITCOIN (BTC/USDT)")
print("=" * 80)

# Fetch 15m bars (around 10,000 bars for robust testing)
df_15m = binance_klines("BTC/USDT", interval="15m", lookback_bars=8000)
print(f"Data 15M loaded: {len(df_15m)} bars")

# Resample to 1H and 4H to construct higher-timeframe features
df_15m["dt"] = pd.to_datetime(df_15m["time"], unit="s", utc=True)
df_15m = df_15m.set_index("dt").sort_index()

# 1H Resample
df_1h = df_15m.resample("1h").agg({
    "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
}).dropna()
df_1h["ema20_1h"] = df_1h["close"].ewm(span=20, adjust=False).mean()
df_1h["ema50_1h"] = df_1h["close"].ewm(span=50, adjust=False).mean()
df_1h["dist_ema50_1h"] = (df_1h["close"] - df_1h["ema50_1h"]) / (df_1h["close"] + 1e-9)
df_1h["trend_1h"] = (df_1h["ema20_1h"] > df_1h["ema50_1h"]).astype(int)
delta_1h = df_1h["close"].diff()
gain_1h = delta_1h.where(delta_1h > 0, 0).rolling(14).mean()
loss_1h = (-delta_1h.where(delta_1h < 0, 0)).rolling(14).mean()
df_1h["rsi_1h"] = 100 - (100 / (1 + gain_1h / (loss_1h + 1e-9)))

# 4H Resample
df_4h = df_15m.resample("4h").agg({
    "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
}).dropna()
df_4h["ema20_4h"] = df_4h["close"].ewm(span=20, adjust=False).mean()
df_4h["ema50_4h"] = df_4h["close"].ewm(span=50, adjust=False).mean()
df_4h["trend_4h"] = (df_4h["ema20_4h"] > df_4h["ema50_4h"]).astype(int)

# Reindex and forward-fill onto 15m
df_15m = df_15m.reset_index()
df_1h = df_1h[["dist_ema50_1h", "trend_1h", "rsi_1h"]].reset_index()
df_4h = df_4h[["trend_4h"]].reset_index()

merged = pd.merge_asof(df_15m, df_1h, on="dt", direction="backward")
merged = pd.merge_asof(merged, df_4h, on="dt", direction="backward")

close = merged["close"]
high = merged["high"]
low = merged["low"]
open_p = merged["open"]
vol = merged["volume"].replace(0, 1)
c_range = (high - low).replace(0, 1e-9)

merged["upper_wick"] = (high - np.maximum(close, open_p)) / c_range
merged["lower_wick"] = (np.minimum(close, open_p) - low) / c_range
merged["body_ratio"] = (close - open_p).abs() / c_range
merged["ret_15m"] = close.pct_change(1)
merged["ret_1h"] = close.pct_change(4)
merged["ret_3h"] = close.pct_change(12)

ema9 = close.ewm(span=9, adjust=False).mean()
ema21 = close.ewm(span=21, adjust=False).mean()
ema50 = close.ewm(span=50, adjust=False).mean()
merged["dist_ema9"] = (close - ema9) / (close + 1e-9)
merged["dist_ema21"] = (close - ema21) / (close + 1e-9)
merged["dist_ema50"] = (close - ema50) / (close + 1e-9)
merged["ema_align_15m"] = ((ema9 > ema21).astype(int) + (ema21 > ema50).astype(int)) / 2.0

delta = close.diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
merged["rsi_15m"] = 100 - (100 / (1 + gain / (loss + 1e-9)))

tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
atr14 = tr.rolling(14).mean()
merged["atr_norm"] = atr14 / (close + 1e-9)
merged["vol_ratio"] = vol / (vol.rolling(20).mean() + 1e-9)

# Macro Multi-Timeframe Trend Confluence Score
merged["mtf_confluence"] = (merged["ema_align_15m"] + merged["trend_1h"] + merged["trend_4h"]) / 3.0

feature_cols = [
    "upper_wick", "lower_wick", "body_ratio",
    "ret_15m", "ret_1h", "ret_3h",
    "dist_ema9", "dist_ema21", "dist_ema50", "ema_align_15m",
    "rsi_15m", "atr_norm", "vol_ratio",
    "dist_ema50_1h", "trend_1h", "rsi_1h", "trend_4h", "mtf_confluence"
]

# Target: 12 bars (3 hours ahead) with deadband
fwd_ret = (merged["close"].shift(-12) - merged["close"]) / merged["close"]
thr = 0.25 * merged["atr_norm"] * np.sqrt(12)
y = pd.Series(np.nan, index=merged.index)
y[fwd_ret > thr] = 1.0
y[fwd_ret < -thr] = 0.0

valid = merged[feature_cols].notna().all(axis=1) & y.notna()
X_clean = merged.loc[valid, feature_cols].values
y_clean = y[valid].astype(int).values

print(f"Valid samples: {len(X_clean)} bars")

# Walk-forward 80/20
split = int(len(X_clean) * 0.80)
X_tr, y_tr = X_clean[:split], y_clean[:split]
X_te, y_te = X_clean[split:], y_clean[split:]

models = {
    "HistGBM": HistGradientBoostingClassifier(learning_rate=0.03, max_iter=150, max_depth=3, random_state=42),
    "LightGBM": lgb.LGBMClassifier(n_estimators=180, learning_rate=0.03, max_depth=4, num_leaves=12, min_child_samples=25, subsample=0.85, random_state=42, verbosity=-1),
    "XGBoost": xgb.XGBClassifier(n_estimators=180, learning_rate=0.03, max_depth=3, subsample=0.85, random_state=42, eval_metric="logloss"),
    "Ensemble (Voting)": VotingClassifier([
        ("lgb", lgb.LGBMClassifier(n_estimators=160, learning_rate=0.03, max_depth=4, num_leaves=12, random_state=42, verbosity=-1)),
        ("xgb", xgb.XGBClassifier(n_estimators=160, learning_rate=0.03, max_depth=3, random_state=42, eval_metric="logloss")),
        ("hgb", HistGradientBoostingClassifier(learning_rate=0.03, max_iter=140, max_depth=3, random_state=42))
    ], voting="soft")
}

print(f"\n{'Model':<20} | {'Test Acc':<10} | {'HC Acc (>=0.56)':<18} | {'HC Coverage':<12} | {'ROC-AUC':<10}")
print("-" * 75)
for name, m in models.items():
    m.fit(X_tr, y_tr)
    probs = m.predict_proba(X_te)[:, 1]
    preds = (probs >= 0.5).astype(int)
    acc = accuracy_score(y_te, preds)
    auc = roc_auc_score(y_te, probs)
    conf = np.maximum(probs, 1 - probs)
    hc_mask = conf >= 0.56
    hc_acc = accuracy_score(y_te[hc_mask], preds[hc_mask]) if hc_mask.sum() >= 10 else acc
    hc_cov = hc_mask.mean()
    print(f"{name:<20} | {acc*100:<9.2f}% | {hc_acc*100:<17.2f}% | {hc_cov*100:<11.2f}% | {auc*100:<9.2f}%")
