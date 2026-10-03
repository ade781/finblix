import pytest
from app.services.simulator_engine import SimulatorEngine

def test_dca_simulation():
    bars = []
    price = 1000.0
    for i in range(100):
        price += 10.0
        bars.append({
            "time": 1700000000 + (i * 86400),
            "open": price,
            "high": price + 5,
            "low": price - 5,
            "close": price,
            "volume": 5000
        })

    res = SimulatorEngine.calculate_what_if(bars, "dca", 100.0, "monthly")
    assert res["total_invested"] > 0
    assert res["current_portfolio_value"] > res["total_invested"]
    assert res["roi_percent"] > 0
    assert len(res["history_curve"]) > 0

def test_risk_calculator():
    res = SimulatorEngine.calculate_risk(
        total_capital=10000.0,
        risk_percent=1.0,
        entry_price=100.0,
        stop_loss_price=95.0,
        take_profit_price=115.0
    )
    assert res["max_dollar_risk"] == 100.0
    assert res["risk_per_unit"] == 5.0
    assert res["recommended_position_size"] == 20.0
    assert res["total_position_cost"] == 2000.0
    assert res["potential_profit"] == 300.0
    assert "1 : 3.00" in res["risk_to_reward_ratio"]
