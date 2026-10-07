import asyncio
import sys
import os

sys.path.append(r"c:\Users\ad\OneDrive\Dokumen\ad\ISENG\finblix\backend")

from app.core.database import SessionLocal
from app.services.ml_training_engine import MLTrainingEngine
from app.services.three_hour_engine import ThreeHourEngine

ASSETS = [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT",
    "XRP/USDT",
    "DOGE/USDT",
    "ADA/USDT",
    "AVAX/USDT"
]

async def train_all():
    db = SessionLocal()
    try:
        for sym in ASSETS:
            print(f"\n==========================================")
            print(f"Training models for {sym}")
            print(f"==========================================\n")
            
            print(f"--- 1. Training Daily Model ({sym}) ---")
            try:
                daily_meta = await MLTrainingEngine.train_model_for_asset(db, sym)
                print(f"Daily Accuracy: {daily_meta.get('metrics', {}).get('test_accuracy_pct', 0)}%")
                print(f"Daily HC Coverage: {daily_meta.get('metrics', {}).get('hc_test_coverage_pct', 0)}%")
            except Exception as e:
                print(f"Failed daily training for {sym}: {e}")
                
            print(f"\n--- 2. Training 15m Model ({sym}) ---")
            try:
                hm_meta = await ThreeHourEngine.train_7d_model(db, sym)
                print(f"15m Accuracy: {hm_meta.get('test_accuracy_pct', 0)}%")
                print(f"15m HC Coverage: {hm_meta.get('hc_test_coverage_pct', 0)}%")
            except Exception as e:
                print(f"Failed 15m training for {sym}: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(train_all())
