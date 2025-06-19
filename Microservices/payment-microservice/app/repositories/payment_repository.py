from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from typing import List, Optional
import logging
import bcrypt
from app.models.payment import Payment, PaymentStatus

logger = logging.getLogger(__name__)

class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_successful_payment_by_order_id(self, order_id: int) -> Optional[Payment]:
        """Check if a successful payment already exists for the given order"""
        logger.debug(f"Repository: Checking for existing successful payment for order {order_id}")
        payment = self.db.query(Payment).filter(
            Payment.order_id == order_id,
            Payment.status == PaymentStatus.SUCCESSFUL
        ).first()
        
        if payment:
            logger.debug(f"Repository: Found existing successful payment with ID {payment.id}")
        else:
            logger.debug(f"Repository: No successful payment found for order {order_id}")
        
        return payment

    def create_payment(self, payment_data: dict) -> Payment:
        """Create a new payment with hashed CVV"""
        logger.debug(f"Repository: Creating payment for order {payment_data.get('order_id')}")
        
        # Hash the CVV
        hashed_cvv = bcrypt.hashpw(
            payment_data['cvv'].encode('utf-8'), 
            bcrypt.gensalt()
        )
        
        # Create payment object
        db_payment = Payment(
            order_id=payment_data['order_id'],
            amount=payment_data['amount'],
            card_number=payment_data['card_number'],
            card_holder_name=payment_data['card_holder_name'],
            expiry_date=payment_data['expiry_date'],
            hashed_cvv=hashed_cvv.decode('utf-8'),
            status=PaymentStatus.SUCCESSFUL
        )
        
        self.db.add(db_payment)
        self.db.commit()
        self.db.refresh(db_payment)
        
        logger.debug(f"Repository: Payment created successfully with ID {db_payment.id}")
        return db_payment

    def get_all_payments(self) -> List[Payment]:
        """Get all payments from the database"""
        logger.debug("Repository: Fetching all payments")
        payments = self.db.query(Payment).all()
        logger.debug(f"Repository: Found {len(payments)} payments")
        return payments

    def get_payment_by_id(self, payment_id: int) -> Optional[Payment]:
        """Get a single payment by ID"""
        logger.debug(f"Repository: Fetching payment with ID {payment_id}")
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        
        if payment:
            logger.debug(f"Repository: Payment found with ID {payment_id}")
        else:
            logger.debug(f"Repository: Payment not found with ID {payment_id}")
        
        return payment

    def get_payments_by_order_id(self, order_id: int) -> List[Payment]:
        """Get all payments for a specific order"""
        logger.debug(f"Repository: Fetching payments for order {order_id}")
        payments = self.db.query(Payment).filter(Payment.order_id == order_id).all()
        logger.debug(f"Repository: Found {len(payments)} payments for order {order_id}")
        return payments

    def update_payment_order_id(self, payment_id: int, order_id: int) -> Optional[Payment]:
        """Update the order_id of an existing payment"""
        logger.debug(f"Repository: Updating payment {payment_id} with order ID {order_id}")
        
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            logger.debug(f"Repository: Payment not found with ID {payment_id}")
            return None
        
        payment.order_id = order_id
        self.db.commit()
        self.db.refresh(payment)
        
        logger.debug(f"Repository: Payment {payment_id} updated successfully with order ID {order_id}")
        return payment

    def rollback(self):
        """Rollback the current transaction"""
        logger.debug("Repository: Rolling back transaction")
        self.db.rollback()

def get_payment_repository(db: Session = Depends(get_db)) -> PaymentRepository:
    """Dependency to get PaymentRepository instance"""
    return PaymentRepository(db)