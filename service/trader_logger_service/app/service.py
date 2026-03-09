import signal

from .schemas import parse_event_log


class TraderLoggerService:
    def __init__(self, consumer, db, logger):
        self.consumer = consumer
        self.db = db
        self.logger = logger

    def run(self):
        def _handle_signal(_signum, _frame):
            self.logger.info("Shutdown signal received, stopping gracefully")
            self.consumer.stop()

        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)

        self.logger.info("Trader logger service started, listening for events")

        try:
            for raw_payload in self.consumer.stream():
                self._on_event(raw_payload)
        finally:
            self.db.close()
            self.consumer.close()

    def _on_event(self, payload):
        try:
            event = parse_event_log(payload)
            self.db.insert_event(event)
            self.logger.info(
                "Logged event: type=%s symbol=%s",
                event.event_type, event.symbol,
            )
        except Exception as e:
            self.logger.exception("Failed to log event: %s", e)
