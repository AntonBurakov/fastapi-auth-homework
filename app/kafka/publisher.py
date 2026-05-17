import json
import time
from typing import Any
from uuid import uuid4

import structlog
from kafka import KafkaProducer

from app.core.tracing import get_trace_id, trace_span


class KafkaPublisher:
    def __init__(self, bootstrap_servers: str = "localhost:9092", topic: str = "user_events"):
        self.logger = structlog.get_logger()
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer: KafkaProducer | None = None

    def _get_producer(self) -> KafkaProducer:
        if self.producer is None:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                key_serializer=lambda v: str(v).encode("utf-8"),
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                retries=5,
                acks="all",
                max_block_ms=3000,
            )

        return self.producer

    def publish_user_registered(self, user: Any) -> bool:
        kafka_event = {
            "event_id": str(uuid4()),
            "event_name": "user_registered",
            "user_id": user.id,
            "email": user.email,
            "trace_id": get_trace_id(),
        }

        with trace_span("kafka.publish_user_registered", topic=self.topic, user_id=user.id):
            attempts = 0
            while attempts < 3:
                try:
                    producer = self._get_producer()
                    fut = producer.send(self.topic, key=user.id, value=kafka_event)
                    fut.get(timeout=10)
                    self.logger.info("published_user_registered", kafka_event=kafka_event)
                    return True
                except Exception as exc:
                    attempts += 1
                    self.logger.error(
                        "publish_failed",
                        error=str(exc),
                        attempt=attempts,
                        kafka_event=kafka_event,
                    )
                    self.close()
                    time.sleep(1 * attempts)

            self.logger.warning(
                "giving_up_publishing_user_registered",
                kafka_event=kafka_event,
            )
            return False

    def close(self) -> None:
        if self.producer is None:
            return

        try:
            self.producer.flush(timeout=5)
            self.producer.close(timeout=5)
        except Exception:
            pass
        finally:
            self.producer = None
