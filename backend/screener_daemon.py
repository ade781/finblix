import asyncio
import time
import httpx
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("screener_alerts.log")
    ]
)
logger = logging.getLogger("MarketScreener")

# Top 20 Binance Liquid Coins
WATCHLIST = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT", 
    "ADA/USDT", "AVAX/USDT", "DOGE/USDT", "DOT/USDT", "MATIC/USDT",
    "LINK/USDT", "UNI/USDT", "LTC/USDT", "ATOM/USDT", "ETC/USDT"
]

API_BASE_URL = "http://127.0.0.1:8001/api/v1"
THRESHOLD_CONVICTION = 65.0  # Alert if ML confidence is > 65%

async def scan_coin(client, symbol):
    url = f"{API_BASE_URL}/prediction/daily/{symbol}"
    try:
        resp = await client.get(url, timeout=15.0)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            ml = data.get("ml_model", {})
            if ml.get("is_trained") and ml.get("prediction"):
                pred = ml["prediction"]
                prob = pred.get("probability_up", 0.5) * 100
                direction = pred.get("predicted_direction", "NETRAL")
                
                # Menghitung skor confidence
                confidence = prob if direction == "NAIK" else (100 - prob)
                
                if confidence >= THRESHOLD_CONVICTION:
                    alert_msg = f"🚀 HIGH CONVICTION ALERT 🚀 | {symbol} | Direction: {direction} | Confidence: {confidence:.1f}%"
                    logger.info(alert_msg)
                    # TODO: Tambahkan request ke Telegram Bot API di sini
                    # requests.post(f"https://api.telegram.org/bot<TOKEN>/sendMessage", data={"chat_id": <ID>, "text": alert_msg})
                    return True
    except Exception as e:
        logger.debug(f"Scan failed for {symbol}: {e}")
    return False

async def main():
    logger.info("Starting Market-Wide ML Screener Daemon...")
    while True:
        logger.info(f"--- Scanning {len(WATCHLIST)} coins for High Conviction Signals ---")
        async with httpx.AsyncClient() as client:
            tasks = [scan_coin(client, sym) for sym in WATCHLIST]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            hits = sum(1 for r in results if r is True)
            logger.info(f"Scan Complete. Found {hits} strong signals.")
            
        # Run every 15 minutes (900 seconds)
        logger.info("Sleeping for 15 minutes...")
        await asyncio.sleep(900)

if __name__ == "__main__":
    asyncio.run(main())
