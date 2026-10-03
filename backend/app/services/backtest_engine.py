from datetime import datetime, timezone
from typing import List, Dict, Any
import pandas as pd
import numpy as np

class BacktestEngine:
    @classmethod
    def run_backtest(
        cls, 
        bars: List[Dict[str, Any]], 
        strategy: str = "rsi_reversal", 
        initial_capital: float = 10000.0,
        fee_percent: float = 0.1
    ) -> Dict[str, Any]:
        if not bars or len(bars) < 30:
            return {
                "initial_capital": initial_capital,
                "final_capital": initial_capital,
                "total_pnl": 0.0,
                "total_pnl_percent": 0.0,
                "total_trades": 0,
                "win_trades": 0,
                "loss_trades": 0,
                "win_rate": 0.0,
                "max_drawdown": 0.0,
                "trades": [],
                "equity_curve": []
            }

        df = pd.DataFrame(bars)
        close = df["close"]

        # Compute technical indicators
        # EMAs
        df["ema_20"] = close.ewm(span=20, adjust=False).mean()
        df["ema_50"] = close.ewm(span=50, adjust=False).mean()

        # RSI 14
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss.replace(0, np.nan))
        df["rsi"] = (100 - (100 / (1 + rs))).fillna(50)

        # MACD
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        df["macd_line"] = ema_12 - ema_26
        df["macd_signal"] = df["macd_line"].ewm(span=9, adjust=False).mean()

        cash = initial_capital
        position_units = 0.0
        entry_price = 0.0
        entry_time = None

        trades = []
        equity_curve = []
        peak_equity = initial_capital
        max_drawdown = 0.0

        for i in range(1, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i - 1]
            t = int(row["time"])
            date_str = datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d")
            p = float(row["close"])

            # Check signals based on strategy
            buy_signal = False
            sell_signal = False

            if strategy == "rsi_reversal":
                if row["rsi"] < 35 and prev_row["rsi"] >= 35:
                    buy_signal = True
                elif row["rsi"] > 68 and prev_row["rsi"] <= 68:
                    sell_signal = True

            elif strategy == "ema_cross":
                if row["ema_20"] > row["ema_50"] and prev_row["ema_20"] <= prev_row["ema_50"]:
                    buy_signal = True
                elif row["ema_20"] < row["ema_50"] and prev_row["ema_20"] >= prev_row["ema_50"]:
                    sell_signal = True

            elif strategy == "macd_cross":
                if row["macd_line"] > row["macd_signal"] and prev_row["macd_line"] <= prev_row["macd_signal"]:
                    buy_signal = True
                elif row["macd_line"] < row["macd_signal"] and prev_row["macd_line"] >= prev_row["macd_signal"]:
                    sell_signal = True

            # Execution
            if buy_signal and position_units == 0 and cash > 0:
                fee = cash * (fee_percent / 100.0)
                investable = cash - fee
                position_units = investable / p
                entry_price = p
                entry_time = date_str
                cash = 0.0

            elif sell_signal and position_units > 0:
                gross = position_units * p
                fee = gross * (fee_percent / 100.0)
                cash = gross - fee

                pnl = cash - (position_units * entry_price)
                pnl_pct = ((p - entry_price) / entry_price) * 100.0

                trades.append({
                    "entry_date": entry_time,
                    "exit_date": date_str,
                    "entry_price": round(entry_price, 2),
                    "exit_price": round(p, 2),
                    "pnl": round(pnl, 2),
                    "pnl_percent": round(pnl_pct, 2),
                    "is_win": pnl > 0
                })

                position_units = 0.0
                entry_price = 0.0

            # Current equity evaluation
            current_equity = cash + (position_units * p)
            if current_equity > peak_equity:
                peak_equity = current_equity
            dd = ((peak_equity - current_equity) / peak_equity) * 100.0
            if dd > max_drawdown:
                max_drawdown = dd

            equity_curve.append({
                "date": date_str,
                "equity": round(current_equity, 2)
            })

        # Close position at the end if still open
        if position_units > 0:
            final_p = float(df.iloc[-1]["close"])
            final_d = datetime.fromtimestamp(int(df.iloc[-1]["time"]), tz=timezone.utc).strftime("%Y-%m-%d")
            gross = position_units * final_p
            cash = gross
            pnl_pct = ((final_p - entry_price) / entry_price) * 100.0
            trades.append({
                "entry_date": entry_time,
                "exit_date": final_d,
                "entry_price": round(entry_price, 2),
                "exit_price": round(final_p, 2),
                "pnl": round(gross - (position_units * entry_price), 2),
                "pnl_percent": round(pnl_pct, 2),
                "is_win": final_p > entry_price
            })

        final_capital = cash
        total_pnl = final_capital - initial_capital
        total_pnl_pct = (total_pnl / initial_capital) * 100.0
        win_count = sum(1 for t in trades if t["is_win"])
        win_rate = (win_count / len(trades) * 100.0) if trades else 0.0

        # Downsample equity curve to max 40 points
        step = max(1, len(equity_curve) // 35)
        sampled_curve = equity_curve[::step]
        if equity_curve and (not sampled_curve or sampled_curve[-1] != equity_curve[-1]):
            sampled_curve.append(equity_curve[-1])

        return {
            "initial_capital": round(initial_capital, 2),
            "final_capital": round(final_capital, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_percent": round(total_pnl_pct, 2),
            "total_trades": len(trades),
            "win_trades": win_count,
            "loss_trades": len(trades) - win_count,
            "win_rate": round(win_rate, 2),
            "max_drawdown": round(max_drawdown, 2),
            "trades": trades,
            "equity_curve": sampled_curve
        }
