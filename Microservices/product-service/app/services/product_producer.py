import os
import json
from app.services.rest_proxy import RestProxyService
from app.kafka_logger import get_kafka_logger

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
logger = get_kafka_logger(__name__, KAFKA_BROKER, "logs.product-service")

class ProductProducer:
    def __init__(self):
        self.rest_proxy = RestProxyService()

    async def send_stock_updated_event(self, product_id: int, order_id: int, status: str):
        event = {
            "event": "stock_updated",
            "product_id": product_id,
            "order_id": order_id,
            "status": status
        }
        await self.rest_proxy.send_event(event, topic="order-events")
        logger.info(f"Published stock_updated event: {event}")


