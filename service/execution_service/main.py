import json
import os
import time
import logging
import hmac
import hashlib
import requests
from kafka import KafkaConsumer, KafkaProducer, errors
from decimal import Decimal, ROUND_DOWN
from dotenv import load_dotenv

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("execution-service")

# ----------------------------
# Config
# ----------------------------
load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
if not API_KEY or not API_SECRET:
    logger.error("BINANCE_API_KEY and BINANCE_API_SECRET must be set as environment variables")
    raise SystemExit(1)

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
APPROVED_TOPIC = "approved_order"
BASE_URL = "https://testnet.binance.vision/api/v3"
KAFKA_STARTUP_DELAY = 15

REQUIRED_FIELDS = ["symbol", "side", "quantity", "type", "internal_id"]

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
        time.sleep(10)

consumer = KafkaConsumer(
    APPROVED_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    group_id="execution-service",
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
)

# ----------------------------
# Helper functions
# ----------------------------
def format_decimal(value, precision=8):
    return str(Decimal(value).quantize(Decimal("1." + "0" * precision), rounding=ROUND_DOWN))

def create_signature(params, secret):
    query_string = "&".join([f"{k}={v}" for k, v in params.items() if v is not None])
    return hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

def send_order_to_binance(order: dict):
    order_type = order["type"].upper()
    symbol = order["symbol"]
    side = order["side"].upper()
    quantity = format_decimal(order["quantity"], precision=6)
    price = format_decimal(order.get("price"), precision=2) if "price" in order else None

    params = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
        "timestamp": int(time.time() * 1000),
    }

    if order_type == "LIMIT":
        if price is None:
            logger.warning(f"LIMIT order missing price: {order}")
            return
        params["price"] = price
        params["timeInForce"] = order.get("timeInForce", "GTC")

    params["signature"] = create_signature(params, API_SECRET)

    try:
        response = requests.post(
            f"{BASE_URL}/order",
            params=params,
            headers={"X-MBX-APIKEY": API_KEY},
            timeout=5,
        )
        data = response.json()
        if response.status_code == 200 and "orderId" in data:
            logger.info(f"Order SUCCESS: internal_id={order['internal_id']} {data}")
        else:
            logger.warning(f"Order FAILED: internal_id={order['internal_id']} {data}")
    except Exception as e:
        logger.error(f"Error sending order: internal_id={order['internal_id']} {e}")

# ----------------------------
# Main loop
# ----------------------------
logger.info("Execution service started, listening to approved orders...")

for message in consumer:
    try:
        order = message.value
        internal_id = order.get("internal_id", "UNKNOWN")
        logger.info(f"Received approved order: internal_id={internal_id} {order}")

        if not all(f in order for f in REQUIRED_FIELDS):
            logger.warning(f"Invalid order received: internal_id={internal_id} {order}")
            continue

        send_order_to_binance(order)
    except Exception as e:
        logger.error(f"Unhandled error processing message: {e}", exc_info=True)
