from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.services.order_service import OrderService
from app.schemas.order import OrderCreate, OrderResponse, OrderUpdate, OrderList, OrderWithTotal, OrdersSummaryResponse, OrderItemResponse
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

@router.get("/orders")
async def get_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    order_service = OrderService(db)
    orders = order_service.get_all_orders()
    response = []
    for order in orders:
        items = [OrderItemResponse(product_id=item.product_id, quantity=item.quantity) for item in order.items]
        response.append(OrderResponse(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            items=items
        ))
    return response

@router.get("/orders/summary", response_model=OrdersSummaryResponse)
async def get_orders_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get summary statistics: total number of orders, total customers, and unique customers.
    """
    
    order_service = OrderService(db)
    
    orders = order_service.get_all_orders()
  
    total_orders = len(orders)
    user_ids = [order.user_id for order in orders]
    unique_customers = len(set(user_ids))

    return {
    "total_orders": total_orders,
    "total_customers": len(user_ids),
    "unique_customers": unique_customers
    }

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
        items = [OrderItemResponse(product_id=item.product_id, quantity=item.quantity) for item in order.items]
        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            items=items
        )
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
    items = [OrderItemResponse(product_id=item.product_id, quantity=item.quantity) for item in order.items]
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        items=items
    )

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
    order_list = []
    for order in orders:
        items = [OrderItemResponse(product_id=item.product_id, quantity=item.quantity) for item in order.items]
        order_list.append(OrderResponse(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            items=items
        ))
    return OrderList(orders=order_list, total=len(order_list))

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