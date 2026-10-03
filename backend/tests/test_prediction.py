import pytest
import math
import asyncio
from app.services.prediction_engine import DailyPredictionEngine

def test_historical_daily_predictions_backtest():
    bars = []
    base_price = 60000.0
    for i in range(70):
        p = base_price + (4000.0 * math.sin(i / 6.0))
        bars.append({
            "time": 1700000000 + (i * 86400),
            "open": p - 100.0,
            "high": p + 300.0,
            "low": p - 300.0,
            "close": p,
            "volume": 25000.0
        })

    res = DailyPredictionEngine._backtest_historical_daily_predictions(bars, days=30)
    assert res["total_days"] > 0
    assert "accuracy_pct" in res
    assert "correct_count" in res
    assert "incorrect_count" in res
    assert isinstance(res["daily_log"], list)
    assert len(res["daily_log"]) == res["total_days"]
    assert res["daily_log"][0]["predicted"] in ["NAIK", "TURUN"]


def test_ml_trained_model_status():
    from app.services.ml_training_engine import MLTrainingEngine
    status = MLTrainingEngine.get_trained_model_status('BTC/USDT')
    assert status is not None
    assert 'metrics' in status
    assert status['metrics']['test_accuracy_pct'] > 50.0
    assert len(status['top_features']) > 0


def test_three_hour_engine_dataset_and_prediction():
    from app.core.database import SessionLocal
    from app.models.asset import Asset
    from app.services.three_hour_engine import ThreeHourEngine

    db = SessionLocal()
    try:
        asset = db.query(Asset).filter(Asset.symbol == 'BTC/USDT').first()
        if not asset:
            asset = Asset(symbol='BTC/USDT', name='Bitcoin', asset_type='crypto', is_active=True)
            db.add(asset)
            db.commit()

        bars = asyncio.run(ThreeHourEngine.fetch_7d_hourly_bars(db, asset))
        assert len(bars) >= 40

        df, feature_cols = ThreeHourEngine.build_intraday_feature_dataset(bars, daily_sentiment=0.15)
        assert not df.empty
        assert 'target_3h' in df.columns
        assert 'rsi_1h' in df.columns
        assert 'ema9_slope' in df.columns
        assert 'cmf_12h' in df.columns
        assert 'volume_surge' in df.columns
        assert len(feature_cols) >= 15

        res = asyncio.run(ThreeHourEngine.predict_3h_outlook(db, 'BTC/USDT'))
        assert res['symbol'] == 'BTC/USDT'
        assert res['prediction_3h']['direction'] in ['NAIK', 'TURUN']
        assert 0 <= res['prediction_3h']['probability_percent'] <= 100
        assert res['target_price']['projected_target_price'] > 0
        assert res['backtest_7d_accuracy']['evaluated_bars'] > 0
    finally:
        db.close()
