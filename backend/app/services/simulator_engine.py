from datetime import datetime, timezone
from typing import List, Dict, Any

class SimulatorEngine:
    @staticmethod
    def calculate_what_if(bars: List[Dict[str, Any]], strategy: str, amount_per_period: float, period: str = "monthly") -> Dict[str, Any]:
        if not bars:
            return {
                "total_invested": 0.0,
                "current_portfolio_value": 0.0,
                "total_profit_loss": 0.0,
                "roi_percent": 0.0,
                "total_units_bought": 0.0,
                "average_buy_price": 0.0,
                "current_price": 0.0,
                "history_curve": []
            }

        current_price = bars[-1]["close"]

        # Interval step
        # Default daily bars; monthly DCA is roughly every 20-30 trading bars
        step_days = 7 if period == "weekly" else 14 if period == "biweekly" else 30

        history_curve = []

        if strategy.lower() == "lump_sum":
            start_price = bars[0]["close"]
            units = amount_per_period / start_price if start_price > 0 else 0
            total_invested = amount_per_period

            # Downsample curve points (max 40 points)
            step = max(1, len(bars) // 35)
            for i in range(0, len(bars), step):
                bar = bars[i]
                d_str = datetime.fromtimestamp(bar["time"], tz=timezone.utc).strftime("%Y-%m-%d")
                val = units * bar["close"]
                history_curve.append({
                    "date": d_str,
                    "invested": round(total_invested, 2),
                    "portfolio_value": round(val, 2)
                })

            final_val = units * current_price
            pnl = final_val - total_invested
            roi = ((pnl / total_invested) * 100) if total_invested > 0 else 0

            return {
                "total_invested": round(total_invested, 2),
                "current_portfolio_value": round(final_val, 2),
                "total_profit_loss": round(pnl, 2),
                "roi_percent": round(roi, 2),
                "total_units_bought": round(units, 6),
                "average_buy_price": round(start_price, 2),
                "current_price": round(current_price, 2),
                "history_curve": history_curve
            }
        else:
            # DCA Strategy
            total_invested = 0.0
            total_units = 0.0
            last_buy_time = 0

            step_sec = step_days * 86400

            for bar in bars:
                t = bar["time"]
                price = bar["close"]
                
                # Check if period has elapsed for another purchase
                if (t - last_buy_time) >= step_sec or last_buy_time == 0:
                    bought = amount_per_period / price if price > 0 else 0
                    total_units += bought
                    total_invested += amount_per_period
                    last_buy_time = t

                    d_str = datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d")
                    cur_val = total_units * price
                    history_curve.append({
                        "date": d_str,
                        "invested": round(total_invested, 2),
                        "portfolio_value": round(cur_val, 2)
                    })

            # Ensure latest point is represented
            final_d_str = datetime.fromtimestamp(bars[-1]["time"], tz=timezone.utc).strftime("%Y-%m-%d")
            final_val = total_units * current_price
            if not history_curve or history_curve[-1]["date"] != final_d_str:
                history_curve.append({
                    "date": final_d_str,
                    "invested": round(total_invested, 2),
                    "portfolio_value": round(final_val, 2)
                })

            avg_buy_price = (total_invested / total_units) if total_units > 0 else 0
            pnl = final_val - total_invested
            roi = ((pnl / total_invested) * 100) if total_invested > 0 else 0

            return {
                "total_invested": round(total_invested, 2),
                "current_portfolio_value": round(final_val, 2),
                "total_profit_loss": round(pnl, 2),
                "roi_percent": round(roi, 2),
                "total_units_bought": round(total_units, 6),
                "average_buy_price": round(avg_buy_price, 2),
                "current_price": round(current_price, 2),
                "history_curve": history_curve
            }

    @staticmethod
    def calculate_risk(total_capital: float, risk_percent: float, entry_price: float, stop_loss_price: float, take_profit_price: float) -> Dict[str, Any]:
        max_dollar_risk = total_capital * (risk_percent / 100.0)
        risk_per_unit = abs(entry_price - stop_loss_price)
        
        if risk_per_unit <= 0:
            return {
                "max_dollar_risk": max_dollar_risk,
                "risk_per_unit": 0.0,
                "recommended_position_size": 0.0,
                "total_position_cost": 0.0,
                "potential_profit": 0.0,
                "risk_to_reward_ratio": "1 : 0",
                "recommendation": "Invalid Stop Loss Price"
            }

        position_size = max_dollar_risk / risk_per_unit
        total_cost = position_size * entry_price
        profit_per_unit = abs(take_profit_price - entry_price)
        potential_profit = position_size * profit_per_unit
        
        ratio = profit_per_unit / risk_per_unit if risk_per_unit > 0 else 0
        ratio_str = f"1 : {ratio:.2f}"
        
        if ratio >= 2.0:
            rec = "Favorable Setup (Risk-to-Reward ≥ 1:2)"
        elif ratio >= 1.5:
            rec = "Moderate Setup (Risk-to-Reward 1:1.5 - 1:2)"
        else:
            rec = "Suboptimal Setup (Risk-to-Reward < 1:1.5)"

        return {
            "max_dollar_risk": round(max_dollar_risk, 2),
            "risk_per_unit": round(risk_per_unit, 2),
            "recommended_position_size": round(position_size, 4),
            "total_position_cost": round(total_cost, 2),
            "potential_profit": round(potential_profit, 2),
            "risk_to_reward_ratio": ratio_str,
            "recommendation": rec
        }
