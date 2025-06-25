from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.services.order_service import OrderService
from app.schemas.order import OrderCreate, OrderResponse, OrderUpdate, OrderList, OrderWithTotal
from app.core.auth import get_current_user
from app.core.auth import verify_token
import httpx
import os
from app.kafka_logger import get_kafka_logger

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = 'logs.order-service'  
logger = get_kafka_logger(__name__, KAFKA_BROKER, KAFKA_TOPIC)

router = APIRouter(
    prefix="/api/v1",
    tags=["orders"]
)

@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new order.
    Requires authentication and valid product stock.
    """
    if current_user["id"] != order_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create order for another user"
        )

    order_service = OrderService(db)
    try:
        order = await order_service.create_order(order_data, current_user["token"])
        return order
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get order details by ID.
    Users can only view their own orders.
    """
    order_service = OrderService(db)
    order = order_service.get_order(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order"
        )
    
    return order

@router.get("/orders/user/{user_id}", response_model=OrderList)
async def get_user_orders(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all orders for a specific user.
    Users can only view their own orders.
    """
    if current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these orders"
        )

    order_service = OrderService(db)
    orders = order_service.get_orders_by_user(user_id)
    return OrderList(orders=orders, total=len(orders))

@router.get("/orders", response_model=List[OrderWithTotal])
async def get_all_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all orders with payment totals (admin only).
    """
    # Todo: Add admin role check
    order_service = OrderService(db)
    orders = order_service.get_all_orders()
    
    # Fetch payment data for each order
    orders_with_totals = []
    
    async with httpx.AsyncClient() as client:
        for order in orders:
            try:
                # Call payment microservice to get payments for this order
                payment_response = await client.get(
                    f"http://payment-service/payments/order/{order.id}",
                    headers={"Authorization": f"Bearer {current_user['token']}"}
                )
                
                total = 0
                if payment_response.status_code == 200:
                    payments = payment_response.json()
                    # Sum successful payments for this order
                    total = sum(
                        payment.get('amount', 0) 
                        for payment in payments 
                        if payment.get('status') == 'SUCCESSFUL'
                    )
                
                # Create order with total
                order_dict = {
                    "id": order.id,
                    "user_id": order.user_id,
                    "product_id": order.product_id,
                    "quantity": order.quantity,
                    "status": order.status,
                    "created_at": order.created_at,
                    "updated_at": order.updated_at,
                    "total": total
                }
                orders_with_totals.append(order_dict)
                
            except Exception as e:
                logger.error(f"Error fetching payments for order {order.id}: {e}")
                # Add order with 0 total if payment fetch fails
                order_dict = {
                    "id": order.id,
                    "user_id": order.user_id,
                    "product_id": order.product_id,
                    "quantity": order.quantity,
                    "status": order.status,
                    "created_at": order.created_at,
                    "updated_at": order.updated_at,
                    "total": 0
                }
                orders_with_totals.append(order_dict)
    
    return orders_with_totals

@router.post("/orders/{order_id}/complete", response_model=OrderResponse)
async def complete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Complete an order after payment verification.
    """
    order_service = OrderService(db)
    try:
        order = await order_service.complete_order(order_id, current_user["token"])
        return order
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/orders/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Cancel an order.
    Users can only cancel their own orders.
    """
    order_service = OrderService(db)
    order = order_service.get_order(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this order"
        )
    
    try:
        order = await order_service.cancel_order(order_id, current_user["token"])
        return order
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.patch("/orders/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update order status (admin only).
    """
    # TODO: Add admin role check
    order_service = OrderService(db)
    order = order_service.update_order_status(order_id, order_update.status)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order