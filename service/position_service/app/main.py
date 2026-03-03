import logging

from .config import Config
from .consumer import KafkaConsumer
from .db import PositionDB
from .service import PositionService


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
        topic=[Config.EXECUTION_RESULT_TOPIC, Config.MARKET_DATA_TOPIC],
        logger=logger,
    )
    db = PositionDB(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        dbname=Config.DB_NAME,
        logger=logger,
    )
    service = PositionService(
        symbol=Config.SYMBOL,
        consumer=consumer,
        db=db,
        logger=logger,
    )
    service.run()


if __name__ == "__main__":
    main()
