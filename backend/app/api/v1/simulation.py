from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.asset import Asset
from app.schemas.simulation_schema import (
    WhatIfRequest, WhatIfResponse,
    RiskCalculatorRequest, RiskCalculatorResponse
)
from app.services.crypto_service import CryptoService
from app.services.stock_service import StockService
from app.services.simulator_engine import SimulatorEngine

router = APIRouter()

@router.post("/what-if", response_model=WhatIfResponse)
async def simulate_what_if(
    payload: WhatIfRequest,
    db: Session = Depends(get_db)
):
    symbol = payload.symbol
    asset = db.query(Asset).filter((Asset.symbol == symbol) | (Asset.symbol == symbol.replace("-", "/"))).first()
    
    # Fetch historical bars (use 1d bars for long-term simulation)
    if asset and asset.asset_type == "crypto":
        bars = await CryptoService.fetch_binance_bars(asset.symbol, timeframe="1d", limit=365)
    elif asset:
        bars = StockService.fetch_stock_bars(asset.symbol, timeframe="1d", limit=365)
    else:
        # Generic fallback
        bars = CryptoService._generate_fallback_bars(symbol, count=200)

    result = SimulatorEngine.calculate_what_if(
        bars=bars,
        strategy=payload.strategy,
        amount_per_period=payload.amount_per_period,
        period=payload.period
    )

    return WhatIfResponse(
        symbol=symbol,
        strategy=payload.strategy,
        total_invested=result["total_invested"],
        current_portfolio_value=result["current_portfolio_value"],
        total_profit_loss=result["total_profit_loss"],
        roi_percent=result["roi_percent"],
        total_units_bought=result["total_units_bought"],
        average_buy_price=result["average_buy_price"],
        current_price=result["current_price"],
        history_curve=result["history_curve"]
    )

@router.post("/risk-calculator", response_model=RiskCalculatorResponse)
async def calculate_risk_position(
    payload: RiskCalculatorRequest
):
    result = SimulatorEngine.calculate_risk(
        total_capital=payload.total_capital,
        risk_percent=payload.risk_percent,
        entry_price=payload.entry_price,
        stop_loss_price=payload.stop_loss_price,
        take_profit_price=payload.take_profit_price
    )
    return RiskCalculatorResponse(**result)
