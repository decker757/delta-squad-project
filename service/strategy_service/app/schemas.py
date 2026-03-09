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
    source: str
    event_type: str


def parse_market_data_event(payload: Dict[str, Any]) -> MarketDataEvent:
    bid = float(payload["bid"])
    ask = float(payload["ask"])
    mid = float(payload["mid"])

    if bid <= 0 or ask <= 0 or mid <= 0:
        raise ValueError(f"bid/ask/mid must be positive: bid={bid} ask={ask} mid={mid}")
    if bid > ask:
        raise ValueError(f"bid ({bid}) cannot be greater than ask ({ask})")

    return MarketDataEvent(
        symbol=payload["symbol"],
        bid=bid,
        ask=ask,
        bid_qty=float(payload["bid_qty"]),
        ask_qty=float(payload["ask_qty"]),
        mid=mid,
        event_time=payload.get("event_time"),
        source=payload.get("source", "binance"),
        event_type=payload.get("event_type", "market_data"),
    )


@dataclass
class TradeSignal:
    symbol: str
    side: str          # "BUY" or "SELL"
    short_ma: float
    long_ma: float
    mid: float
    timestamp: float
    quantity: float
    price: float
    type: str = "LIMIT"
    timeInForce: str = "GTC"
    signal_type: str = "MA_CROSSOVER"
    event_type: str = "trade_signal"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
