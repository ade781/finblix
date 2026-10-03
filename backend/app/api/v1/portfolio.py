from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.asset import Asset
from app.models.ohlcv import OHLCVBar
from app.services.portfolio_service import PortfolioService
from app.services.crypto_service import CryptoService
from app.services.stock_service import StockService

router = APIRouter()

class BuyTradeRequest(BaseModel):
    symbol: str
    amount: float

class CloseTradeRequest(BaseModel):
    trade_id: int

async def get_current_price_for_asset(db: Session, symbol: str) -> float:
    asset = db.query(Asset).filter((Asset.symbol == symbol) | (Asset.symbol == symbol.replace("-", "/"))).first()
    if asset:
        if asset.asset_type == "crypto":
            bars = await CryptoService.fetch_binance_bars(asset.symbol, timeframe="1d", limit=2)
            if bars:
                return float(bars[-1]["close"])
        else:
            bars = StockService.fetch_stock_bars(asset.symbol, timeframe="1d", limit=2)
            if bars:
                return float(bars[-1]["close"])
    return 100.0

@router.get("/summary")
async def get_portfolio_summary(db: Session = Depends(get_db)):
    # Build a quick live price map for open trades
    port = PortfolioService.get_or_create_portfolio(db)
    prices_map = {}
    
    # Pre-fetch prices for open positions
    for t in port.trades:
        if t.status == "open":
            asset = db.query(Asset).filter(Asset.id == t.asset_id).first()
            if asset and asset.symbol not in prices_map:
                prices_map[asset.symbol] = await get_current_price_for_asset(db, asset.symbol)

    summary = PortfolioService.get_portfolio_summary(db, "default_trader", prices_map)
    return {"status": "success", "data": summary}

@router.post("/buy")
async def buy_asset(payload: BuyTradeRequest, db: Session = Depends(get_db)):
    try:
        cur_price = await get_current_price_for_asset(db, payload.symbol)
        result = PortfolioService.execute_trade(
            db=db,
            user_name="default_trader",
            symbol=payload.symbol,
            trade_type="buy",
            amount=payload.amount,
            current_price=cur_price
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/close/{trade_id}")
async def close_trade(trade_id: int, db: Session = Depends(get_db)):
    try:
        # Get asset symbol of trade
        from app.models.simulation import VirtualTrade
        t = db.query(VirtualTrade).filter(VirtualTrade.id == trade_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Trade not found")
        asset = db.query(Asset).filter(Asset.id == t.asset_id).first()
        cur_price = await get_current_price_for_asset(db, asset.symbol if asset else "BTC/USDT")
        
        result = PortfolioService.close_position(db, trade_id, cur_price)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reset")
def reset_portfolio(db: Session = Depends(get_db)):
    result = PortfolioService.reset_portfolio(db, "default_trader")
    return result
