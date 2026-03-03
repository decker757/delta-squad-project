import logging

from .binance_client import BinanceBookTickerClient
from .publisher import KafkaPublisher
from .schemas import parse_book_ticker

class MarketDataService:
    def __init__(
        self,
        symbol: str,
        topic: str,
        client: BinanceBookTickerClient,
        publisher: KafkaPublisher,
        logger: logging.Logger,
    ):
        self.symbol = symbol
        self.topic = topic
        self.client = client
        self.publisher = publisher
        self.logger = logger

    async def run(self) -> None:
        self.logger.info(
            "starting MarketDataService symbol=%s topic=%s",
            self.symbol,
            self.topic,
        )

        try:
            async for raw_payload in self.client.stream():
                try:
                    event = parse_book_ticker(raw_payload)
                    self.publisher.publish(
                        topic=self.topic,
                        payload=event.to_dict(),
                        key=event.symbol,
                    )

                    self.logger.info(
                        "Published market_data symbol=%s bid=%s ask=%s mid=%s",
                        event.symbol,
                        event.bid,
                        event.ask,
                        event.mid,
                    )
                except Exception as e:
                    self.logger.exception(
                        "Failed to process/publish market data payload=%s error=%s",
                        raw_payload,
                        e,
                    )
        finally:
            self.publisher.close()

