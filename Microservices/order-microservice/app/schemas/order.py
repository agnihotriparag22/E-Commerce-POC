from pydantic import BaseModel, Field
from typing import Optional
from app.models.order import OrderStatus

class PaymentInfo(BaseModel):
    amount: float = Field(..., description="Payment amount")
    card_holder_name: str = Field(..., description="Card holder name")
    card_number: str = Field(..., description="Card number")
    cvv: str = Field(..., description="CVV")
    expiry_date: str = Field(..., description="Expiry date")
    
class OrderBase(BaseModel):
    product_id: str = Field(..., description="ID of the product to order")
    quantity: int = Field(..., gt=0, description="Quantity of the product to order")

class OrderCreate(OrderBase):
    user_id: int = Field(..., gt=0, description="ID of the user placing the order")
    payment_info: PaymentInfo = Field(..., description="Payment information")

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