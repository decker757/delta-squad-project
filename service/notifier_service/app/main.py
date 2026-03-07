import logging

from .config import Config
from .consumer import KafkaConsumer
from .telegram import TelegramClient
from .service import NotifierService


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
        topics=[Config.EXECUTION_RESULT_TOPIC, Config.BLOCKED_ORDER_TOPIC],
        logger=logger,
    )
    telegram = TelegramClient(
        bot_token=Config.TELEGRAM_BOT_TOKEN,
        chat_id=Config.TELEGRAM_CHAT_ID,
        logger=logger,
    )
    service = NotifierService(
        consumer=consumer,
        telegram=telegram,
        logger=logger,
    )
    service.run()


if __name__ == "__main__":
    main()
