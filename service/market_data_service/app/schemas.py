from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict

@dataclass
class MarketDataEvent:
    symbol: str
    bid: float
    ask: float
    bid_qty: float
    ask_qty: float
    mid: float
    event_time: int | None
    source: str = "binance"
    event_type: str = "market_data"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def parse_book_ticker(payload: Dict[str, Any]) -> MarketDataEvent:
    """
    Expected Binance bookTicker payload fields commonly include:
    s = symbol
    b = best bid price
    B = best bid qty
    a = best ask price
    A = best ask qty
    E = event time (may not always be present depending on stream variant)
    """
    symbol = str(payload["s"]).upper()
    bid = float(payload["b"])
    ask = float(payload["a"])
    bid_qty = float(payload["B"])
    ask_qty = float(payload["A"])
    event_time = int(payload["E"]) if "E" in payload else None

    if bid <= 0 or ask <= 0:
        raise ValueError("Bid/ask must be positive")

    if bid > ask:
        # Rare / defensive check
        raise ValueError("Bid is greater than ask")

    mid = (bid + ask) / 2

    return MarketDataEvent(
        symbol=symbol,
        bid=bid,
        ask=ask,
        bid_qty=bid_qty,
        ask_qty=ask_qty,
        mid=mid,
        event_time=event_time,
    )