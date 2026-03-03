import logging
import signal
import time

from .consumer import KafkaConsumer
from .publisher import KafkaPublisher
from .schemas import parse_market_data_event, TradeSignal
from .strategy import MACrossoverStrategy


class StrategyService:
    def __init__(
        self,
        symbol: str,
        signal_topic: str,
        consumer: KafkaConsumer,
        publisher: KafkaPublisher,
        strategy: MACrossoverStrategy,
        logger: logging.Logger,
    ):
        self.symbol = symbol
        self.signal_topic = signal_topic
        self.consumer = consumer
        self.publisher = publisher
        self.strategy = strategy
        self.logger = logger

    def run(self) -> None:
        def _handle_signal(_signum, _frame):
            self.logger.info("Shutdown signal received, stopping gracefully")
            self.consumer.stop()

        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)

        self.logger.info(
            "starting StrategyService symbol=%s signal_topic=%s short_window=%s long_window=%s",
            self.symbol,
            self.signal_topic,
            self.strategy.short_window,
            self.strategy.long_window,
        )

        try:
            for raw_payload in self.consumer.stream():
                try:
                    event = parse_market_data_event(raw_payload)
                    result = self.strategy.evaluate(event.mid)

                    if result is None:
                        continue

                    trade_signal = TradeSignal(
                        symbol=event.symbol,
                        side=result.side,
                        short_ma=result.short_ma,
                        long_ma=result.long_ma,
                        mid=event.mid,
                        timestamp=time.time(),
                    )
                    self.publisher.publish(
                        topic=self.signal_topic,
                        payload=trade_signal.to_dict(),
                        key=event.symbol,
                    )
                    self.logger.info(
                        "Signal emitted side=%s symbol=%s short_ma=%.4f long_ma=%.4f mid=%.4f",
                        trade_signal.side,
                        trade_signal.symbol,
                        trade_signal.short_ma,
                        trade_signal.long_ma,
                        trade_signal.mid,
                    )
                except Exception as e:
                    self.logger.exception(
                        "Failed to process market data payload=%s error=%s",
                        raw_payload,
                        e,
                    )
        finally:
            self.consumer.close()
            self.publisher.close()
