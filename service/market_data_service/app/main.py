import asyncio
import logging

from .binance_client import BinanceBookTickerClient
from .config import Config
from .publisher import KafkaPublisher
from .service import MarketDataService


def setup_logger() -> logging.Logger:
    logger = logging.getLogger(Config.SERVICE_NAME)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False
    return logger


async def async_main() -> None:
    logger = setup_logger()

    client = BinanceBookTickerClient(
        ws_url=Config.BINANCE_WS_URL,
        reconnect_delay=Config.RECONNECT_DELAY_SECONDS,
        logger=logger,
    )
    publisher = KafkaPublisher(
        bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
        logger=logger,
    )
    service = MarketDataService(
        symbol=Config.SYMBOL,
        topic=Config.MARKET_DATA_TOPIC,
        client=client,
        publisher=publisher,
        logger=logger,
    )
    await service.run()


if __name__ == "__main__":
    asyncio.run(async_main())