from pydantic import BaseModel, Field
from typing import Optional
from app.models.order import OrderStatus

class OrderBase(BaseModel):
    product_id: str = Field(..., description="ID of the product to order")
    quantity: int = Field(..., gt=0, description="Quantity of the product to order")

class OrderCreate(OrderBase):
    user_id: int = Field(..., gt=0, description="ID of the user placing the order")

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None

class OrderResponse(OrderBase):
    id: int
    user_id: int
    status: OrderStatus

    class Config:
        from_attributes = True

class OrderList(BaseModel):
    orders: list[OrderResponse]
    total: int 