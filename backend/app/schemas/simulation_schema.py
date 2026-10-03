from pydantic import BaseModel
from typing import List, Optional

class CurvePoint(BaseModel):
    date: str
    invested: float
    portfolio_value: float

class WhatIfRequest(BaseModel):
    symbol: str = "BTC/USDT"
    strategy: str = "dca"  # dca or lump_sum
    amount_per_period: float = 100.0
    period: str = "monthly"  # monthly, weekly, biweekly
    start_date: str = "2023-01-01"
    end_date: Optional[str] = None

class WhatIfResponse(BaseModel):
    symbol: str
    strategy: str
    total_invested: float
    current_portfolio_value: float
    total_profit_loss: float
    roi_percent: float
    total_units_bought: float
    average_buy_price: float
    current_price: float
    history_curve: List[CurvePoint]

class RiskCalculatorRequest(BaseModel):
    total_capital: float = 10000.0
    risk_percent: float = 1.0
    entry_price: float = 70000.0
    stop_loss_price: float = 68000.0
    take_profit_price: float = 75000.0

class RiskCalculatorResponse(BaseModel):
    max_dollar_risk: float
    risk_per_unit: float
    recommended_position_size: float
    total_position_cost: float
    potential_profit: float
    risk_to_reward_ratio: str
    recommendation: str
