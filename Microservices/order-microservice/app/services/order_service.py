from sqlalchemy.orm import Session
import httpx
import os
import json
from typing import Optional, Dict, Any
from app.models.order import Order, OrderStatus
from app.services.rest_proxy import RestProxyService
from app.schemas.schema_registry import SchemaRegistryService

from app.schemas.order import OrderCreate, OrderUpdate
from app.db.database import get_db
from app.kafka_logger import get_kafka_logger

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = 'logs.order-service'  
logger = get_kafka_logger(__name__, KAFKA_BROKER, KAFKA_TOPIC)

# ---
# HTTP REST: Synchronous, request/response operations
# ---
class ProductService:
    def __init__(self):
        self.base_url = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8002")

    async def get_product(self, product_id: str, auth_token: str) -> Dict[str, Any]:
        # HTTP REST: Synchronous call to Product Service
        logger.debug(f"Fetching product {product_id} from Product Service")
        async with httpx.AsyncClient() as client:
            try:
                headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
                response = await client.get(
                    f"{self.base_url}/api/v1/products/{product_id}",
                    headers=headers
                )
                logger.debug(f"Product Service response for {product_id}: status={response.status_code}, body={response.text}")
                if response.status_code == 200:
                    return response.json()
                logger.error(f"Failed to get product {product_id}: {response.text}")
                raise Exception("Product not found")
            except Exception as e:
                logger.error(f"Error getting product {product_id}: {e}")
                raise

    async def check_stock(self, product_id: str, quantity: int, auth_token: str) -> bool:
        
        logger.debug(f"Checking stock for product {product_id} with quantity {quantity}")
        product = await self.get_product(product_id, auth_token)
        logger.debug(f"Product {product_id} stock: {product.get('stock', 0)}")
        return product.get("stock", 0) >= quantity


class PaymentService:
    def __init__(self):
        self.base_url = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8003")
        self.rest_proxy = RestProxyService()
        self.schema_registry = SchemaRegistryService(subject="payment-events-value")
        self.payment_event_schema = {
            "type": "record",
            "name": "PaymentEvent",
            "fields": [
                {"name": "event", "type": "string"},
                {"name": "order_id", "type": "int"},
                {"name": "amount", "type": "double"},
                {
                    "name": "payment_info",
                    "type": {
                        "type": "record",
                        "name": "PaymentInfo",
                        "fields": [
                            {"name": "card_holder_name", "type": ["null", "string"], "default": None},
                            {"name": "card_number_masked", "type": ["null", "string"], "default": None},
                            {"name": "expiry_date", "type": ["null", "string"], "default": None},
                            {"name": "cvv", "type": "string", "default": None}
                        ]
                    }
                },
                {"name": "payment_id", "type": ["null", "string"], "default": None},
                {"name": "status", "type": ["null", "string"], "default": None}
            ]
        }

    async def async_init(self):
        schema_json = json.dumps(self.payment_event_schema)
        result = await self.schema_registry.register_schema(schema_json)
        logger.info(f"Payment Schema registered successfully: {result}")
        

    async def create_payment(self, order_id: int, amount: float, payment_info: Dict[str, Any], auth_token: str) -> Dict[str, Any]:
        logger.debug(f"Creating payment for order {order_id} with amount {amount}")
        async with httpx.AsyncClient(timeout=30.0) as client:  
            try:
                headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
                response = await client.post(
                    f"{self.base_url}/api/v1/payments/",
                    json={
                        "order_id": order_id,
                        "amount": amount,
                        "card_number": payment_info.get("card_number"),
                        "card_holder_name": payment_info.get("card_holder_name", "Test User"),
                        "expiry_date": payment_info.get("expiry_date"),
                        "cvv": payment_info.get("cvv")
                    },
                    headers=headers
                )
                logger.debug(f"Payment Service response for order {order_id}: status={response.status_code}, body={response.text}")
                if response.status_code == 200:
                    await self.rest_proxy.send_event({
                        "event": "payment_initiated",
                        "order_id": order_id,
                        "amount": amount,
                        "payment_info": payment_info,
                    }, auth_token=auth_token, topic="payment-events")
                    return response.json()
                logger.error(f"Payment creation failed: {response.text}")
                raise Exception(f"Payment creation failed: {response.text}")
            except Exception as e:
                logger.error("Error creating payment", exc_info=True)
                raise Exception(f"Error creating payment: {e}") from e

    async def verify_payment(self, payment_id: int, auth_token: str) -> bool:
        logger.debug(f"Verifying payment {payment_id}")
        async with httpx.AsyncClient() as client:
            try:
                headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
                response = await client.get(
                    f"{self.base_url}/api/v1/payments/{payment_id}",
                    headers=headers
                )
                logger.debug(f"Payment verification response for payment {payment_id}: status={response.status_code}, body={response.text}")
                if response.status_code == 200:
                    payment_data = response.json()
                    
                    # Rest proxy implementation for payment verification
                    await self.rest_proxy.send_event({
                        "event": "payment_verified",
                        "payment_id": payment_id
                    },auth_token=auth_token, topic="payment-events")
                     
                    # Handle both cases: "SUCCESSFUL" and "successful"
                    return payment_data.get("status", "").upper() == "SUCCESSFUL"
                return False
            except Exception as e:
                logger.error(f"Error verifying payment: {e}")
                return False

    async def update_payment_order_id(self, payment_id: int, order_id: int, auth_token: str) -> None:
        logger.debug(f"Requesting update of payment {payment_id} with order {order_id} via event")
        # Instead of making a REST call, publish an event for the Payment Service to consume
        await self.rest_proxy.send_event({
            "event": "update_payment_order_id_requested",
            "payment_id": payment_id,
            "order_id": order_id
        }, auth_token=auth_token, topic="payment-events")
        logger.info(f"Published update_payment_order_id_requested event for payment {payment_id} and order {order_id}")
        # The Payment Service should consume this event and perform the update

