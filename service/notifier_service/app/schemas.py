from __future__ import annotations

from dataclasses import dataclass, asdict
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

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BlockedOrder:
    order_id: str
    symbol: str
    side: str
    quantity: float
    reason: str
    timestamp: float
    event_type: str = "blocked_order"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def parse_execution_result(payload: Dict[str, Any]) -> ExecutionResult:
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
        status=payload["status"],
        timestamp=float(payload["timestamp"]),
    )


def parse_blocked_order(payload: Dict[str, Any]) -> BlockedOrder:
    quantity = float(payload["quantity"])
    if quantity <= 0:
        raise ValueError("quantity must be positive")

    side = payload["side"]
    if side not in ("BUY", "SELL"):
        raise ValueError(f"Invalid side: {side!r}")

    return BlockedOrder(
        order_id=payload["order_id"],
        symbol=payload["symbol"],
        side=side,
        quantity=quantity,
        reason=payload["reason"],
        timestamp=float(payload["timestamp"]),
    )
