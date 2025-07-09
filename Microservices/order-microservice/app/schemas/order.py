from pydantic import BaseModel, Field
from typing import Optional, List
from app.models.order import OrderStatus

class PaymentInfo(BaseModel):
    amount: float = Field(..., description="Payment amount")
    card_holder_name: str = Field(..., description="Card holder name")
    card_number: str = Field(..., description="Card number")
    cvv: str = Field(..., description="CVV")
    expiry_date: str = Field(..., description="Expiry date")

class OrderItemBase(BaseModel):
    product_id: int = Field(..., description="ID of the product to order")
    quantity: int = Field(..., gt=0, description="Quantity of the product to order")

class OrderItemCreate(OrderItemBase):
    pass

# Response schema for order items (only product_id and quantity, no id)
class OrderItemResponse(BaseModel):
    product_id: int
    quantity: int
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    user_id: int = Field(..., gt=0, description="ID of the user placing the order")
    items: List[OrderItemCreate] = Field(..., description="List of items in the order")
    payment_info: PaymentInfo = Field(..., description="Payment information")

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None

class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: OrderStatus
    items: List[OrderItemResponse]
    class Config:
        from_attributes = True

class OrdersSummaryResponse(BaseModel):
    total_orders: int
    total_customers: int
    unique_customers: int

class OrderList(BaseModel):
    orders: List[OrderResponse]
    total: int 

class OrderWithTotal(OrderResponse):
    total: float = 0.0