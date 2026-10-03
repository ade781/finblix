import pytest
from app.services.ta_engine import TAEngine

def test_ta_engine_indicators_calculation():
    # 30 daily bars mock data
    bars = []
    price = 100.0
    for i in range(50):
        price = price * (1.01 if i % 2 == 0 else 0.99)
        bars.append({
            "time": 1700000000 + (i * 86400),
            "open": price,
            "high": price * 1.02,
            "low": price * 0.98,
            "close": price,
            "volume": 10000 + (i * 100)
        })

    ta = TAEngine.calculate_indicators(bars)

    assert ta["rsi_14"] is not None
    assert 0 <= ta["rsi_14"] <= 100
    assert ta["rsi_status"] in ["oversold", "neutral", "overbought"]
    assert ta["ema_20"] is not None
    assert ta["ema_50"] is not None
    assert ta["macd_line"] is not None
    assert ta["macd_signal"] is not None
    assert ta["bollinger_upper"] > ta["bollinger_lower"]
    assert ta["overall_signal"] in ["strong_buy", "buy", "neutral", "sell", "strong_sell"]
