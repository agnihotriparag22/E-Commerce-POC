import asyncio
import json
from aiokafka import AIOKafkaConsumer
from app.services.order_service import OrderService
from app.db.database import get_db
from app.kafka_logger import get_kafka_logger
import os

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
logger = get_kafka_logger(__name__, KAFKA_BROKER, "logs.order-service")

class OrderConsumer:
    def __init__(self, db_session):
        self.order_service = OrderService(db_session)

    async def start(self):
        consumer = AIOKafkaConsumer(
            "order-events",
            bootstrap_servers=KAFKA_BROKER,
            group_id="order-service",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest"
        )
        await consumer.start()
        logger.info("OrderConsumer started and listening to topic: order-events")
        try:
            async for msg in consumer:
                event = msg.value
                event_type = event.get("event")
                logger.info(f"Received event on order-events: {event}")
                if event_type == "payment_completed":
                    await self.order_service.handle_payment_completed_event(event)
                elif event_type == "stock_updated":
                    await self.order_service.handle_stock_updated_event(event)
                else:
                    logger.warning(f"Unknown event type {event_type} for event: {event}")
        finally:
            await consumer.stop()

