from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.sql import func
from app.db.base import Base
import enum

class PaymentStatus(enum.Enum):
    SUCCESSFUL = "successful"
    FAILED = "failed"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    card_number = Column(String(16), nullable=False)
    card_holder_name = Column(String(100), nullable=False)
    expiry_date = Column(String(5), nullable=False)
    hashed_cvv = Column(String(60), nullable=False)  # bcrypt hash is always 60 characters
    status = Column(Enum(PaymentStatus), default=PaymentStatus.SUCCESSFUL, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 