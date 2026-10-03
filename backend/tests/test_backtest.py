import pytest
from app.services.backtest_engine import BacktestEngine

def test_backtest_rsi():
    bars = []
    price = 50000.0
    for i in range(120):
        # generate sine-like wave for price
        import math
        price = 50000.0 + (5000.0 * math.sin(i / 5.0))
        bars.append({
            "time": 1700000000 + (i * 86400),
            "open": price,
            "high": price + 200,
            "low": price - 200,
            "close": price,
            "volume": 12000
        })

    res = BacktestEngine.run_backtest(bars, strategy="rsi_reversal", initial_capital=10000.0)
    assert res["initial_capital"] == 10000.0
    assert "total_pnl" in res
    assert "win_rate" in res
    assert "max_drawdown" in res
    assert isinstance(res["trades"], list)
