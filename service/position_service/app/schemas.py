from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict

@dataclass                                                                                                                                                                                                  
class ExecutionResult:                                                                                                                                                                                      
    order_id: str                                                                                                                                                                                           
    symbol: str 
    side: str           # "BUY" or "SELL"
    quantity: float
    fill_price: float
    status: str         # "FILLED", "PARTIALLY_FILLED", "REJECTED"
    timestamp: float
    event_type: str = "execution_result"

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

def parse_execution_result(payload) -> ExecutionResult:
    status = payload["status"]
    if status not in ("FILLED", "PARTIALLY_FILLED"):
        raise ValueError(f"Skipping non-fill status: {status}")

    quantity = float(payload["quantity"])
    fill_price = float(payload["fill_price"])

    if quantity <= 0 or fill_price <= 0:
        raise ValueError("quantity and fill_price must be positive")

    side = payload["side"]
    if side not in ("BUY", "SELL"):
        raise ValueError(f"Invalid side: {side!r}")

    return ExecutionResult(
        order_id=payload["order_id"],
        symbol=payload["symbol"],
        side=side,
        quantity=quantity,
        fill_price=fill_price,
        status=status,
        timestamp=float(payload["timestamp"]),
    )
