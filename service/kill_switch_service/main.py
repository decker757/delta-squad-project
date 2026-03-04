import json
import time
import logging
import uuid
from kafka import KafkaConsumer, KafkaProducer, errors

# ----------------------------
# INITIAL SETUP
# ----------------------------
time.sleep(15)  # wait for Kafka to spin up

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kill-switch-service")

# Kafka broker
KAFKA_BROKER = "kafka:9092"

# Wait until Kafka is reachable
while True:
    try:
        test_producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER)
        test_producer.close()
        logger.info("Kafka is reachable!")
        break
    except errors.NoBrokersAvailable:
        logger.info("Waiting for Kafka...")
        time.sleep(10)

# Kafka topics
TRADE_SIGNAL_TOPIC = "trade_signal"
APPROVED_TOPIC = "approved_order"
BLOCKED_TOPIC = "blocked_order"

# Kafka consumer
consumer = KafkaConsumer(
    TRADE_SIGNAL_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
)

# Kafka producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# ----------------------------
# KILL-SWITCH CONFIG
# ----------------------------
positions = {"BTCUSDT": 0.0}  # example positions
last_trade_time = {}
COOLDOWN_SECONDS = 3  # prevent too-frequent trades
MAX_POSITION = 1.0    # max allowed position per symbol

# ----------------------------
# RISK & COOLDOWN CHECKS
# ----------------------------
def check_risk(symbol: str, side: str, quantity: float) -> bool:
    new_pos = positions[symbol] + quantity if side == "BUY" else positions[symbol] - quantity
    if abs(new_pos) > MAX_POSITION:
        logger.warning(f"Trade BLOCKED due to position limit: {symbol} {side} {quantity}")
        return False
    return True

def check_cooldown(symbol: str) -> bool:
    now = time.time()
    last = last_trade_time.get(symbol, 0)
    elapsed = now - last
    if elapsed < COOLDOWN_SECONDS:
        remaining = COOLDOWN_SECONDS - elapsed
        logger.info(f"Trade BLOCKED due to cooldown ({remaining:.3f} sec remaining)")
        return False
    last_trade_time[symbol] = now
    return True

# ----------------------------
# PROCESS TRADE SIGNAL
# ----------------------------
def process_trade_signal(trade_signal: dict):
    # Assign internal_id if missing
    if "internal_id" not in trade_signal:
        trade_signal["internal_id"] = str(uuid.uuid4())

    # Required fields
    required_fields = ["internal_id", "symbol", "side", "quantity", "type"]
    for f in required_fields:
        if f not in trade_signal:
            logger.warning(f"Incomplete trade signal, skipping: {trade_signal}")
            return

    # Extract & normalize fields
    symbol = trade_signal["symbol"]
    side = trade_signal["side"]
    order_type = trade_signal["type"]
    quantity = float(trade_signal["quantity"])
    price = float(trade_signal["price"]) if trade_signal.get("price") else None
    time_in_force = trade_signal.get("timeInForce", "GTC") if order_type == "LIMIT" else None

    # Cooldown & risk checks
    if not check_cooldown(symbol) or not check_risk(symbol, side, quantity):
        # Forward blocked trades
        producer.send(BLOCKED_TOPIC, trade_signal)
        return

    # Update positions
    positions[symbol] = positions[symbol] + quantity if side == "BUY" else positions[symbol] - quantity

    # Construct Binance-ready trade
    binance_order = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
        "internal_id": trade_signal["internal_id"]
    }

    if order_type == "LIMIT":
        binance_order["price"] = price
        binance_order["timeInForce"] = time_in_force

    # Log approval
    logger.info(f"Trade APPROVED: {binance_order}")

    # Forward to execution-service
    forward_to_execution(binance_order)

# ----------------------------
# FORWARD TO EXECUTION-SERVICE
# ----------------------------
def forward_to_execution(trade: dict):
    producer.send(APPROVED_TOPIC, trade)
    logger.info(f"Forwarded trade to execution-service: {trade}")

# ----------------------------
# MAIN LOOP
# ----------------------------
logger.info("Kill-switch service started, waiting for trade signals...")
for msg in consumer:
    raw_signal = msg.value
    process_trade_signal(raw_signal)