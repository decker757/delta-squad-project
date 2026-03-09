import json
import logging
from typing import Iterator, Dict, Any

from confluent_kafka import Consumer, KafkaError

class KafkaConsumer:
    def __init__(self, bootstrap_servers: str, group_id: str, topic: list[str], logger: logging.Logger):
        self.logger = logger
        self._consumer = Consumer({
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest"
        })
        self._consumer.subscribe(topic)
        self._stopped = False
    
    def stream(self) -> Iterator[Dict[str, Any]]:
        while not self._stopped:
            msg = self._consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                self.logger.error("Consumer error: %s", msg.error())
                continue
            try:
                yield json.loads(msg.value().decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                self.logger.warning("Malformed message, skipping: %s", e)
                continue

    def stop(self) -> None:
        self._stopped = True
    
    def close(self) -> None:
        self._consumer.close()