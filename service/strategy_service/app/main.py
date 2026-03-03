import logging

from .config import Config
from .consumer import KafkaConsumer
from .publisher import KafkaPublisher
from .service import StrategyService
from .strategy import MACrossoverStrategy


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


def main() -> None:
    logger = setup_logger()

    consumer = KafkaConsumer(
        bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
        group_id=Config.CONSUMER_GROUP_ID,
        topic=Config.MARKET_DATA_TOPIC,
        logger=logger,
    )
    publisher = KafkaPublisher(
        bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
        logger=logger,
    )
    strategy = MACrossoverStrategy(
        short_window=Config.SHORT_WINDOW,
        long_window=Config.LONG_WINDOW,
    )
    service = StrategyService(
        symbol=Config.SYMBOL,
        signal_topic=Config.TRADE_SIGNAL_TOPIC,
        consumer=consumer,
        publisher=publisher,
        strategy=strategy,
        logger=logger,
    )
    service.run()


if __name__ == "__main__":
    main()
