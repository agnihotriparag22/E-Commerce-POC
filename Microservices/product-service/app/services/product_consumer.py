import asyncio
import json
from aiokafka import AIOKafkaConsumer
from app.kafka_logger import get_kafka_logger
from app.services.product_service import ProductService
import os

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
logger = get_kafka_logger(__name__, KAFKA_BROKER, "logs.product-service")

class ProductConsumer:
    def __init__(self, db_session):
        self.product_service = ProductService(db_session)

    async def start(self):
        consumer = AIOKafkaConsumer(
            "product-events",
            bootstrap_servers=KAFKA_BROKER,
            group_id="product-service",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest"
        )
        await consumer.start()
        logger.info("ProductConsumer started and listening to topic: product-events")
        try:
            async for msg in consumer:
                event = msg.value
                event_type = event.get("event")
                logger.info(f"Received event on product-events: {event}")
                if event_type == "update_stock":
                    await self.handle_update_stock_event(event)
                else:
                    logger.warning(f"Unknown event type {event_type} for event: {event}")
        finally:
            await consumer.stop()

    async def handle_update_stock_event(self, event: dict):
        """
        Handles update_stock events from Kafka.
        event = {
            'product_id': int,
            'quantity': int,
            'increase': bool,
            'reason': str,
            'order_id': int
        }
        """
        try:
            logger.info(f"Processing update_stock event: {event}")
            product_id = event.get('product_id')
            quantity = event.get('quantity')
            increase = event.get('increase', False)
            
            await self.product_service.update_stock(product_id, quantity, increase)
            logger.info(f"Stock updated for product {product_id}, quantity {quantity}, increase={increase}")
           
        except Exception as e:
            logger.error(f"Error processing update_stock event: {e}")


