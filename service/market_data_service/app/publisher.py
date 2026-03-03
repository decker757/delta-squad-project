import json
import logging
from typing import Any, Dict

from confluent_kafka import Producer

class KafkaPublisher:
    def __init__(self, bootstrap_servers: str, logger: logging.Logger):
        self.logger = logger
        self.producer = Producer({
            "bootstrap.servers": bootstrap_servers,
        })
    
    def _delivery_callback(self, err, msg) -> None:
        if err is not None:
            self.logger.error("Kafka delivery failed: %s", err)
        else:
            self.logger.debug(
                "Kafka delivered topic=%s partition=%s offset=%s",
                msg.topic(),
                msg.partition(),
                msg.offset()
            )
    
    def publish(self, topic: str, payload: Dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")

        self.producer.poll(0)

        self.producer.produce(
            topic=topic,
            value=data,
            callback=self._delivery_callback,
        )

    def close(self) -> None:
        self.producer.flush()