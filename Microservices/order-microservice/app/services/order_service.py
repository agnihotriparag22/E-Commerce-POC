from sqlalchemy.orm import Session
import httpx
import os
import json
import logging
from typing import Optional, Dict, Any
from app.models.order import Order, OrderStatus
from app.services.rest_proxy import RestProxyService
from app.schemas.schema_registry import SchemaRegistryService

from app.schemas.order import OrderCreate, OrderUpdate
from app.db.database import get_db

logger = logging.getLogger(__name__)

class ProductService:
    def __init__(self):
        self.base_url = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8002")

    async def get_product(self, product_id: str, auth_token: str) -> Dict[str, Any]:
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

    async def update_stock(self, product_id: str, quantity: int, auth_token: str, increase: bool = False) -> None:
        logger.debug(f"{'Increasing' if increase else 'Decreasing'} stock for product {product_id} by {quantity}")
        async with httpx.AsyncClient() as client:
            try:
                headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
                endpoint = f"{self.base_url}/api/v1/products/{product_id}/{'increase' if increase else 'decrease'}-stock"
                response = await client.post(
                    endpoint,
                    json={"quantity": quantity},
                    headers=headers
                )
                logger.debug(f"Stock update response for product {product_id}: status={response.status_code}, body={response.text}")
                if response.status_code != 200:
                    logger.error(f"Failed to update stock for product {product_id}: {response.text}")
                    raise Exception("Failed to update stock")
            except Exception as e:
                logger.error(f"Error updating stock for product {product_id}: {e}")
                raise

class PaymentService:
    def __init__(self):
        self.base_url = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8003")
        self.rest_proxy = RestProxyService()
        self.schema_registry = SchemaRegistryService( subject = "payment-events-value")
        payment_event_schema = {
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
                                    {"name": "card_number_masked", "type": ["null", "string"], "default": None},  # Only last 4 digits
                                    {"name": "expiry_date", "type": ["null", "string"], "default": None},
                                    {"name": "cvv", "type": "string", "default": None}
                                ]
                            }
                        },
                        {"name": "payment_id", "type": ["null", "string"], "default": None},
                        {"name": "status", "type": ["null", "string"], "default": None}
                    ]
                }
        
        schema_json = json.dumps(payment_event_schema)
        result = self.schema_registry.register_schema(schema_json)
        
        logger.info(f"Payment Schema registered successfully: {result}")
        

    async def create_payment(self, order_id: int, amount: float, payment_info: Dict[str, Any], auth_token: str) -> Dict[str, Any]:
        logger.debug(f"Creating payment for order {order_id} with amount {amount}")
        async with httpx.AsyncClient() as client:
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
                    
                    # Rest proxy implementation for payment creation
                    # await self.rest_proxy.send_event({
                    #         "event": "payment_initiated",
                    #         "order_id": order_id,
                    #         "amount": amount,
                    #         "payment_info": payment_info,
                    #         # "card_number": payment_info.card_number,
                    #         # "card_holder_name": payment_info.card_holder_name,
                    #         # "expiry_date": payment_info.expiry_date,
                    #         # "cvv": payment_info.cvv
                    #     }, auth_token=auth_token)
                    
                    return response.json()
                    
                logger.error(f"Payment creation failed: {response.text}")
                raise Exception("Payment creation failed")
            except Exception as e:
                logger.error(f"Error creating payment: {e}")
                raise

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
                    },auth_token=auth_token)
                     
                    # Handle both cases: "SUCCESSFUL" and "successful"
                    return payment_data.get("status", "").upper() == "SUCCESSFUL"
                return False
            except Exception as e:
                logger.error(f"Error verifying payment: {e}")
                return False

    async def update_payment_order_id(self, payment_id: int, order_id: int, auth_token: str) -> None:
        logger.debug(f"Updating payment {payment_id} with order {order_id}")
        async with httpx.AsyncClient() as client:
            try:
                headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
                response = await client.put(
                    f"{self.base_url}/api/v1/payments/{payment_id}/order/{order_id}",
                    headers=headers
                )
                logger.debug(f"Update payment order_id response: status={response.status_code}, body={response.text}")
                if response.status_code != 200:
                    logger.error(f"Failed to update payment {payment_id} with order {order_id}: {response.text}")
                    raise Exception("Failed to update payment")
                
                # Rest proxy implementation for payment update with order_id
                await self.rest_proxy.send_event({
                    "event": "payment_updated",
                    "payment_id": payment_id,
                    "order_id": order_id
                }, auth_token=auth_token)
                
            except Exception as e:
                logger.error(f"Error updating payment {payment_id} with order {order_id}: {e}")
                raise

