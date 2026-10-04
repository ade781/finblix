import asyncio
import sys
import os
import json
import logging

sys.path.append(r"c:\Users\ad\OneDrive\Dokumen\ad\ISENG\finblix\backend")
from app.core.database import SessionLocal
from app.services.three_hour_engine import ThreeHourEngine
from app.services.ml_training_engine import MLTrainingEngine

logging.basicConfig(level=logging.INFO)

async def test():
    db = SessionLocal()
    try:
        print("Training BTC-USDT 15m (3h outlook)...")
        res = await ThreeHourEngine.train_7d_model(db, "BTC/USDT")
        print("\nResult 15m:")
        print(json.dumps(res, indent=2))
        
        print("\nTraining BTC-USDT Daily...")
        res_daily = await MLTrainingEngine.train_model_for_asset(db, "BTC/USDT")
        print("\nResult Daily:")
        print(json.dumps(res_daily, indent=2))
    finally:
        db.close()
    
if __name__ == "__main__":
    asyncio.run(test())
