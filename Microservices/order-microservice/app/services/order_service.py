from sqlalchemy.orm import Session
import httpx
import os
import logging
from typing import Optional, Dict, Any
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate
from app.db.database import get_db

logger = logging.getLogger(__name__)

class ProductService:
    def __init__(self):
        self.base_url = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8002")

    async def get_product(self, product_id: str, auth_token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
                response = await client.get(
                    f"{self.base_url}/api/v1/products/{product_id}",
                    headers=headers
                )
                if response.status_code == 200:
                    return response.json()
                logger.error(f"Failed to get product {product_id}: {response.text}")
                raise Exception("Product not found")
            except Exception as e:
                logger.error(f"Error getting product {product_id}: {e}")
                raise

    async def check_stock(self, product_id: str, quantity: int, auth_token: str) -> bool:
        product = await self.get_product(product_id, auth_token)
        return product.get("stock", 0) >= quantity

    async def update_stock(self, product_id: str, quantity: int, auth_token: str, increase: bool = False) -> None:
        async with httpx.AsyncClient() as client:
            try:
                headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
                endpoint = f"{self.base_url}/api/v1/products/{product_id}/{'increase' if increase else 'decrease'}-stock"
                response = await client.post(
                    endpoint,
                    json={"quantity": quantity},
                    headers=headers
                )
                if response.status_code != 200:
                    logger.error(f"Failed to update stock for product {product_id}: {response.text}")
                    raise Exception("Failed to update stock")
            except Exception as e:
                logger.error(f"Error updating stock for product {product_id}: {e}")
                raise

class PaymentService:
    def __init__(self):
        self.base_url = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8003")

    async def create_payment(self, order_id: int, amount: float, auth_token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
                response = await client.post(
                    f"{self.base_url}/api/v1/payments/",
                    json={
                        "order_id": order_id,
                        "amount": amount,
                        "card_number": "4111111111111111",  # This should come from the request
                        "card_holder_name": "Test User",    # This should come from the request
                        "expiry_date": "12/25",            # This should come from the request
                        "cvv": "123"                       # This should come from the request
                    },
                    headers=headers
                )
                if response.status_code == 200:
                    return response.json()
                logger.error(f"Payment creation failed: {response.text}")
                raise Exception("Payment creation failed")
            except Exception as e:
                logger.error(f"Error creating payment: {e}")
                raise

    async def verify_payment(self, payment_id: int, auth_token: str) -> bool:
        async with httpx.AsyncClient() as client:
            try:
                headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
                response = await client.get(
                    f"{self.base_url}/api/v1/payments/{payment_id}",
                    headers=headers
                )
                if response.status_code == 200:
                    payment_data = response.json()
                    return payment_data.get("status") == "successful"
                return False
            except Exception as e:
                logger.error(f"Error verifying payment: {e}")
                return False

class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.product_service = ProductService()
        self.payment_service = PaymentService()

    async def create_order(self, order_data: OrderCreate, auth_token: str) -> Order:
        logger.info(f"Creating order: {order_data}")
        try:
            # Get product details and check stock
            if not await self.product_service.check_stock(order_data.product_id, order_data.quantity, auth_token):
                raise Exception("Insufficient stock")

            # Create order in pending state
            db_order = Order(
                user_id=order_data.user_id,
                product_id=order_data.product_id,
                quantity=order_data.quantity,
                status=OrderStatus.PENDING
            )
            self.db.add(db_order)
            self.db.commit()
            self.db.refresh(db_order)

            try:
                # Reduce stock
                await self.product_service.update_stock(
                    order_data.product_id,
                    order_data.quantity,
                    auth_token
                )

                # Update order status to completed
                db_order.status = OrderStatus.COMPLETED
                self.db.commit()
                self.db.refresh(db_order)

                return db_order
            except Exception as e:
                # If anything fails, revert stock and cancel order
                await self.product_service.update_stock(
                    order_data.product_id,
                    order_data.quantity,
                    auth_token,
                    increase=True
                )
                db_order.status = OrderStatus.CANCELLED
                self.db.commit()
                raise Exception(f"Order creation failed: {str(e)}")

        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise

    async def cancel_order(self, order_id: int, auth_token: str) -> Order:
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise Exception("Order not found")

            if order.status == OrderStatus.COMPLETED:
                raise Exception("Cannot cancel completed order")

            # Return stock if order was pending
            if order.status == OrderStatus.PENDING:
                await self.product_service.update_stock(
                    order.product_id,
                    order.quantity,
                    auth_token,
                    increase=True
                )

            order.status = OrderStatus.CANCELLED
            self.db.commit()
            self.db.refresh(order)
            return order
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            raise

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.db.query(Order).filter(Order.id == order_id).first()

    def get_orders_by_user(self, user_id: int) -> list[Order]:
        return self.db.query(Order).filter(Order.user_id == user_id).all()

    def get_all_orders(self) -> list[Order]:
        return self.db.query(Order).all()

    def update_order_status(self, order_id: int, status: OrderStatus) -> Optional[Order]:
        order = self.get_order(order_id)
        if order:
            order.status = status
            self.db.commit()
            self.db.refresh(order)
        return order 