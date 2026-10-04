from fastapi import APIRouter
from app.api.v1.market import router as market_router
from app.api.v1.screener import router as screener_router
from app.api.v1.indicators import router as indicators_router
from app.api.v1.simulation import router as simulation_router
from app.api.v1.news import router as news_router
from app.api.v1.watchlist import router as watchlist_router
from app.api.v1.backtest import router as backtest_router
from app.api.v1.portfolio import router as portfolio_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.prediction import router as prediction_router
from app.api.v1.trade_bot import router as trade_bot_router

api_router = APIRouter()
api_router.include_router(market_router, prefix="/market", tags=["Market Data"])
api_router.include_router(screener_router, prefix="/screener", tags=["Market Screener"])
api_router.include_router(indicators_router, prefix="/indicators", tags=["Technical Indicators"])
api_router.include_router(simulation_router, prefix="/simulation", tags=["Simulation & Risk"])
api_router.include_router(news_router, prefix="/news", tags=["News & Sentiment"])
api_router.include_router(watchlist_router, prefix="/watchlist", tags=["Watchlist"])
api_router.include_router(backtest_router, prefix="/backtest", tags=["Strategy Backtester"])
api_router.include_router(portfolio_router, prefix="/portfolio", tags=["Paper Trading Portfolio"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["Anomaly & Alerts"])
api_router.include_router(prediction_router, prefix="/prediction", tags=["Daily Direction Prediction & Accuracy"])
api_router.include_router(trade_bot_router, prefix="/trade", tags=["Webhook Trade Executor Bot"])