class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.product_service = ProductService()
        self.payment_service = PaymentService()
        self.rest_proxy = RestProxyService()
        self.schema_registry = SchemaRegistryService(subject="order-events-value")
        self.order_event_schema = {
            "type": "record",
            "name": "OrderEvent",
            "fields": [
                {"name": "event", "type": "string"},
                {"name": "order_id", "type": "int"},
                {"name": "user_id", "type": "int"},
                {"name": "product_id", "type": "int"},
                {"name": "quantity", "type": "int"},
                {"name": "status", "type": "string"}
            ]
        }

    async def async_init(self):
        schema_json = json.dumps(self.order_event_schema)
        result = await self.schema_registry.register_schema(schema_json)
        logger.info(f"Order Schema registered successfully: {result}")

    async def create_order(self, order_data: OrderCreate, auth_token: str) -> Order:
        logger.info(f"Creating order: {order_data}")
        logger.info(f"Payment info received: {order_data.payment_info}")
        db_order = None
        try:
            # Step 1: Check stock availability (still synchronous)
            logger.debug(f"Checking stock for product {order_data.product_id} and quantity {order_data.quantity}")
            if not await self.product_service.check_stock(order_data.product_id, order_data.quantity, auth_token):
                logger.warning(f"Insufficient stock for product {order_data.product_id}")
                raise Exception("Insufficient stock")

            # Step 2: Get product details to calculate total amount (still synchronous)
            logger.debug(f"Fetching product details for product {order_data.product_id}")
            product = await self.product_service.get_product(order_data.product_id, auth_token)
            total_amount = product["price"] * order_data.quantity
            logger.debug(f"Calculated total amount for order: {total_amount}")

           
            frontend_amount = order_data.payment_info.amount if order_data.payment_info else None
            if frontend_amount and frontend_amount != total_amount:
                logger.warning(f"Payment amount mismatch: frontend={frontend_amount}, calculated={total_amount}")
               

            
            logger.debug("Adding order to database in PAYMENT_PENDING state")
            db_order = Order(
                user_id=order_data.user_id,
                product_id=order_data.product_id,
                quantity=order_data.quantity,
                status=OrderStatus.PENDING
            )
            self.db.add(db_order)
            self.db.commit()
            self.db.refresh(db_order)
            logger.info(f"Order created with ID: {db_order.id} in PAYMENT_PENDING state")

            # Step 5: Publish create_payment event to Kafka (async)
            payment_info_dict = {
                'amount': order_data.payment_info.amount,
                'card_holder_name': order_data.payment_info.card_holder_name,
                'card_number': order_data.payment_info.card_number,
                'cvv': order_data.payment_info.cvv,
                'expiry_date': order_data.payment_info.expiry_date
            } if order_data.payment_info else {}

            await self.rest_proxy.send_event({
                "event": "create_payment",
                "order_id": db_order.id,
                "amount": total_amount,
                "payment_info": payment_info_dict,
                "user_id": order_data.user_id
            }, auth_token=auth_token, topic="payment-events")

            
            await self.rest_proxy.send_event({
                "event": "order_created_pending_payment",
                "order_id": db_order.id,
                "user_id": order_data.user_id,
                "product_id": order_data.product_id,
                "quantity": order_data.quantity,
                "status": OrderStatus.PENDING.value
            }, auth_token=auth_token, topic="order-events")

            
            return db_order
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            if db_order and db_order.id:
                try:
                    logger.debug(f"Cleaning up order {db_order.id} due to error")
                    await self._delete_order(db_order.id)
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup order {db_order.id}: {cleanup_error}")
            raise

    async def _delete_order(self, order_id: int) -> None:
        """Private method to delete an order"""
        logger.debug(f"Attempting to delete order {order_id}")
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if order:
                self.db.delete(order)
                self.db.commit()
                
                
                await self.rest_proxy.send_event({
                "event": "order_deleted",
                "order_id": order_id
                }, auth_token=None, topic="order-events")
                
                logger.info(f"Order {order_id} deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting order {order_id}: {e}")
            self.db.rollback()
            raise

    async def cancel_order(self, order_id: int, auth_token: str) -> Order:
        logger.debug(f"Attempting to cancel order {order_id}")
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                logger.warning(f"Order {order_id} not found for cancellation")
                raise Exception("Order not found")

            if order.status == OrderStatus.COMPLETED:
                logger.warning(f"Attempt to cancel completed order {order_id}")
                raise Exception("Cannot cancel completed order")

          
            if order.status == OrderStatus.PENDING:
                logger.debug(f"Publishing stock return event for product {order.product_id} due to order {order_id} cancellation")
                await self.rest_proxy.send_event({
                    "event": "update_stock",
                    "product_id": order.product_id,
                    "quantity": order.quantity,
                    "increase": True,
                    "reason": "order_cancelled",
                    "order_id": order_id
                }, auth_token=auth_token, topic="product-events")

            order.status = OrderStatus.CANCELLED
            self.db.commit()
            
            await self.rest_proxy.send_event({
                "event": "order_cancelled",
                "order_id": order_id,
                "user_id": order.user_id,
                "product_id": order.product_id,
                "quantity": order.quantity,
                "status": OrderStatus.CANCELLED.value
            }, auth_token=auth_token, topic="order-events")
            self.db.refresh(order)
            logger.info(f"Order {order_id} cancelled successfully")
            return order
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            raise

    def get_orders_by_user(self, user_id: int):
        """Return all orders for a given user_id."""
        return self.db.query(Order).filter(Order.user_id == user_id).all()

    def get_order(self, order_id: int):
        """Return a single order by order_id."""
        return self.db.query(Order).filter(Order.id == order_id).first()

    def get_all_orders(self) -> list[Order]:
        logger.debug("Fetching all orders from database")
        return self.db.query(Order).all()
        
    async def handle_payment_completed_event(self, event: dict):
        logger.debug(f"Session id: {id(self.db)}")
        all_orders = self.db.query(Order).all()
        logger.debug(f"All order IDs in DB at event time: {[o.id for o in all_orders]}")
        order = self.get_order(event['order_id'])
        retry_count = 0
        while not order and retry_count < 3:
            logger.warning(f"Order {event['order_id']} not found, retrying in 0.5s (attempt {retry_count+1})")
            await asyncio.sleep(0.5)
            order = self.get_order(event['order_id'])
            retry_count += 1
        if not order:
            logger.error(f"Order {event['order_id']} not found for payment completion event after retries")
            return
        if event.get('status', '').upper() == 'SUCCESSFUL':
            order.status = OrderStatus.COMPLETED
            self.db.commit()
            self.db.refresh(order)
            logger.info(f"Order {order.id} marked as COMPLETED after payment success")
            # Publish event to reduce stock
            await self.rest_proxy.send_event({
                "event": "update_stock",
                "product_id": order.product_id,
                "quantity": order.quantity,
                "increase": False,
                "reason": "order_completed",
                "order_id": order.id
            }, auth_token=None, topic="product-events")
            # Optionally, publish order_completed event
            await self.rest_proxy.send_event({
                "event": "order_completed",
                "order_id": order.id,
                "user_id": order.user_id,
                "product_id": order.product_id,
                "quantity": order.quantity,
                "status": OrderStatus.COMPLETED.value
            }, auth_token=None, topic="order-events")
        else:
            
            await self._delete_order(order.id)
            logger.info(f"Order {order.id} deleted due to payment failure")

    
    async def handle_stock_updated_event(self, event: dict):
        
        if event.get('status', '').upper() == 'SUCCESSFUL':
            logger.info(f"Stock updated")
        else:
            logger.warning(f"Stock update failed ") 