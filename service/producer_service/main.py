import json
import logging
import os
import random
import threading
import time
import uuid
from kafka import KafkaProducer, KafkaConsumer, errors

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("producer-service")

# ----------------------------
# Config
# ----------------------------
KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_STARTUP_DELAY = 15

SYMBOL = os.getenv("SYMBOL", "BTCUSDT")
QUANTITY = float(os.getenv("QUANTITY", "0.01"))
SIGNAL_INTERVAL_SECONDS = float(os.getenv("SIGNAL_INTERVAL_SECONDS", "5"))

# ----------------------------
# Wait for Kafka
# ----------------------------
time.sleep(KAFKA_STARTUP_DELAY)
while True:
    try:
        probe = KafkaProducer(bootstrap_servers=KAFKA_BROKER)
        probe.close()
        logger.info("Kafka is reachable!")
        break
    except errors.NoBrokersAvailable:
        logger.info("Waiting for Kafka...")
        time.sleep(2)

# ----------------------------
# Kafka clients
# ----------------------------
producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER)
consumer = KafkaConsumer(
    "market_data",
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda m: json.loads(m.decode()),
)

# ----------------------------
# Market price tracking
# ----------------------------
_price_lock = threading.Lock()
_latest_mid_price = None

def get_latest_mid():
    with _price_lock:
        return _latest_mid_price

def update_market_price():
    global _latest_mid_price
    for msg in consumer:
        try:
            market_data = msg.value
            if market_data.get("symbol") == SYMBOL:
                with _price_lock:
                    _latest_mid_price = market_data.get("mid")
        except Exception as e:
            logger.error(f"Error processing market data message: {e}", exc_info=True)

threading.Thread(target=update_market_price, daemon=True).start()

# ----------------------------
# Main loop
# ----------------------------
logger.info("Producer service started, waiting for initial market price...")

while get_latest_mid() is None:
    time.sleep(1)

logger.info("Initial market price received, generating trade signals...")

while True:
    mid_price = get_latest_mid()

    trade_order = {
        "symbol": SYMBOL,
        "side": random.choice(["BUY", "SELL"]),
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": f"{QUANTITY:.7f}",
        "price": f"{mid_price:.2f}",
        "internal_id": str(uuid.uuid4()),
    }

    producer.send("trade_signal", json.dumps(trade_order).encode())
    producer.flush()
    logger.info(f"Trade signal sent: {trade_order}")
    time.sleep(SIGNAL_INTERVAL_SECONDS)
