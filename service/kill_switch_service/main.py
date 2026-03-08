import json
import os
import time
import logging
import uuid
from collections import defaultdict
from kafka import KafkaConsumer, KafkaProducer, errors

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kill-switch-service")

# ----------------------------
# Config
# ----------------------------
KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TRADE_SIGNAL_TOPIC = "trade_signal"
APPROVED_TOPIC = "approved_order"
BLOCKED_TOPIC = "blocked_order"

KAFKA_STARTUP_DELAY = 15
COOLDOWN_SECONDS = float(os.getenv("COOLDOWN_SECONDS", "3"))
MAX_POSITION = float(os.getenv("MAX_POSITION", "1.0"))

REQUIRED_FIELDS = ["symbol", "side", "quantity", "type"]
VALID_SIDES = ("BUY", "SELL")

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

# ----------------------------
# Kafka clients
# ----------------------------
consumer = KafkaConsumer(
    TRADE_SIGNAL_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

# ----------------------------
# State
# NOTE: positions are in-memory only — they reset on service restart.
# For production, back this with a persistent store (e.g. Redis).
# ----------------------------
positions: dict = defaultdict(float)
last_trade_time: dict = {}

# ----------------------------
# Risk & cooldown checks
# ----------------------------
def check_risk(symbol: str, side: str, quantity: float) -> bool:
    new_pos = positions[symbol] + (quantity if side == "BUY" else -quantity)
    if abs(new_pos) > MAX_POSITION:
        logger.warning(f"Trade BLOCKED due to position limit: {symbol} {side} {quantity}")
        return False
    return True

def check_cooldown(symbol: str) -> bool:
    elapsed = time.time() - last_trade_time.get(symbol, 0)
    if elapsed < COOLDOWN_SECONDS:
        logger.info(f"Trade BLOCKED due to cooldown ({COOLDOWN_SECONDS - elapsed:.3f}s remaining)")
        return False
    return True

# ----------------------------
# Signal processing
# ----------------------------
def process_trade_signal(trade_signal: dict):
    trade_signal.setdefault("internal_id", str(uuid.uuid4()))

    if not all(f in trade_signal for f in REQUIRED_FIELDS):
        logger.warning(f"Incomplete trade signal, skipping: {trade_signal}")
        return

    symbol = trade_signal["symbol"]
    side = trade_signal["side"]
    order_type = trade_signal["type"]
    quantity = float(trade_signal["quantity"])
    price = float(trade_signal["price"]) if trade_signal.get("price") else None
    time_in_force = trade_signal.get("timeInForce", "GTC") if order_type == "LIMIT" else None

    if side not in VALID_SIDES:
        logger.warning(f"Invalid side '{side}', must be one of {VALID_SIDES}, skipping: {trade_signal}")
        return

    # Both checks must pass before committing any state
    if not check_cooldown(symbol) or not check_risk(symbol, side, quantity):
        producer.send(BLOCKED_TOPIC, trade_signal)
        producer.flush()
        return

    last_trade_time[symbol] = time.time()
    positions[symbol] += quantity if side == "BUY" else -quantity

    binance_order = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
        "internal_id": trade_signal["internal_id"],
    }
    if order_type == "LIMIT":
        binance_order["price"] = price
        binance_order["timeInForce"] = time_in_force

    producer.send(APPROVED_TOPIC, binance_order)
    producer.flush()
    logger.info(f"Trade APPROVED and forwarded to execution-service: {binance_order}")

# ----------------------------
# Main loop
# ----------------------------
logger.info("Kill-switch service started, waiting for trade signals...")
for msg in consumer:
    try:
        process_trade_signal(msg.value)
    except Exception as e:
        logger.error(f"Unhandled error processing message: {e}", exc_info=True)
