import asyncio
import json
from aiokafka import AIOKafkaConsumer
from app.repositories.payment_repository import PaymentRepository
from app.kafka_logger import get_kafka_logger
from app.services.payment_producer import PaymentProducer
import os

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
logger = get_kafka_logger(__name__, KAFKA_BROKER, "logs.payment-service")
print(f"KAFKA_BROKER in consumer: {KAFKA_BROKER}")

class PaymentConsumer:
    def __init__(self, db_session, payment_service=None):
        self.payment_service = payment_service
        self.db_session = db_session
        self.payment_producer = PaymentProducer()
        self.payment_repo = PaymentRepository(db_session)
        self.consumer = None
        self._running_task = None
        self._stopped = asyncio.Event()

    async def start(self):
        print("PaymentConsumer.start() called")  # Add this line
        self.consumer = AIOKafkaConsumer(
            "payment-events",
            bootstrap_servers=KAFKA_BROKER,
            group_id="payment-service-main",  # Use a unique group ID
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest"
        )
        await self.consumer.start()
        print("AIOKafkaConsumer started")  # Add this line
        logger.info("PaymentConsumer started and listening to topic: payment-events")
        try:
            async for msg in self.consumer:
                try:
                    event = msg.value
                    logger.info(f"Received event on payment-events: {event}")
                    event_type = event.get("event")
                    if event_type == "create_payment":
                        await self.handle_create_payment_event(event)
                    elif event_type == "update_payment_order_id_requested":
                        await self.handle_update_payment_order_id_event(event)
                    else:
                        logger.warning(f"Unknown event type {event_type} for event: {event}")
                    if self._stopped.is_set():
                        break
                except Exception as e:
                    print(f"Exception in event processing: {e}")
                    logger.error(f"Exception in event processing: {e}", exc_info=True)
        finally:
            await self.consumer.stop()
            logger.info("PaymentConsumer stopped.")

    async def stop(self):
        logger.info("Stopping PaymentConsumer...")
        self._stopped.set()
        if self.consumer:
            await self.consumer.stop()

    async def handle_create_payment_event(self, event: dict):
        """
        Handles create_payment events from Kafka.
        event = {
            'order_id': int,
            'amount': float,
            'payment_info': dict,
            'user_id': int,
            ...
        }
        """
        try:
            logger.info(f"Processing create_payment event: {event}")
            # 1. Create payment in DB
            payment = await self.payment_repo.create_payment({
                'order_id': event['order_id'],
                'amount': event['amount'],
                'card_number': event['payment_info'].get('card_number'),
                'card_holder_name': event['payment_info'].get('card_holder_name'),
                'expiry_date': event['payment_info'].get('expiry_date'),
                'cvv': event['payment_info'].get('cvv'),
            })
            # 2. Publish payment_completed event
            status = 'SUCCESSFUL' if payment.status.name.upper() == 'SUCCESSFUL' else 'FAILED'
            await self.payment_producer.send_payment_completed_event(
                order_id=payment.order_id,
                status=status,
                payment_id=payment.id,
                user_id=event.get('user_id')
            )
            logger.info(f"Payment processed and payment_completed event published for order {payment.order_id}")
        except Exception as e:
            logger.error(f"Error processing create_payment event: {e}")
            # Optionally, publish a failed payment_completed event
            await self.payment_producer.send_payment_completed_event(
                order_id=event.get('order_id'),
                status='FAILED',
                payment_id=None,
                user_id=event.get('user_id')
            )

    async def handle_update_payment_order_id_event(self, event: dict):
        """
        Handles update_payment_order_id_requested events from Kafka.
        event = {
            'payment_id': int,
            'order_id': int
        }
        """
        try:
            logger.info(f"Processing update_payment_order_id_requested event: {event}")
            payment_id = event.get('payment_id')
            order_id = event.get('order_id')
            if payment_id is None or order_id is None:
                logger.error(f"Missing payment_id or order_id in event: {event}")
                return
            self.payment_repo.update_payment_order_id(payment_id, order_id)
            logger.info(f"Updated payment {payment_id} with new order_id {order_id}")
            # Optionally, publish a payment_updated event here if needed
        except Exception as e:
            logger.error(f"Error processing update_payment_order_id_requested event: {e}")

# Usage example (to be run in your app's startup):
# from app.db.database import get_db
# from app.services.payment_service import PaymentService
# import asyncio
# db = next(get_db())
# payment_service = PaymentService(db)
# consumer = PaymentConsumer(db, payment_service)
# asyncio.create_task(consumer.start())
