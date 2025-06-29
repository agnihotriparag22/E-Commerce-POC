import os
import json
import logging
from app.services.rest_proxy import RestProxyService
from app.kafka_logger import get_kafka_logger

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
logger = get_kafka_logger(__name__, KAFKA_BROKER, "logs.payment-service")

class PaymentProducer: 
    def __init__(self):
        self.rest_proxy = RestProxyService()
        

    async def send_payment_completed_event(self, order_id, status, payment_id=None, user_id=None):
        event = {
            "event": "payment_completed",
            "order_id": order_id,
            "status": status,
            "payment_id": payment_id,
            "user_id": user_id
        }
        try:
            logger.info(f"Publishing payment_completed event: {event}")
            await self.rest_proxy.send_event(event, topic="order-events")
            logger.info(f"payment_completed event sent successfully for order_id={order_id}")
        except Exception as e:
            logger.error(f"Failed to send payment_completed event for order_id={order_id}: {e}", exc_info=True)
            raise


