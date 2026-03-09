import json
import logging
import threading
import time
import urllib.error
import urllib.request

import psycopg2


class CommandPoller(threading.Thread):
    """Background thread that polls Telegram for bot commands."""

    def __init__(self, bot_token: str, chat_id: str, db_config: dict, symbol: str, logger: logging.Logger):
        super().__init__(daemon=True)
        self._base_url = f"https://api.telegram.org/bot{bot_token}"
        self.chat_id = chat_id
        self.db_config = db_config
        self.symbol = symbol
        self.logger = logger
        self._offset = 0

    def run(self) -> None:
        self.logger.info("Command poller started")
        while True:
            try:
                self._poll()
            except Exception as e:
                self.logger.warning("Command poll error: %s", e)
                time.sleep(5)

    def _poll(self) -> None:
        url = f"{self._base_url}/getUpdates?offset={self._offset}&timeout=30"
        with urllib.request.urlopen(url, timeout=35) as resp:
            data = json.loads(resp.read())

        for update in data.get("result", []):
            self._offset = update["update_id"] + 1
            text = update.get("message", {}).get("text", "")
            if text.startswith("/position"):
                self._handle_position()

    def _handle_position(self) -> None:
        try:
            conn = psycopg2.connect(**self.db_config, sslmode="require")
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT net_qty, avg_entry_price, realized_pnl, unrealized_pnl, updated_at
                        FROM positions
                        WHERE symbol = %s
                        """,
                        (self.symbol,),
                    )
                    row = cur.fetchone()
            finally:
                conn.close()

            if row is None:
                text = f"No open position for {self.symbol}."
            else:
                net_qty, avg_entry, realized_pnl, unrealized_pnl, updated_at = row
                direction = "LONG" if net_qty > 0 else "SHORT" if net_qty < 0 else "FLAT"
                text = (
                    f"*{self.symbol} Position*\n"
                    f"Direction: `{direction}`\n"
                    f"Net Qty: `{net_qty:.4f} BTC`\n"
                    f"Avg Entry: `${avg_entry:,.2f}`\n"
                    f"Unrealized PnL: `${unrealized_pnl:,.2f}`\n"
                    f"Realized PnL: `${realized_pnl:,.2f}`\n"
                    f"Updated: {updated_at.strftime('%H:%M:%S UTC')}"
                )
        except Exception as e:
            self.logger.exception("Failed to fetch position: %s", e)
            text = "Failed to fetch position — check service logs."

        self._send(text)

    def _send(self, text: str) -> None:
        payload = json.dumps({
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10):
                pass
        except urllib.error.URLError as e:
            self.logger.error("Failed to send command reply: %s", e)
