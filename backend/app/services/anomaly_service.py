from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.models.ohlcv import OHLCVBar
from app.models.news import AlertLog
from app.services.ta_engine import TAEngine

class AnomalyService:
    @classmethod
    def scan_asset_anomalies(cls, db: Session, asset: Asset) -> List[Dict[str, Any]]:
        # Fetch last 30 daily bars
        bars_db = db.query(OHLCVBar).filter(
            OHLCVBar.asset_id == asset.id,
            OHLCVBar.timeframe == "1d"
        ).order_by(OHLCVBar.open_time.desc()).limit(30).all()

        if not bars_db or len(bars_db) < 20:
            return []

        bars = [{
            "time": b.open_time,
            "open": float(b.open_price),
            "high": float(b.high_price),
            "low": float(b.low_price),
            "close": float(b.close_price),
            "volume": float(b.volume)
        } for b in reversed(bars_db)]

        latest = bars[-1]
        vol_slice = [b["volume"] for b in bars[-21:-1]]
        avg_vol = sum(vol_slice) / len(vol_slice) if vol_slice else 1.0

        ta = TAEngine.calculate_indicators(bars)
        anomalies = []

        # 1. Volume Spike Check (> 2.5x SMA vol 20)
        vol_ratio = latest["volume"] / avg_vol if avg_vol > 0 else 1.0
        if vol_ratio >= 2.5:
            severity = "critical" if vol_ratio >= 4.0 else "warning"
            msg = f"Volume Spike terdeteksi pada {asset.symbol}! Volume saat ini ({latest['volume']:,.0f}) mencapai {vol_ratio:.1f}x di atas rata-rata 20 hari ({avg_vol:,.0f})."
            anomalies.append({
                "type": "volume_spike",
                "message": msg,
                "severity": severity
            })

        # 2. Extreme Price Movement (> 6% in 24h)
        chg = abs(ta.get("change_24h_percent", 0.0))
        if chg >= 6.0:
            direction = "lonjakan naik" if (ta.get("change_24h_percent", 0.0) > 0) else "anjlok tajam"
            msg = f"Pergerakan harga ekstrem pada {asset.symbol}: {direction} sebesar {ta['change_24h_percent']}% dalam 24 jam terakhir."
            anomalies.append({
                "type": "price_breakout",
                "message": msg,
                "severity": "critical" if chg >= 10.0 else "warning"
            })

        # 3. Extreme RSI
        rsi = ta.get("rsi_14")
        if rsi is not None:
            if rsi <= 25:
                msg = f"{asset.symbol} berada di zona ekstrem oversold (RSI: {rsi:.1f} <= 25). Potensi technical rebound tinggi."
                anomalies.append({
                    "type": "rsi_oversold",
                    "message": msg,
                    "severity": "info"
                })
            elif rsi >= 78:
                msg = f"{asset.symbol} berada di zona ekstrem overbought (RSI: {rsi:.1f} >= 78). Waspadai aksi ambil untung (profit taking)."
                anomalies.append({
                    "type": "rsi_overbought",
                    "message": msg,
                    "severity": "info"
                })

        # Record to AlertLog in MySQL if not duplicate recently
        for anom in anomalies:
            existing = db.query(AlertLog).filter(
                AlertLog.asset_id == asset.id,
                AlertLog.alert_type == anom["type"],
                AlertLog.is_read == False
            ).first()

            if not existing:
                alert = AlertLog(
                    asset_id=asset.id,
                    alert_type=anom["type"],
                    message=anom["message"],
                    severity=anom["severity"]
                )
                db.add(alert)

        try:
            db.commit()
        except Exception:
            db.rollback()

        return anomalies

    @classmethod
    def scan_all_assets(cls, db: Session) -> List[Dict[str, Any]]:
        assets = db.query(Asset).filter(Asset.is_active == True).all()
        all_found = []
        for a in assets:
            found = cls.scan_asset_anomalies(db, a)
            for f in found:
                all_found.append({
                    "symbol": a.symbol,
                    **f
                })
        return all_found
