import os


class Config:
    SERVICE_NAME = "trader-logger-service"

    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    CONSUMER_GROUP_ID = os.getenv("CONSUMER_GROUP_ID", "trader-logger-service")

    MARKET_DATA_TOPIC = os.getenv("MARKET_DATA_TOPIC", "market_data")
    TRADE_SIGNAL_TOPIC = os.getenv("TRADE_SIGNAL_TOPIC", "trade_signal")
    APPROVED_ORDER_TOPIC = os.getenv("APPROVED_ORDER_TOPIC", "approved_order")
    BLOCKED_ORDER_TOPIC = os.getenv("BLOCKED_ORDER_TOPIC", "blocked_order")
    EXECUTION_RESULT_TOPIC = os.getenv("EXECUTION_RESULT_TOPIC", "execution_result")

    ALL_TOPICS = [
        MARKET_DATA_TOPIC,
        TRADE_SIGNAL_TOPIC,
        APPROVED_ORDER_TOPIC,
        BLOCKED_ORDER_TOPIC,
        EXECUTION_RESULT_TOPIC,
    ]

    DB_HOST = os.getenv("DB_HOST", "postgres")
    DB_PORT = int(os.getenv("DB_PORT") or "5432")
    DB_USER = os.getenv("DB_USER", "trader")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "trader")
    DB_NAME = os.getenv("DB_NAME", "trading")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
