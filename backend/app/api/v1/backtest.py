from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.asset import Asset
from app.services.crypto_service import CryptoService
from app.services.stock_service import StockService
from app.services.backtest_engine import BacktestEngine

router = APIRouter()

class BacktestRequest(BaseModel):
    symbol: str = "BTC/USDT"
    strategy: str = "rsi_reversal"  # rsi_reversal, ema_cross, macd_cross
    initial_capital: float = 10000.0
    fee_percent: float = 0.1

@router.post("/run")
async def run_backtest(
    payload: BacktestRequest,
    db: Session = Depends(get_db)
):
    symbol = payload.symbol
    asset = db.query(Asset).filter((Asset.symbol == symbol) | (Asset.symbol == symbol.replace("-", "/"))).first()

    if asset and asset.asset_type == "crypto":
        bars = await CryptoService.fetch_binance_bars(asset.symbol, timeframe="1d", limit=300)
    elif asset:
        bars = StockService.fetch_stock_bars(asset.symbol, timeframe="1d", limit=300)
    else:
        bars = await CryptoService.fetch_binance_bars(symbol, timeframe="1d", limit=300)

    if not bars:
        raise HTTPException(status_code=404, detail=f"Data pasar historis tidak tersedia untuk {symbol}")

    result = BacktestEngine.run_backtest(
        bars=bars,
        strategy=payload.strategy,
        initial_capital=payload.initial_capital,
        fee_percent=payload.fee_percent
    )

    return {
        "status": "success",
        "symbol": symbol,
        "strategy": payload.strategy,
        "data": result
    }
