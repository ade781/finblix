import pytest
import math
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
