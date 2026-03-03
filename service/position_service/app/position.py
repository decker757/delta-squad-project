from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Position:
    symbol: str
    net_qty: float = 0.0
    avg_entry_price: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0

    def apply_fill(self, side, qty, fill_price) -> float:
        if side == "BUY":
            if self.net_qty < 0:
                # Covering or reducing a short position
                realized = (self.avg_entry_price - fill_price) * qty
                self.realized_pnl += realized
                self.net_qty += qty
                if self.net_qty == 0:
                    self.avg_entry_price = 0.0
                return realized
            else:
                # Opening or adding to a long position
                self.avg_entry_price = (self.avg_entry_price * self.net_qty + fill_price * qty) / (self.net_qty + qty)
                self.net_qty += qty
                return 0.0
        else:  # SELL
            if self.net_qty > 0:
                # Reducing or closing a long position
                realized = (fill_price - self.avg_entry_price) * qty
                self.realized_pnl += realized
                self.net_qty -= qty
                if self.net_qty == 0:
                    self.avg_entry_price = 0.0
                return realized
            else:
                # Opening or adding to a short position
                self.avg_entry_price = (self.avg_entry_price * abs(self.net_qty) + fill_price * qty) / (abs(self.net_qty) + qty)
                self.net_qty -= qty
                return 0.0
        
    def get_unrealized_pnl(self, current_mid) -> float:
        if self.net_qty == 0:
            return 0.0
        return (current_mid - self.avg_entry_price) * self.net_qty
    

