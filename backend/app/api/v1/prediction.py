from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.services.prediction_engine import DailyPredictionEngine
from app.services.ml_training_engine import MLTrainingEngine
from app.services.three_hour_engine import ThreeHourPredictionEngine
from app.services.scraper_service import ScraperService

router = APIRouter()

@router.get("/daily/{symbol:path}")
async def get_daily_prediction(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Mengembalikan prediksi arah harian (NAIK / TURUN) di akhir hari untuk hari esok
    berdasarkan perpaduan Analisis Teknikal dan Fundamental Berita & Fear/Greed.
    Juga menyertakan rekam jejak akurasi historis harian (30 hari terakhir) serta status ML model.
    """
    try:
        result = await DailyPredictionEngine.predict_daily_direction(db, symbol)
        
        # Cek apakah sudah ada model Machine Learning yang terlatih
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

@router.get("/three-hours/{symbol:path}")
async def get_three_hour_prediction(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Mengembalikan prediksi lintasan granular per 15 MENIT selama 3 JAM KE DEPAN (12 interval proyeksi):
    - Pelatihan data lilin native 15-menit (500-1000 bar) dengan GBDT & Random Forest
    - 12 Titik milestone: +15m, +30m, +45m, +60m, ..., +180m (harga, probabilitas, batas volatilitas, katalis)
    - Proyeksi titik puncak (Peak), titik terendah (Dip), dan strategi taktis
    - Scraping berita harian massal aktual dan analisis sentimen
    - Evaluasi backtest walk-forward 15-menit 7 hari terakhir
    """
    try:
        result = await ThreeHourPredictionEngine.predict_3h_outlook(db, symbol)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return {
            "status": "success",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal melakukan prediksi 3 jam: {str(e)}")

@router.post("/train-three-hours/{symbol:path}")
async def train_three_hour_model(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Melatih model Machine Learning Intraday berbasis data 15-menit (Multi-Horizon 12-Interval)
    khusus untuk memprediksi lintasan tiap 15 menit selama 3 jam ke depan.
    """
    try:
        report = await ThreeHourPredictionEngine.train_7d_model(db, symbol)
        return {
            "status": "success",
            "message": f"Model Intraday 7-Hari untuk prediksi 3 jam ({symbol}) berhasil dilatih!",
            "data": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal melatih model 3 jam: {str(e)}")

@router.post("/scrape-daily-news")
async def trigger_bulk_daily_news_scraping(
    limit_per_feed: int = Query(35, description="Jumlah artikel per RSS feed"),
    db: Session = Depends(get_db)
):
    """
    Memicu scraping massal berita finansial harian dari berbagai feed berita pasar modal & kripto.
    Mengumpulkan puluhan artikel berita harian aktual untuk memperkaya sentimen prediksi 3 jam dan harian.
    """
    try:
        summary = await ScraperService.scrape_bulk_daily_news(db, limit_per_feed=limit_per_feed)
        return {
            "status": "success",
            "message": "Scraping massal berita finansial harian berhasil diselesaikan!",
            "data": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal melakukan scraping berita harian: {str(e)}")

@router.post("/train/{symbol:path}")
async def train_ml_model(
    symbol: str,
    n_estimators_rf: int = Query(300, description="Jumlah pohon Random Forest"),
    n_estimators_gb: int = Query(250, description="Jumlah stage Gradient Boosting"),
    db: Session = Depends(get_db)
):
    """
    Melatih model Machine Learning (Ensemble) menggunakan data historis multi-tahun
    dan data sentimen berita / Fear & Greed terakhir.
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
            "message": f"Model AI untuk {symbol} berhasil dilatih dan disimpan!",
            "data": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal melatih model: {str(e)}")

@router.get("/model-status/{symbol:path}")
async def get_model_status(symbol: str):
    """
    Mendapatkan status, metrik akurasi, dan feature importance dari model AI yang telah dilatih.
    """
    status = MLTrainingEngine.get_trained_model_status(symbol)
    if not status:
        return {
            "status": "success",
            "data": {
                "symbol": symbol,
                "is_trained": False,
                "message": "Model belum dilatih untuk aset ini. Silakan jalankan training."
            }
        }
    return {
        "status": "success",
        "data": {
            "is_trained": True,
            **status
        }
    }