class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.product_service = ProductService()
        self.payment_service = PaymentService()
        self.rest_proxy = RestProxyService()
        self.schema_registry = SchemaRegistryService(subject="order-events-value")
        order_event_schema = {
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
        schema_json = json.dumps(order_event_schema)
        result = self.schema_registry.register_schema(schema_json)
        
        logger.info(f"Order Schema registered successfully: {result}")

    async def create_order(self, order_data: OrderCreate, auth_token: str) -> Order:
        logger.info(f"Creating order: {order_data}")
        logger.info(f"Payment info received: {order_data.payment_info}")
        db_order = None
        
        try:
            # Step 1: Check stock availability
            logger.debug(f"Checking stock for product {order_data.product_id} and quantity {order_data.quantity}")
            if not await self.product_service.check_stock(order_data.product_id, order_data.quantity, auth_token):
                logger.warning(f"Insufficient stock for product {order_data.product_id}")
                raise Exception("Insufficient stock")

            # Step 2: Get product details to calculate total amount
            logger.debug(f"Fetching product details for product {order_data.product_id}")
            product = await self.product_service.get_product(order_data.product_id, auth_token)
            total_amount = product["price"] * order_data.quantity
            logger.debug(f"Calculated total amount for order: {total_amount}")

            # Step 3: Validate payment amount from frontend matches calculated amount
            frontend_amount = order_data.payment_info.amount if order_data.payment_info else None
                
            if frontend_amount and frontend_amount != total_amount:
                logger.warning(f"Payment amount mismatch: frontend={frontend_amount}, calculated={total_amount}")
                # You might want to use the calculated amount or raise an exception
                # For now, we'll use the calculated amount for security

            # Step 4: Create order in PENDING state first
            logger.debug("Adding order to database in PENDING state")
            db_order = Order(
                user_id=order_data.user_id,
                product_id=order_data.product_id,
                quantity=order_data.quantity,
                status=OrderStatus.PENDING
            )
            self.db.add(db_order)
            self.db.commit()

            #Rest Proxy implementation for order creation in Pending status
            await self.rest_proxy.send_event({
                    "event": "pending_order_created",
                    "order_id": db_order.id,
                    "user_id": order_data.user_id,
                    "product_id": order_data.product_id,
                    "quantity": order_data.quantity,
                    "status": OrderStatus.PENDING.value
            }, auth_token=auth_token)
            
            self.db.refresh(db_order)
            
            logger.info(f"Order created with ID: {db_order.id} in PENDING state")

            # Step 5: Process payment with the order_id
            try:
                # Convert payment_info to dict for the payment service
                payment_info_dict = {
                    'amount': order_data.payment_info.amount,
                    'card_holder_name': order_data.payment_info.card_holder_name,
                    'card_number': order_data.payment_info.card_number,
                    'cvv': order_data.payment_info.cvv,
                    'expiry_date': order_data.payment_info.expiry_date
                } if order_data.payment_info else {}
                
                logger.info(f"Payment info for order {db_order.id}: {payment_info_dict}")
                
                payment = await self.payment_service.create_payment(
                    order_id=db_order.id,
                    amount=total_amount,
                    payment_info=payment_info_dict,
                    auth_token=auth_token
                )
                
                logger.info(f"Payment response: {payment}")
                
                # Step 6: Check if payment was successful (handle both cases)
                payment_status = payment.get("status", "").upper() if payment else ""
                
                if payment and payment_status == "SUCCESSFUL":
                    # Payment successful - update order status to COMPLETED
                    logger.debug(f"Payment successful for order {db_order.id}, updating status to COMPLETED")
                    db_order.status = OrderStatus.COMPLETED
                    self.db.commit()
                    
                    #Rest Proxy implementation for order creation in completed status
                    await self.rest_proxy.send_event({
                        "event": "order_created",
                        "order_id": db_order.id,
                        "user_id": order_data.user_id,
                        "product_id": order_data.product_id,
                        "quantity": order_data.quantity,
                        "status": OrderStatus.COMPLETED.value
                    }, auth_token=auth_token)
                    
                    self.db.refresh(db_order)
                    
                    logger.info(f"Payment successful for order {db_order.id}, status updated to COMPLETED")
                    
                    # Step 7: Reduce stock after successful payment
                    logger.debug(f"Reducing stock for product {order_data.product_id} after successful payment")
                    await self.product_service.update_stock(
                        order_data.product_id,
                        order_data.quantity,
                        auth_token
                    )
                    
                    return db_order
                
                else:
                    # Payment failed - delete the order
                    logger.error(f"Payment failed for order {db_order.id}. Status: {payment_status}, Payment: {payment}")
                    await self._delete_order(db_order.id)
                    raise Exception(f"Payment failed with status: {payment_status}")

            except Exception as payment_error:
                logger.error(f"Payment processing failed for order {db_order.id}: {payment_error}")
                # Delete the order if payment fails
                if db_order:
                    await self._delete_order(db_order.id)
                raise Exception(f"Failed to process payment: {str(payment_error)}")

        except Exception as e:
            logger.error(f"Error creating order: {e}")
            # If order was created but something else failed, clean it up
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
                
                #Rest Proxy Implementation for order_deletion
                await self.rest_proxy.send_event({
                "event": "order_deleted",
                "order_id": order_id
                }, auth_token=None)
                
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

            # Return stock if order was pending
            if order.status == OrderStatus.PENDING:
                logger.debug(f"Returning stock for product {order.product_id} due to order {order_id} cancellation")
                await self.product_service.update_stock(
                    order.product_id,
                    order.quantity,
                    auth_token,
                    increase=True
                )

            order.status = OrderStatus.CANCELLED
            self.db.commit()
            
            #Rest Proxy Implementation for order_cancellation
            await self.rest_proxy.send_event({
                "event": "order_cancelled",
                "order_id": order_id
            }, auth_token=auth_token)
            
            self.db.refresh(order)
            logger.info(f"Order {order_id} cancelled successfully")
            return order
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            raise

    def get_order(self, order_id: int) -> Optional[Order]:
        logger.debug(f"Fetching order {order_id} from database")
        return self.db.query(Order).filter(Order.id == order_id).first()

    def get_orders_by_user(self, user_id: int) -> list[Order]:
        logger.debug(f"Fetching orders for user {user_id}")
        return self.db.query(Order).filter(Order.user_id == user_id).all()

    def get_all_orders(self) -> list[Order]:
        logger.debug("Fetching all orders from database")
        return self.db.query(Order).all()

    def update_order_status(self, order_id: int, status: OrderStatus) -> Optional[Order]:
        logger.debug(f"Updating status for order {order_id} to {status}")
        order = self.get_order(order_id)
        if order:
            order.status = status
            self.db.commit()
            self.db.refresh(order)
        return order