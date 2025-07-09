from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
import re

class PaymentBase(BaseModel):
    order_id: int
    amount: float
    card_number: str
    card_holder_name: str
    expiry_date: str
    cvv: str  # This is for input only, will be hashed before storage

    @validator('card_number')
    def validate_card_number(cls, v):
        if not re.match(r'^\d{16}$', v):
            raise ValueError('Card number must be exactly 16 digits')
        return v

    @validator('expiry_date')
    def validate_expiry_date(cls, v):
        if not re.match(r'^(0[1-9]|1[0-2])/([0-9]{2})$', v):
            raise ValueError('Expiry date must be in MM/YY format')
        return v

    @validator('cvv')
    def validate_cvv(cls, v):
        if not re.match(r'^\d{3}$', v):
            raise ValueError('CVV must be exactly 3 digits')
        return v

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    amount: float
    card_number: str
    card_holder_name: str
    expiry_date: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 