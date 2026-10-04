from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.deps import get_db
import httpx
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class WebhookConfig(BaseModel):
    symbol: str
    target_url: str  # URL Telegram Bot atau API Broker (Binance/Bybit)
    min_probability: float = 0.65  # Hanya eksekusi jika probability >= 65%
    secret_token: str = "FINBLIX_SECRET_XYZ" # Security token

async def fire_webhook(url: str, payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, timeout=10.0)
            logger.info(f"Webhook fired to {url}")
    except Exception as e:
        logger.error(f"Failed to fire webhook to {url}: {e}")

@router.post("/execute-signal")
async def execute_trade_signal(
    config: WebhookConfig,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Endpoint Webhook Trading Bot. 
    Mengeksekusi prediksi High-Conviction Finblix dan meneruskannya ke Bot Eksternal.
    """
    if config.secret_token != "FINBLIX_SECRET_XYZ":
        raise HTTPException(status_code=401, detail="Invalid Security Token")

    # Di sini, kita simulasikan penarikan ML Prediction. 
    # Idealnya akan memanggil MLTrainingEngine
    from app.services.ml_training_engine import MLTrainingEngine
    ml_prediction = await MLTrainingEngine.predict_with_ml_model(db, config.symbol)
    
    if not ml_prediction or ml_prediction.get("predicted_direction") == "NETRAL":
        return {"status": "skipped", "reason": "No strong signal currently"}

    prob = ml_prediction.get("probability_up", 0.5)
    direction = ml_prediction.get("predicted_direction")
    
    # Validasi Threshold Conviction (contoh: 65%)
    if (direction == "NAIK" and prob >= config.min_probability) or \
       (direction == "TURUN" and (1 - prob) >= config.min_probability):
        
        trade_payload = {
            "symbol": config.symbol,
            "action": "BUY" if direction == "NAIK" else "SELL",
            "confidence_score": prob if direction == "NAIK" else (1 - prob),
            "source": "Finblix ML Quant Engine",
            "recommended_leverage": "2x" if prob < 0.7 else "5x" # Dynamic risk allocation
        }
        
        # Kirim HTTP POST ke Bot Broker (Binance / Telegram) di latar belakang
        background_tasks.add_task(fire_webhook, config.target_url, trade_payload)
        
        return {
            "status": "executed",
            "trade_signal": trade_payload,
            "message": "Signal queued for background webhook execution"
        }
    
    return {
        "status": "skipped", 
        "reason": f"Signal probability {prob} did not meet threshold {config.min_probability}"
    }
