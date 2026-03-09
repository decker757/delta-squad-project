import signal

from .schemas import parse_execution_result, parse_market_data_event
from .position import Position

class PositionService:
    def __init__(self, symbol, consumer, db, logger):
        self.symbol = symbol
        self.consumer = consumer
        self.db = db
        self.logger = logger

    def run(self):
        def _handle_signal(_signum, _frame):
            self.logger.info("Shutdown signal received, stopping gracefully")
            self.consumer.stop()

        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)

        # load position from DB on startup
        self._position = self.db.load_position(self.symbol) or Position(symbol=self.symbol)

        try:
            for raw_payload in self.consumer.stream():
                event_type = raw_payload.get("event_type")

                if event_type == "execution_result":
                    self._on_execution_result(raw_payload)
                elif event_type == "market_data":
                    self._on_market_data(raw_payload)

        finally:
            self.db.close()
            self.consumer.close()

    def _on_execution_result(self, payload):
        status = payload.get("status")
        if status not in ("FILLED", "PARTIALLY_FILLED"):
            self.logger.debug("Skipping non-fill status: %s", status)
            return
        try:
            fill = parse_execution_result(payload)
            realized = self._position.apply_fill(fill.side, fill.quantity, fill.fill_price)
            self.db.upsert_position_and_insert_trade(self._position, fill, realized)
            self.logger.info(
                "Fill applied side=%s qty=%s price=%s realized_pnl=%s net_qty=%s",
                fill.side, fill.quantity, fill.fill_price, realized, self._position.net_qty,
            )
        except Exception as e:
            self.logger.exception("Failed to process execution_result: %s", e)

    def _on_market_data(self, payload):
        try:
            event = parse_market_data_event(payload)
            unrealized = self._position.get_unrealized_pnl(event.mid)
            self.db.update_unrealized_pnl(self.symbol, unrealized)
        except Exception as e:
            self.logger.exception("Failed to load market data: %s", e)