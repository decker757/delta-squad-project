import signal

from .schemas import parse_execution_result, parse_blocked_order


class NotifierService:
    def __init__(self, consumer, telegram, logger):
        self.consumer = consumer
        self.telegram = telegram
        self.logger = logger

    def run(self):
        def _handle_signal(_signum, _frame):
            self.logger.info("Shutdown signal received, stopping gracefully")
            self.consumer.stop()

        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)

        self.logger.info("Notifier service started, listening for events")

        try:
            for raw_payload in self.consumer.stream():
                event_type = raw_payload.get("event_type")

                if event_type == "execution_result":
                    self._on_execution_result(raw_payload)
                elif event_type == "blocked_order":
                    self._on_blocked_order(raw_payload)
        finally:
            self.consumer.close()

    def _on_execution_result(self, payload):
        try:
            event = parse_execution_result(payload)
            self.telegram.notify_execution(event)
            self.logger.info(
                "Notified execution: order=%s side=%s qty=%s price=%s",
                event.order_id, event.side, event.quantity, event.fill_price,
            )
        except Exception as e:
            self.logger.exception("Failed to process execution_result: %s", e)

    def _on_blocked_order(self, payload):
        try:
            event = parse_blocked_order(payload)
            self.telegram.notify_blocked(event)
            self.logger.info(
                "Notified blocked order: order=%s reason=%s",
                event.order_id, event.reason,
            )
        except Exception as e:
            self.logger.exception("Failed to process blocked_order: %s", e)
