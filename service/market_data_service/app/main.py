import asyncio
import logging

from .config import Config
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
    service = MarketDataService(logger=logger)
    await service.run()


if __name__ == "__main__":
    asyncio.run(async_main())