import sys
import os
import asyncio

backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.services.three_hour_engine import ThreeHourPredictionEngine

SYMBOLS = [
    # Cryptocurrencies
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "BNB/USDT",
    "XRP/USDT",
    # Indonesian Stocks
    "BBCA.JK",
    "BBRI.JK",
    "BMRI.JK",
    "TLKM.JK",
    "ASII.JK",
]

async def train_all():
    print("=" * 75)
    print("FINBLIX 15-MINUTE 3-HOUR MULTI-HORIZON ENGINE - BATCH TRAINER")
    print("=" * 75)
    
    db = SessionLocal()
    results = []
    
    try:
        for symbol in SYMBOLS:
            print(f"\n[TRAINING 15M] Processing symbol: {symbol} ...")
            try:
                meta = await ThreeHourPredictionEngine.train_7d_model(db, symbol)
                acc = meta.get("test_accuracy_pct", 0.0)
                train_smp = meta.get("samples_trained", 0)
                test_smp = meta.get("samples_tested", 0)
                dur = meta.get("duration_seconds", 0.0)
                print(f"  -> SUCCESS! Test Acc: {acc}% | Train: {train_smp} | Test: {test_smp} | Time: {dur}s")
                results.append((symbol, "SUCCESS", f"{acc}%", train_smp + test_smp, f"{dur}s"))
            except Exception as e:
                print(f"  -> FAILED: {e}")
                results.append((symbol, "FAILED", "-", 0, str(e)))
    finally:
        db.close()
        
    print("\n" + "=" * 75)
    print("SUMMARY RESULTS (15-MINUTE HIGH-CONVICTION MODELS)")
    print("=" * 75)
    print(f"{'Symbol':<15} {'Status':<10} {'Accuracy':<12} {'Total Bars':<12} {'Duration'}")
    print("-" * 75)
    for sym, stat, acc, bars, dur in results:
        print(f"{sym:<15} {stat:<10} {acc:<12} {bars:<12} {dur}")
    print("=" * 75)

if __name__ == "__main__":
    asyncio.run(train_all())
