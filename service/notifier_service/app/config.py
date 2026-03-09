import os


class Config:
    SERVICE_NAME = "notifier-service"

    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    EXECUTION_RESULT_TOPIC = os.getenv("EXECUTION_RESULT_TOPIC", "execution_result")
    BLOCKED_ORDER_TOPIC = os.getenv("BLOCKED_ORDER_TOPIC", "blocked_order")
    CONSUMER_GROUP_ID = os.getenv("CONSUMER_GROUP_ID", "notifier-service")

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

    SYMBOL = os.getenv("SYMBOL", "BTCUSDT")

    DB_HOST = os.getenv("DB_HOST", "")
    DB_PORT = int(os.getenv("DB_PORT") or "5432")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "postgres")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
