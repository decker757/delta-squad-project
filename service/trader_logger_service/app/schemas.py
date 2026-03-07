from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Any, Dict


@dataclass
class EventLog:
    event_type: str
    symbol: str
    payload: Dict[str, Any]
    received_at: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def parse_event_log(raw: Dict[str, Any]) -> EventLog:
    event_type = raw.get("event_type")
    if not event_type:
        raise ValueError("Missing event_type field")

    symbol = raw.get("symbol", "UNKNOWN")

    return EventLog(
        event_type=event_type,
        symbol=symbol,
        payload=raw,
        received_at=time.time(),
    )
