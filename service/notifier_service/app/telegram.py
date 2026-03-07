import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone

from .schemas import ExecutionResult, BlockedOrder


class TelegramClient:
    BASE_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, bot_token: str, chat_id: str, logger: logging.Logger):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.logger = logger
        self._url = self.BASE_URL.format(token=bot_token)

    def send_message(self, text: str) -> None:
        if not self.bot_token or not self.chat_id:
            self.logger.warning("Telegram credentials not set, skipping notification")
            return

        payload = json.dumps({
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }).encode("utf-8")

        req = urllib.request.Request(
            self._url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status != 200:
                    self.logger.error("Telegram API returned status %s", resp.status)
        except urllib.error.URLError as e:
            self.logger.error("Failed to send Telegram message: %s", e)

    def notify_execution(self, event: ExecutionResult) -> None:
        ts = datetime.fromtimestamp(event.timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        text = (
            f"*Trade Executed*\n"
            f"Symbol: `{event.symbol}`\n"
            f"Side: `{event.side}`\n"
            f"Qty: `{event.quantity}`\n"
            f"Price: `{event.fill_price}`\n"
            f"Status: `{event.status}`\n"
            f"Order: `{event.order_id}`\n"
            f"Time: {ts}"
        )
        self.send_message(text)

    def notify_blocked(self, event: BlockedOrder) -> None:
        ts = datetime.fromtimestamp(event.timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        text = (
            f"*Order Blocked*\n"
            f"Symbol: `{event.symbol}`\n"
            f"Side: `{event.side}`\n"
            f"Qty: `{event.quantity}`\n"
            f"Reason: `{event.reason}`\n"
            f"Order: `{event.order_id}`\n"
            f"Time: {ts}"
        )
        self.send_message(text)
