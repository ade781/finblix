from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

class TAEngine:
    @staticmethod
    def calculate_indicators(bars: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not bars or len(bars) < 20:
            return {
                "rsi_14": None,
                "rsi_status": "neutral",
                "macd_line": None,
                "macd_signal": None,
                "macd_hist": None,
                "ema_20": None,
                "ema_50": None,
                "ema_200": None,
                "bollinger_upper": None,
                "bollinger_middle": None,
                "bollinger_lower": None,
                "overall_signal": "neutral",
                "change_24h_percent": 0.0,
                "last_price": bars[-1]["close"] if bars else 0.0
            }

        df = pd.DataFrame(bars)
        close = df["close"]

        # 1. EMAs
        ema_20_series = close.ewm(span=20, adjust=False).mean()
        ema_50_series = close.ewm(span=50, adjust=False).mean() if len(close) >= 50 else ema_20_series
        ema_200_series = close.ewm(span=200, adjust=False).mean() if len(close) >= 200 else ema_50_series

        ema_20 = float(ema_20_series.iloc[-1])
        ema_50 = float(ema_50_series.iloc[-1])
        ema_200 = float(ema_200_series.iloc[-1])

        # 2. RSI 14
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss.replace(0, np.nan))
        rsi_series = 100 - (100 / (1 + rs))
        rsi_val = rsi_series.iloc[-1]
        rsi_14 = float(round(rsi_val, 2)) if not np.isnan(rsi_val) else 50.0

        if rsi_14 < 30:
            rsi_status = "oversold"
        elif rsi_14 > 70:
            rsi_status = "overbought"
        else:
            rsi_status = "neutral"

        # 3. MACD (12, 26, 9)
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd_line_series = ema_12 - ema_26
        macd_signal_series = macd_line_series.ewm(span=9, adjust=False).mean()
        macd_hist_series = macd_line_series - macd_signal_series

        macd_line = float(round(macd_line_series.iloc[-1], 4))
        macd_signal = float(round(macd_signal_series.iloc[-1], 4))
        macd_hist = float(round(macd_hist_series.iloc[-1], 4))

        # 4. Bollinger Bands (20, 2)
        sma_20 = close.rolling(window=20).mean()
        std_20 = close.rolling(window=20).std()
        upper_bb = sma_20 + (2 * std_20)
        lower_bb = sma_20 - (2 * std_20)

        bb_middle = float(round(sma_20.iloc[-1], 2))
        bb_upper = float(round(upper_bb.iloc[-1], 2))
        bb_lower = float(round(lower_bb.iloc[-1], 2))

        # 5. Last Price & 24h Change
        last_price = float(close.iloc[-1])
        prev_price = float(close.iloc[-2]) if len(close) > 1 else last_price
        change_24h = round(((last_price - prev_price) / prev_price) * 100, 2) if prev_price > 0 else 0.0

        # 6. Overall Signal Scoring
        score = 0
        if ema_20 > ema_50:
            score += 1
        else:
            score -= 1

        if last_price > ema_200:
            score += 2
        else:
            score -= 2

        if rsi_status == "oversold":
            score += 2  # Oversold bounce potential
        elif rsi_status == "overbought":
            score -= 2  # Overbought pullback risk
        elif 45 <= rsi_14 <= 60:
            score += 1

        if macd_hist > 0:
            score += 1
        else:
            score -= 1

        if score >= 4:
            overall_signal = "strong_buy"
        elif score >= 2:
            overall_signal = "buy"
        elif score <= -4:
            overall_signal = "strong_sell"
        elif score <= -2:
            overall_signal = "sell"
        else:
            overall_signal = "neutral"

        return {
            "rsi_14": rsi_14,
            "rsi_status": rsi_status,
            "macd_line": macd_line,
            "macd_signal": macd_signal,
            "macd_hist": macd_hist,
            "ema_20": round(ema_20, 2),
            "ema_50": round(ema_50, 2),
            "ema_200": round(ema_200, 2),
            "bollinger_upper": bb_upper,
            "bollinger_middle": bb_middle,
            "bollinger_lower": bb_lower,
            "overall_signal": overall_signal,
            "change_24h_percent": change_24h,
            "last_price": round(last_price, 2)
        }
