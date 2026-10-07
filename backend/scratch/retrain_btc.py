import os
import sys
import time
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, init_db
from app.services.ml_training_engine import MLTrainingEngine
from app.services.three_hour_engine import ThreeHourPredictionEngine

async def main():
    print("=" * 80)
    print("FINBLIX: RETRAINING BITCOIN (BTC/USDT) SOTA MACHINE LEARNING MODELS")
    print("Features: Microstructure + Fractional Diff + Garman-Klass + MTF Ribbon")
    print("Architectures: LightGBM / XGBoost / HistGBM / Stacking Ensemble")
    print("=" * 80)
    
    init_db()
    db = SessionLocal()
    
    symbol = "BTC/USDT"
    
    # 1. Train Daily Model
    print(f"\n[1/2] Melatih Model Harian (Daily 1D) untuk {symbol}...")
    t0 = time.time()
    daily_meta = await MLTrainingEngine.train_model_for_asset(db, symbol, interval="1d", horizon=1)
    d_dur = round(time.time() - t0, 2)
    print(f"-> Selesai dalam {d_dur}s!")
    print(f"   Architecture : {daily_meta.get('model_architecture')}")
    print(f"   Train Acc    : {daily_meta.get('metrics', {}).get('train_accuracy_pct')}%")
    print(f"   Test Acc     : {daily_meta.get('metrics', {}).get('test_accuracy_pct')}%")
    print(f"   ROC-AUC      : {daily_meta.get('metrics', {}).get('roc_auc_pct')}%")
    print(f"   HC Test Acc  : {daily_meta.get('metrics', {}).get('hc_test_accuracy_pct')}%")
    print(f"   HC Coverage  : {daily_meta.get('metrics', {}).get('hc_test_coverage_pct')}%")
    
    # 2. Train 15M / 3H Intraday Model
    print(f"\n[2/2] Melatih Model Intraday (15M / 3H Horizon) untuk {symbol}...")
    t1 = time.time()
    intraday_meta = await ThreeHourPredictionEngine.train_7d_model(db, symbol)
    i_dur = round(time.time() - t1, 2)
    print(f"-> Selesai dalam {i_dur}s!")
    print(f"   Architecture : {intraday_meta.get('model_architecture', 'Ensemble')}")
    print(f"   Train Acc    : {intraday_meta.get('metrics', {}).get('train_accuracy_pct', 'N/A')}%")
    print(f"   Test Acc     : {intraday_meta.get('test_accuracy_pct')}%")
    print(f"   ROC-AUC      : {intraday_meta.get('roc_auc_pct')}%")
    print(f"   HC Test Acc  : {intraday_meta.get('hc_test_accuracy_pct')}%")
    print(f"   HC Coverage  : {intraday_meta.get('hc_test_coverage_pct')}%")
    
    db.close()
    print("\n" + "=" * 80)
    print("RETRAINING BITCOIN SELESAI DENGAN SUKSES!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
