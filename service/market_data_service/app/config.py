import os

class Config:
    SERVICE_NAME = "market-data-service"

    SYMBOL = os.getenv("SYMBOL", "BTCUSDT").upper()
    STREAM_SYMBOL = SYMBOL.lower()

    BINANCE_WS_BASE_URL = os.getenv(
        "BINANCE_WS_BASE_URL",
        "wss://stream.binance.com:9443/ws",
    )
    BINANCE_WS_URL = f"{BINANCE_WS_BASE_URL}/{STREAM_SYMBOL}@bookTicker"

    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS",  "kafka:9092")
    MARKET_DATA_TOPIC = os.getenv("MARKET_DATA_TOPIC", "market_data")

    RECONNECT_DELAY_SECONDS = float(os.getenv("RECONNECT_DELAY_SECONDS", "3"))

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")