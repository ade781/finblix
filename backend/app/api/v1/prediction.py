from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.services.prediction_engine import DailyPredictionEngine
from app.services.ml_training_engine import MLTrainingEngine

router = APIRouter()

@router.get("/daily/{symbol:path}")
async def get_daily_prediction(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Mengembalikan prediksi arah harian (NAIK / TURUN) di akhir hari untuk hari esok
    berdasarkan perpaduan 60% Analisis Teknikal dan 40% Fundamental Berita & Fear/Greed.
    Juga menyertakan rekam jejak akurasi historis harian (30 hari terakhir) serta status ML model 1 tahun.
    """
    try:
        result = await DailyPredictionEngine.predict_daily_direction(db, symbol)
        
        # Cek apakah sudah ada model Machine Learning 1 tahun yang terlatih
        ml_prediction = await MLTrainingEngine.predict_with_ml_model(db, symbol)
        ml_status = MLTrainingEngine.get_trained_model_status(symbol)
        
        if result and "prediction" in result:
            result["ml_model"] = {
                "is_trained": ml_status is not None,
                "status": ml_status.get("status", "NOT_TRAINED") if ml_status else "NOT_TRAINED",
                "trained_at": ml_status.get("trained_at") if ml_status else None,
                "test_accuracy_pct": ml_status.get("metrics", {}).get("test_accuracy_pct") if ml_status else None,
                "prediction": ml_prediction
            }

        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal melakukan prediksi harian: {str(e)}")

@router.post("/train/{symbol:path}")
async def train_ml_model(
    symbol: str,
    n_estimators_rf: int = Query(300, description="Jumlah pohon Random Forest"),
    n_estimators_gb: int = Query(250, description="Jumlah stage Gradient Boosting"),
    db: Session = Depends(get_db)
):
    """
    Melatih model Machine Learning (Ensemble RF 300 + GB 250) menggunakan data historis 1 tahun
    dan data sentimen berita / Fear & Greed 1 tahun terakhir.
    Membutuhkan komputasi intensif dan waktu kalkulasi nyata.
    """
    try:
        report = await MLTrainingEngine.train_model_for_asset(
            db=db,
            symbol=symbol,
            n_estimators_rf=n_estimators_rf,
            n_estimators_gb=n_estimators_gb
        )
        return {
            "status": "success",
            "message": f"Model AI 1 Tahun untuk {symbol} berhasil dilatih dan disimpan!",
            "data": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal melatih model: {str(e)}")

@router.get("/model-status/{symbol:path}")
async def get_model_status(symbol: str):
    """
    Mendapatkan status, metrik akurasi, dan feature importance dari model AI 1 tahun yang telah dilatih.
    """
    status = MLTrainingEngine.get_trained_model_status(symbol)
    if not status:
        return {
            "status": "success",
            "data": {
                "symbol": symbol,
                "is_trained": False,
                "message": "Model belum dilatih untuk aset ini. Silakan jalankan training 1 tahun."
            }
        }
    return {
        "status": "success",
        "data": {
            "is_trained": True,
            **status
        }
    }
