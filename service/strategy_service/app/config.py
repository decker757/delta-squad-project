import os


class Config:
    SERVICE_NAME = "strategy-service"

    SYMBOL = os.getenv("SYMBOL", "BTCUSDT").upper()

    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    MARKET_DATA_TOPIC = os.getenv("MARKET_DATA_TOPIC", "market_data")
    TRADE_SIGNAL_TOPIC = os.getenv("TRADE_SIGNAL_TOPIC", "trade_signal")
    CONSUMER_GROUP_ID = os.getenv("CONSUMER_GROUP_ID", "strategy-service")

    SHORT_WINDOW = int(os.getenv("SHORT_WINDOW", "7"))
    LONG_WINDOW = int(os.getenv("LONG_WINDOW", "25"))

    QUANTITY = float(os.getenv("QUANTITY", "0.01"))
    ORDER_TYPE = os.getenv("ORDER_TYPE", "LIMIT")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
