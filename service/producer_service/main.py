import time
import json
from kafka import KafkaProducer, KafkaConsumer
import socket
import random
import uuid

time.sleep(15)

# Wait for Kafka to be reachable
host = "kafka"
port = 9092
while True:
    try:
        s = socket.socket()
        s.connect((host, port))
        s.close()
        print("Kafka is reachable!", flush=True)
        break
    except Exception:
        print("Waiting for Kafka...", flush=True)
        time.sleep(2)


producer = KafkaProducer(bootstrap_servers='kafka:9092')
consumer = KafkaConsumer(
    'market_data',
    bootstrap_servers='kafka:9092',
    value_deserializer=lambda m: json.loads(m.decode())
)

# Store latest market price
latest_mid_price = None

def get_latest_mid():
    global latest_mid_price
    return latest_mid_price if latest_mid_price is not None else 26000  # fallback default

# Background consumer to update latest market price
def update_market_price():
    global latest_mid_price
    for msg in consumer:
        market_data = msg.value
        if market_data.get('symbol') == 'BTCUSDT':
            latest_mid_price = market_data.get('mid')

import threading
threading.Thread(target=update_market_price, daemon=True).start()

print("Producer container started, generating trade signals...")

while True:
    # Generate trade signal using latest mid price
    mid_price = get_latest_mid()  # pull from market-data-service
    quantity = 0.01

    trade_order = {
        "symbol": "BTCUSDT",
        "side": random.choice(["BUY", "SELL"]),
        "type": "LIMIT",                    # or "MARKET"
        "timeInForce": "GTC",               # only needed for LIMIT
        "quantity": f"{quantity:.7f}",      # string with correct precision
        "price": f"{mid_price:.2f}",        # string rounded to tick size
        "internal_id": str(uuid.uuid4())
    }

    producer.send('trade_signal', json.dumps(trade_order).encode())
    producer.flush()
    print(f"Trade signal sent! {trade_order}")
    time.sleep(5)