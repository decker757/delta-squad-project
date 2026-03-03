import logging

from .binance_client import BinanceBookTickerClient
from .config import Config
from .publisher import KafkaPublisher
from .schemas import parse_book_ticker

class MarketDataService:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.client = BinanceBookTickerClient(
            ws_url=Config.BINANCE_WS_BASE_URL,
            reconnect_delay=Config.RECONNECT_DELAY_SECONDS,
            logger=logger
        )
        self.publisher = KafkaPublisher(
            bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
            logger=logger
        )
    
    async def run(self) -> None:
        self.logger.info(
            "starting MarketDataService symbol=%s topic=%s",
            Config.SYMBOL,
            Config.MARKET_DATA_TOPIC
        )

        try:
            async for raw_payload in self.client.stream():
                try:
                    event = parse_book_ticker(raw_payload)
                    self.publisher.publish(
                        topic=Config.MARKET_DATA_TOPIC,
                        payload=event.to_dict(),
                    )

                    self.logger.info(
                        "Published market_data symbol=%s bid=%s ask=%s mid=%s",
                        event.symbol,
                        event.bid,
                        event.ask,
                        event.mid
                    )
                except Exception as e:
                    self.logger.exception(
                        "Failed to process/publish market data payload=%s error=%s",
                        raw_payload,
                        e,
                    )
        finally:
            self.publisher.close()

