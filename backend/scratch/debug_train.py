import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, init_db
from app.services.market_data import binance_klines
from app.services.ml_training_engine import MLTrainingEngine
from app.services.scraper_service import ScraperService
from app.services.quant_ml import fit_direction_model

init_db()
db = SessionLocal()
symbol = "BTC/USDT"
print("1. Fetching klines...")
df = binance_klines(symbol, interval="1d", lookback_bars=1500)
print(f"Klines fetched: {len(df)}")

print("2. Sentiment map...")
fng_map = MLTrainingEngine.load_historical_fng_series()
news_sentiment_map = ScraperService.get_date_sentiment_map(db, symbol)
print(f"FNG items: {len(fng_map)}, news items: {len(news_sentiment_map)}")

print("3. Building features...")
t0 = time.time()
feat_df, feature_cols, fwd_ret, scale = MLTrainingEngine.build_ml_features(df, fng_map, news_sentiment_map, horizon=1)
print(f"Features built in {time.time()-t0:.2f}s! Columns: {len(feature_cols)}")

print("4. Fitting direction model...")
t1 = time.time()
fit_result = fit_direction_model(
    feat=feat_df,
    candidate_cols=feature_cols,
    fwd_ret=fwd_ret,
    scale=scale,
    horizon=1,
    k_deadband=0.25,
    test_frac=0.2,
    n_splits=5,
    max_features=15,
    times=feat_df["time"],
    random_state=42
)
print(f"Fitted in {time.time()-t1:.2f}s!")
print("Best candidate:", fit_result["metrics"]["model_name"])
print("Test accuracy:", fit_result["metrics"]["test_accuracy_pct"])
