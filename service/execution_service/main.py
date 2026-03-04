import json
import time
import logging
import hmac
import hashlib
import requests
import os
from kafka import KafkaConsumer
from decimal import Decimal, ROUND_DOWN
from dotenv import load_dotenv

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
if not API_KEY or not API_SECRET:
    raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET must be set in .env")

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("execution-service")

# ----------------------------
# Kafka Config
# ----------------------------
KAFKA_BROKER = "kafka:9092"
APPROVED_TOPIC = "approved_order"

consumer = KafkaConsumer(
    APPROVED_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
)

# ----------------------------
# Binance Testnet API
# ----------------------------
BASE_URL = "https://testnet.binance.vision/api/v3"

# ----------------------------
# Helper Functions
# ----------------------------
def format_decimal(value, precision=8):
    """Format number to string with proper precision"""
    return str(Decimal(value).quantize(Decimal("1." + "0"*precision), rounding=ROUND_DOWN))

def create_signature(params, secret):
    """Generate HMAC SHA256 signature, ignoring None values"""
    query_string = "&".join([f"{k}={v}" for k, v in params.items() if v is not None])
    return hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

def send_order_to_binance(order: dict):
    """Send LIMIT or MARKET order to Binance Testnet"""
    order_type = order["type"].upper()
    symbol = order["symbol"]
    side = order["side"].upper()
    quantity = format_decimal(order["quantity"], precision=6)
    price = format_decimal(order.get("price"), precision=2) if "price" in order else None

    # Build Binance parameters
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

    # Add signature
    params["signature"] = create_signature(params, API_SECRET)

    headers = {"X-MBX-APIKEY": API_KEY}
    url = f"{BASE_URL}/order"

    try:
        response = requests.post(url, params=params, headers=headers, timeout=5)
        data = response.json()
        if response.status_code == 200 and "orderId" in data:
            logger.info(f"Order SUCCESS: internal_id={order['internal_id']} {data}")
        else:
            logger.warning(f"Order FAILED: internal_id={order['internal_id']} {data}")
    except Exception as e:
        logger.error(f"Error sending order: internal_id={order['internal_id']} {e}")

# ----------------------------
# Main Loop
# ----------------------------
logger.info("Execution service started, listening to approved orders...")

for message in consumer:
    order = message.value
    internal_id = order.get("internal_id", "UNKNOWN")
    logger.info(f"Received approved order: internal_id={internal_id} {order}")

    # Basic validation
    required_fields = ["symbol", "side", "quantity", "type", "internal_id"]
    if not all(f in order for f in required_fields):
        logger.warning(f"Invalid order received: internal_id={internal_id} {order}")
        continue

    # Send to Binance Testnet
    send_order_to_binance(order)