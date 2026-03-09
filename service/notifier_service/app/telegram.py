import json
import logging
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

from .schemas import ExecutionResult, BlockedOrder

_MAX_RETRIES = 3
_RETRY_BACKOFF_SECONDS = 2


class TelegramClient:
    BASE_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, bot_token: str, chat_id: str, logger: logging.Logger):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.logger = logger
        self._url = self.BASE_URL.format(token=bot_token)

    def send_message(self, text: str) -> None:
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

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status != 200:
                        self.logger.error("Telegram API returned status %s", resp.status)
                    return  # success (or non-retryable API error)
            except urllib.error.URLError as e:
                if attempt < _MAX_RETRIES:
                    delay = _RETRY_BACKOFF_SECONDS * attempt
                    self.logger.warning(
                        "Telegram send failed (attempt %d/%d): %s — retrying in %ds",
                        attempt, _MAX_RETRIES, e, delay,
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(
                        "Telegram send failed after %d attempts: %s", _MAX_RETRIES, e
                    )

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
