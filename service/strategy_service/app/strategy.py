from __future__ import annotations

import statistics
from collections import deque
from dataclasses import dataclass


@dataclass
class CrossoverResult:
    side: str
    short_ma: float
    long_ma: float


class MACrossoverStrategy:
    def __init__(self, short_window: int, long_window: int):
        if short_window >= long_window:
            raise ValueError(
                f"short_window ({short_window}) must be less than long_window ({long_window})"
            )
        self.short_window = short_window
        self.long_window = long_window
        self._prices: deque[float] = deque(maxlen=long_window)
        self._last_side: str | None = None

    def evaluate(self, mid: float) -> CrossoverResult | None:
        self._prices.append(mid)

        if len(self._prices) < self.long_window:
            return None

        short_ma = statistics.mean(list(self._prices)[-self.short_window:])
        long_ma = statistics.mean(self._prices)

        if short_ma > long_ma:
            curr_side = "BUY"
        elif short_ma < long_ma:
            curr_side = "SELL"
        else:
            # MAs are equal — no clear direction, don't update state
            return None

        prev_side = self._last_side
        self._last_side = curr_side

        # Only emit on crossover (direction change), not every tick
        if prev_side is None or curr_side == prev_side:
            return None

        return CrossoverResult(side=curr_side, short_ma=short_ma, long_ma=long_ma)
