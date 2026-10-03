from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.news import AlertLog
from app.models.asset import Asset
from app.services.anomaly_service import AnomalyService
from app.services.webhook_service import WebhookService

router = APIRouter()

class WebhookTestRequest(BaseModel):
    channel: str = "discord"  # 'discord' or 'telegram'
    webhook_url: Optional[str] = None
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    message: Optional[str] = "Peringatan Anomali Finblix Terdeteksi! BTC/USDT mengalami lonjakan volume."

@router.get("/")
def get_alerts(unread_only: bool = False, db: Session = Depends(get_db)):
    query = db.query(AlertLog)
    if unread_only:
        query = query.filter(AlertLog.is_read == False)
    alerts = query.order_by(AlertLog.triggered_at.desc()).limit(20).all()

    results = []
    for a in alerts:
        asset = db.query(Asset).filter(Asset.id == a.asset_id).first()
        results.append({
            "id": a.id,
            "asset_id": a.asset_id,
            "symbol": asset.symbol if asset else "UNKNOWN",
            "alert_type": a.alert_type,
            "message": a.message,
            "severity": a.severity,
            "triggered_at": a.triggered_at.strftime("%Y-%m-%d %H:%M") if a.triggered_at else "",
            "is_read": a.is_read
        })
    return {"status": "success", "count": len(results), "data": results}

@router.post("/scan")
def scan_anomalies(db: Session = Depends(get_db)):
    anomalies = AnomalyService.scan_all_assets(db)
    return {"status": "success", "found_count": len(anomalies), "anomalies": anomalies}

@router.post("/mark-read/{alert_id}")
def mark_alert_read(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(AlertLog).filter(AlertLog.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    return {"status": "success", "message": "Alert marked as read"}

@router.post("/webhook-test")
async def test_webhook(payload: WebhookTestRequest):
    if payload.channel == "discord":
        res = await WebhookService.send_discord_alert(payload.webhook_url, payload.message)
    elif payload.channel == "telegram":
        res = await WebhookService.send_telegram_alert(payload.bot_token, payload.chat_id, payload.message)
    else:
        raise HTTPException(status_code=400, detail="Channel must be discord or telegram")
    return res
