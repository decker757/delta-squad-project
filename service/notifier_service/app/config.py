import os


class Config:
    SERVICE_NAME = "notifier-service"

    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    EXECUTION_RESULT_TOPIC = os.getenv("EXECUTION_RESULT_TOPIC", "execution_result")
    BLOCKED_ORDER_TOPIC = os.getenv("BLOCKED_ORDER_TOPIC", "blocked_order")
    CONSUMER_GROUP_ID = os.getenv("CONSUMER_GROUP_ID", "notifier-service")

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
