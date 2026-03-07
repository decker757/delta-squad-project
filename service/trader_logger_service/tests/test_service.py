import logging

from app.schemas import EventLog
from app.service import TraderLoggerService


class FakeConsumer:
    def __init__(self, messages):
        self._messages = messages
        self._closed = False

    def stream(self):
        yield from self._messages

    def stop(self):
        pass

    def close(self):
        self._closed = True


class FakeDB:
    def __init__(self):
        self.events = []
        self._closed = False

    def insert_event(self, event: EventLog):
        self.events.append(event)

    def close(self):
        self._closed = True


def test_service_logs_all_event_types():
    messages = [
        {"event_type": "market_data", "symbol": "BTCUSDT", "mid": 68000},
        {"event_type": "trade_signal", "symbol": "BTCUSDT", "side": "BUY"},
        {"event_type": "approved_order", "symbol": "BTCUSDT", "order_id": "o1"},
        {"event_type": "blocked_order", "symbol": "BTCUSDT", "reason": "cooldown"},
        {"event_type": "execution_result", "symbol": "BTCUSDT", "order_id": "o2"},
    ]
    consumer = FakeConsumer(messages)
    db = FakeDB()
    logger = logging.getLogger("test")

    service = TraderLoggerService(consumer=consumer, db=db, logger=logger)
    service.run()

    assert len(db.events) == 5
    assert [e.event_type for e in db.events] == [
        "market_data", "trade_signal", "approved_order", "blocked_order", "execution_result",
    ]
    assert db._closed
    assert consumer._closed


def test_service_skips_invalid_event():
    messages = [
        {"symbol": "BTCUSDT"},  # missing event_type
        {"event_type": "market_data", "symbol": "BTCUSDT"},
    ]
    consumer = FakeConsumer(messages)
    db = FakeDB()
    logger = logging.getLogger("test")

    service = TraderLoggerService(consumer=consumer, db=db, logger=logger)
    service.run()

    assert len(db.events) == 1
    assert db.events[0].event_type == "market_data"
