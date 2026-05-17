import json
import os
import signal
import sys

import structlog
from kafka import KafkaConsumer

from app.core.logging import setup_logging


def run_consumer(bootstrap_servers: str, topic: str, group_id: str = "fastapi-auth-group"):
    logger = structlog.get_logger()
    processed_event_ids: set[str] = set()

    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )

    logger.info("kafka_consumer_started", topic=topic, bootstrap_servers=bootstrap_servers)

    def _signal_handler(sig, frame):
        logger.info("shutting_down_consumer")
        try:
            consumer.close()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    for message in consumer:
        try:
            event = json.loads(message.value.decode("utf-8"))
            event_id = event.get("event_id")

            if event_id in processed_event_ids:
                logger.info("duplicate_event_skipped", event_id=event_id, partition=message.partition, offset=message.offset)
                consumer.commit()
                continue

            logger.info("consumed_event", value=event, partition=message.partition, offset=message.offset)

            if event_id:
                processed_event_ids.add(event_id)

            consumer.commit()
            logger.info("offset_committed", partition=message.partition, offset=message.offset)
        except json.JSONDecodeError as exc:
            logger.error("invalid_json_event", error=str(exc), raw=message.value.decode("utf-8", errors="replace"))
            consumer.commit()
        except Exception as exc:
            logger.error("consumer_processing_error", error=str(exc), raw=message.value.decode("utf-8", errors="replace"))


if __name__ == "__main__":
    setup_logging()
    bootstrap = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC", "user_events")
    group = os.getenv("KAFKA_CONSUMER_GROUP", "fastapi-auth-group")

    run_consumer(bootstrap, topic, group)
