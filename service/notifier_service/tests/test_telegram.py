import logging

from app.schemas import ExecutionResult, BlockedOrder
from app.telegram import TelegramClient


class FakeTelegramClient(TelegramClient):
    """Subclass that captures messages instead of sending HTTP requests."""

    def __init__(self):
        self.sent_messages = []
        self.logger = logging.getLogger("test")
        self.bot_token = "fake-token"
        self.chat_id = "123"

    def send_message(self, text: str) -> None:
        self.sent_messages.append(text)


def test_notify_execution_format():
    client = FakeTelegramClient()
    event = ExecutionResult(
        order_id="order-001",
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.001,
        fill_price=68000.0,
        status="FILLED",
        timestamp=1700000000.0,
    )
    client.notify_execution(event)
    assert len(client.sent_messages) == 1
    msg = client.sent_messages[0]
    assert "Trade Executed" in msg
    assert "BTCUSDT" in msg
    assert "BUY" in msg
    assert "68000.0" in msg
    assert "order-001" in msg


def test_notify_blocked_format():
    client = FakeTelegramClient()
    event = BlockedOrder(
        order_id="order-002",
        symbol="BTCUSDT",
        side="SELL",
        quantity=0.001,
        reason="position_limit_exceeded",
        timestamp=1700000000.0,
    )
    client.notify_blocked(event)
    assert len(client.sent_messages) == 1
    msg = client.sent_messages[0]
    assert "Order Blocked" in msg
    assert "BTCUSDT" in msg
    assert "SELL" in msg
    assert "position_limit_exceeded" in msg
    assert "order-002" in msg


def test_no_credentials_skips(caplog):
    client = TelegramClient(bot_token="", chat_id="", logger=logging.getLogger("test"))
    with caplog.at_level(logging.WARNING):
        client.send_message("test")
    assert "credentials not set" in caplog.text
