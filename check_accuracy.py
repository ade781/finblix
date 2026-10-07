import os
import sys
import glob
import json
import asyncio

sys.path.insert(0, os.path.abspath('backend'))

from app.core.database import SessionLocal
from app.services.prediction_engine import DailyPredictionEngine
from app.services.three_hour_engine import ThreeHourPredictionEngine
from app.services.ml_training_engine import MLTrainingEngine

def check_stored_ml_models():
    print("=" * 95)
    print("1. EVALUASI MODEL MACHINE LEARNING TERLATIH (STORAGE METRICS)")
    print("=" * 95)
    files = sorted(glob.glob('backend/app/models_storage/*_meta.json'))
    daily_models = []
    intraday_models = []

    for f in files:
        name = os.path.basename(f)
        with open(f, 'r') as fp:
            data = json.load(fp)
        if '3h' in name or '15m' in name:
            intraday_models.append((name, data))
        else:
            daily_models.append((name, data))

    print("\n[A] Model Prediksi Harian (Daily Ensemble - Random Forest & Gradient Boosting):")
    print(f"{'Simbol / Model':<22} | {'Test Acc':<10} | {'Train Acc':<10} | {'F1-Score':<10} | {'ROC-AUC':<10}")
    print("-" * 72)
    for name, data in daily_models:
        sym = data.get("symbol", name.replace("_meta.json", ""))
        m = data.get("metrics", {})
        test_acc = f"{m.get('test_accuracy_pct', 'N/A')}%"
        train_acc = f"{m.get('train_accuracy_pct', 'N/A')}%"
        f1 = f"{m.get('f1_score', 'N/A')}"
        auc = f"{m.get('roc_auc', 'N/A')}"
        print(f"{sym:<22} | {test_acc:<10} | {train_acc:<10} | {f1:<10} | {auc:<10}")

    print("\n[B] Model Prediksi Intraday Multi-Horizon (15-Minute / 3-Hour):")
    print(f"{'Simbol / Model':<25} | {'Test Acc':<10} | {'CV Acc (TS-Split)':<18} | {'Sampel Training':<16}")
    print("-" * 76)
    for name, data in intraday_models:
        sym = data.get("symbol", name.replace("_meta.json", ""))
        test_acc = f"{data.get('test_accuracy_pct', 'N/A')}%"
        cv_acc = f"{data.get('cv_accuracy_pct', 'N/A')}%"
        samples = f"{data.get('samples_trained', 'N/A')} bar"
        print(f"{sym:<25} | {test_acc:<10} | {cv_acc:<18} | {samples:<16}")

async def evaluate_live_predictions():
    db = SessionLocal()
    assets_to_test = ['BTC/USDT']
    
    print("\n" + "=" * 95)
    print("2. AUDIT PREDIKSI HARIAN (DAILY ENGINE 30 HARI - ALL DAYS VS HIGH-CONVICTION)")
    print("=" * 95)
    print(f"{'Simbol':<12} | {'Akurasi Total':<15} | {'High-Conviction Acc':<22} | {'Hari Sinyal Kuat':<18} | {'Prediksi Esok':<15}")
    print("-" * 90)

    for sym in assets_to_test:
        try:
            res = await DailyPredictionEngine.predict_daily_direction(db, sym)
            track = res.get("accuracy_track_record", {})
            total_acc = f"{track.get('accuracy_percentage', 0.0)}% ({track.get('correct_predictions', 0)}/{track.get('days_evaluated', 0)})"
            
            hc = track.get("high_conviction", {})
            hc_acc = f"{hc.get('accuracy_percentage', 0.0)}%"
            hc_eval = f"{hc.get('correct_predictions', 0)}/{hc.get('days_evaluated', 0)} hari"
            
            pred = res.get("prediction", {})
            pred_dir = f"{pred.get('direction', 'N/A')} ({pred.get('confidence_percent', 0)}%)"
            
            print(f"{sym:<12} | {total_acc:<15} | {hc_acc:<22} | {hc_eval:<18} | {pred_dir:<15}")
        except Exception as e:
            print(f"{sym:<12} | ERROR: {str(e)}")

    print("\n" + "=" * 95)
    print("3. AUDIT LINTASAN 3 JAM TIAP 15 MENIT (12 INTERVAL PROYEKSI & AKURASI 7 HARI)")
    print("=" * 95)
    print(f"{'Simbol':<12} | {'Arah 3H':<10} | {'Target Puncak (Peak)':<24} | {'Target Terendah (Dip)':<24} | {'Akurasi Walk-Forward 15M':<25}")
    print("-" * 105)

    for sym in assets_to_test:
        try:
            res = await ThreeHourPredictionEngine.predict_3h_outlook(db, sym)
            p3h = res.get("prediction_3h", {})
            tsum = res.get("trajectory_summary", {})
            btest = res.get("backtest_7d_accuracy", {})
            
            dir_str = f"{p3h.get('direction', 'N/A')} ({p3h.get('probability_percent', 0)}%)"
            
            peak = tsum.get("peak_target", {})
            peak_str = f"{peak.get('price', 0):,.2f} ({peak.get('interval_label', '')} {peak.get('change_percent', 0):+}%)"
            
            dip = tsum.get("dip_target", {})
            dip_str = f"{dip.get('price', 0):,.2f} ({dip.get('interval_label', '')} {dip.get('change_percent', 0):+}%)"
            
            b_acc = f"{btest.get('accuracy_percent', 0)}% (HC: {btest.get('high_conviction_accuracy_percent', 0)}%)"
            
            print(f"{sym:<12} | {dir_str:<10} | {peak_str:<24} | {dip_str:<24} | {b_acc:<25}")
            
            # Print sample steps for the first asset
            if sym == 'BTC/USDT':
                print("\n   [Rincian 12 Interval Proyeksi per 15 Menit untuk BTC/USDT]:")
                print(f"   {'Step':<6} | {'Waktu':<10} | {'Target Harga':<14} | {'Delta %':<8} | {'Arah':<10} | {'Prob':<6} | {'Rentang Volatilitas':<22} | {'Katalis':<30}")
                print("   " + "-" * 115)
                for item in res.get("intervals_15m", [])[:6]:  # First 6 steps
                    print(f"   {item['interval_label']:<6} | {item['time_label']} WIB | {item['projected_price']:<14,.2f} | {item['change_percent']:<+7.2f}% | {item['direction']:<10} | {item['probability_percent']:<5.1f}% | {item['lower_band']:,.1f} - {item['upper_band']:,.1f} | {item['catalyst'][:30]}")
                print(f"   ... ({len(res.get('intervals_15m', [])) - 6} interval langkah berikutnya hingga +180m / 3 Jam)")
                print(f"   Tactical Plan: {tsum.get('tactical_recommendation')}\n")
        except Exception as e:
            print(f"{sym:<12} | ERROR: {str(e)}")
            
    db.close()

if __name__ == '__main__':
    check_stored_ml_models()
    asyncio.run(evaluate_live_predictions())
