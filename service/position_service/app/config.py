import os


class Config:
    SERVICE_NAME = "position-service"

    SYMBOL = os.getenv("SYMBOL", "BTCUSDT").upper()

    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    EXECUTION_RESULT_TOPIC = os.getenv("EXECUTION_RESULT_TOPIC", "execution_result")
    MARKET_DATA_TOPIC = os.getenv("MARKET_DATA_TOPIC", "market_data")
    CONSUMER_GROUP_ID = os.getenv("CONSUMER_GROUP_ID", "position-service")

    DB_HOST = os.getenv("DB_HOST", "postgres")
    DB_PORT = int(os.getenv("DB_PORT") or "5432")
    DB_USER = os.getenv("DB_USER", "trader")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "trader")
    DB_NAME = os.getenv("DB_NAME", "trading")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")