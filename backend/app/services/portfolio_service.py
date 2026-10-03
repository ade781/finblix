from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.simulation import VirtualPortfolio, VirtualTrade
from app.models.asset import Asset

class PortfolioService:
    @classmethod
    def get_or_create_portfolio(cls, db: Session, user_name: str = "default_trader") -> VirtualPortfolio:
        port = db.query(VirtualPortfolio).filter(VirtualPortfolio.user_name == user_name).first()
        if not port:
            port = VirtualPortfolio(
                user_name=user_name,
                portfolio_name="Main Paper Trading",
                initial_balance=10000.00,
                cash_balance=10000.00,
                currency="USD"
            )
            db.add(port)
            db.commit()
            db.refresh(port)
        return port

    @classmethod
    def execute_trade(
        cls, 
        db: Session, 
        user_name: str, 
        symbol: str, 
        trade_type: str, 
        amount: float, 
        current_price: float
    ) -> Dict[str, Any]:
        port = cls.get_or_create_portfolio(db, user_name)
        asset = db.query(Asset).filter((Asset.symbol == symbol) | (Asset.symbol == symbol.replace("-", "/"))).first()
        if not asset:
            raise ValueError(f"Asset {symbol} not found")

        total_cost = float(amount) * float(current_price)

        if trade_type.lower() == "buy":
            if float(port.cash_balance) < total_cost:
                raise ValueError(f"Saldo cash tidak mencukupi. Saldo: ${float(port.cash_balance):,.2f}, Diperlukan: ${total_cost:,.2f}")

            port.cash_balance = float(port.cash_balance) - total_cost

            trade = VirtualTrade(
                portfolio_id=port.id,
                asset_id=asset.id,
                trade_type="buy",
                amount=amount,
                entry_price=current_price,
                total_cost=total_cost,
                status="open"
            )
            db.add(trade)
            db.commit()
            db.refresh(trade)
            return {
                "status": "success",
                "message": f"Berhasil beli {amount} {asset.symbol} pada harga ${current_price:,.2f}",
                "trade_id": trade.id,
                "remaining_cash": float(port.cash_balance)
            }
        else:
            raise ValueError("Untuk menutup posisi, gunakan fungsi close_position.")

    @classmethod
    def close_position(cls, db: Session, trade_id: int, current_price: float) -> Dict[str, Any]:
        trade = db.query(VirtualTrade).filter(VirtualTrade.id == trade_id, VirtualTrade.status == "open").first()
        if not trade:
            raise ValueError("Posisi terbuka tidak ditemukan atau sudah ditutup")

        port = db.query(VirtualPortfolio).filter(VirtualPortfolio.id == trade.portfolio_id).first()

        entry_p = float(trade.entry_price)
        cur_p = float(current_price)
        amt = float(trade.amount)

        gross_return = amt * cur_p
        pnl_amt = (cur_p - entry_p) * amt
        pnl_pct = ((cur_p - entry_p) / entry_p) * 100.0 if entry_p > 0 else 0.0

        trade.closed_price = cur_p
        trade.pnl_amount = pnl_amt
        trade.pnl_percent = pnl_pct
        trade.status = "closed"

        port.cash_balance = float(port.cash_balance) + gross_return

        db.commit()

        return {
            "status": "success",
            "message": f"Posisi #{trade_id} berhasil ditutup pada harga ${cur_p:,.2f}. PnL: ${pnl_amt:,.2f} ({pnl_pct:+.2f}%)",
            "pnl_amount": pnl_amt,
            "pnl_percent": pnl_pct,
            "new_cash_balance": float(port.cash_balance)
        }

    @classmethod
    def get_portfolio_summary(cls, db: Session, user_name: str = "default_trader", live_prices: Dict[str, float] = None) -> Dict[str, Any]:
        if live_prices is None:
            live_prices = {}

        port = cls.get_or_create_portfolio(db, user_name)
        trades = db.query(VirtualTrade).filter(VirtualTrade.portfolio_id == port.id).all()

        open_trades = []
        closed_trades = []
        unrealized_pnl = 0.0
        realized_pnl = 0.0
        open_positions_val = 0.0

        for t in trades:
            asset = db.query(Asset).filter(Asset.id == t.asset_id).first()
            sym = asset.symbol if asset else "UNKNOWN"
            cur_p = live_prices.get(sym, float(t.entry_price))

            if t.status == "open":
                entry_p = float(t.entry_price)
                amt = float(t.amount)
                val = amt * cur_p
                open_positions_val += val
                pnl = (cur_p - entry_p) * amt
                pnl_pct = ((cur_p - entry_p) / entry_p) * 100.0 if entry_p > 0 else 0.0
                unrealized_pnl += pnl

                open_trades.append({
                    "id": t.id,
                    "symbol": sym,
                    "trade_type": t.trade_type,
                    "amount": amt,
                    "entry_price": entry_p,
                    "current_price": cur_p,
                    "total_cost": float(t.total_cost),
                    "current_value": round(val, 2),
                    "unrealized_pnl": round(pnl, 2),
                    "unrealized_pnl_percent": round(pnl_pct, 2),
                    "executed_at": t.executed_at.strftime("%Y-%m-%d %H:%M") if t.executed_at else ""
                })
            else:
                pnl_amt = float(t.pnl_amount or 0.0)
                realized_pnl += pnl_amt
                closed_trades.append({
                    "id": t.id,
                    "symbol": sym,
                    "trade_type": t.trade_type,
                    "amount": float(t.amount),
                    "entry_price": float(t.entry_price),
                    "closed_price": float(t.closed_price or 0.0),
                    "pnl_amount": round(pnl_amt, 2),
                    "pnl_percent": round(float(t.pnl_percent or 0.0), 2),
                    "executed_at": t.executed_at.strftime("%Y-%m-%d %H:%M") if t.executed_at else ""
                })

        cash = float(port.cash_balance)
        total_port_val = cash + open_positions_val
        total_pnl = (total_port_val - float(port.initial_balance))
        total_roi = (total_pnl / float(port.initial_balance)) * 100.0

        wins = sum(1 for c in closed_trades if c["pnl_amount"] > 0)
        win_rate = (wins / len(closed_trades) * 100.0) if closed_trades else 0.0

        return {
            "portfolio_name": port.portfolio_name,
            "currency": port.currency,
            "initial_balance": float(port.initial_balance),
            "cash_balance": round(cash, 2),
            "open_positions_value": round(open_positions_val, 2),
            "total_portfolio_value": round(total_port_val, 2),
            "realized_pnl": round(realized_pnl, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "total_pnl": round(total_pnl, 2),
            "total_roi_percent": round(total_roi, 2),
            "win_rate": round(win_rate, 2),
            "open_trades": open_trades,
            "closed_trades": closed_trades
        }

    @classmethod
    def reset_portfolio(cls, db: Session, user_name: str = "default_trader") -> Dict[str, Any]:
        port = cls.get_or_create_portfolio(db, user_name)
        db.query(VirtualTrade).filter(VirtualTrade.portfolio_id == port.id).delete()
        port.cash_balance = 10000.00
        db.commit()
        return {"status": "success", "message": "Portofolio virtual berhasil di-reset ke $10,000"}
