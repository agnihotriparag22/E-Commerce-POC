from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.core.auth import get_current_user
from app.repositories.payment_repository import PaymentRepository, get_payment_repository
from sqlalchemy.exc import SQLAlchemyError
from app.kafka_logger import get_kafka_logger
import os
from app.models.payment import PaymentStatus

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = 'logs.payment-service'  
logger = get_kafka_logger(__name__, KAFKA_BROKER, KAFKA_TOPIC)
router = APIRouter()

@router.post("/payments/", response_model=PaymentResponse)
async def create_payment(
    payment: PaymentCreate, 
    payment_repo: PaymentRepository = Depends(get_payment_repository),
    current_user: dict = Depends(get_current_user)
):
    logger.info(f"Creating new payment for order ID #{payment.order_id} by user {current_user['id']}")
    
    try:
        # Check if a successful payment already exists for this order
        existing_payment = payment_repo.get_successful_payment_by_order_id(payment.order_id)
        
        if existing_payment:
            logger.warning(f"Payment already exists for order ID #{payment.order_id}")
            raise HTTPException(
                status_code=400,
                detail=f"Payment for order ID #{payment.order_id} has already been processed successfully"
            )

        # Create the payment
        db_payment = payment_repo.create_payment(payment.dict())
        logger.info(f"Successfully created payment with ID {db_payment.id}")
        return db_payment
        
    except HTTPException:
        # Re-raise HTTP exceptions (like the duplicate payment check)
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error creating payment: {e}", exc_info=True)
        payment_repo.rollback()
        raise HTTPException(status_code=500, detail="Failed to create payment due to database error")
    except Exception as e:
        logger.error(f"Unexpected error creating payment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while creating payment")

@router.get("/payments/", response_model=List[PaymentResponse])
async def get_all_payments(
    payment_repo: PaymentRepository = Depends(get_payment_repository),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all payments (admin only).
    TODO: Add proper admin role check
    """
    logger.info(f"Fetching all payments by user {current_user['id']}")
    
    try:
        payments = payment_repo.get_all_payments()
        logger.info(f"Successfully fetched {len(payments)} payments")
        return payments
    except SQLAlchemyError as e:
        logger.error(f"Error fetching all payments: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch payments")
    except Exception as e:
        logger.error(f"Unexpected error fetching payments: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/payments/successful")
async def get_total_successful_payments(
    payment_repo: PaymentRepository = Depends(get_payment_repository),
    current_user: dict = Depends(get_current_user)
):
    """
    Get the total amount of all payments with status 'successful' from the payment microservice.
    """
    # Only admin should be able to access this endpoint (add admin check if needed)
    try:
        payments = payment_repo.get_all_payments()
       
        total = sum(
            payment.amount
            for payment in payments
            if (
                (hasattr(payment.status, "value") and payment.status == PaymentStatus.SUCCESSFUL)
                or (str(payment.status).lower() == PaymentStatus.SUCCESSFUL.value)
            )
        )
        print("total", total)
        return {"total_successful_payments": total}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching successful payments: {str(e)}"
        )

@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int, 
    payment_repo: PaymentRepository = Depends(get_payment_repository),
    current_user: dict = Depends(get_current_user)
):
    logger.info(f"Fetching payment with ID {payment_id} by user {current_user['id']}")
    
    try:
        payment = payment_repo.get_payment_by_id(payment_id)
        if payment is None:
            logger.warning(f"Payment not found with ID {payment_id}")
            raise HTTPException(status_code=404, detail="Payment not found")
        
        logger.info(f"Successfully fetched payment with ID {payment_id}")
        return payment
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except SQLAlchemyError as e:
        logger.error(f"Error fetching payment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch payment")
    except Exception as e:
        logger.error(f"Unexpected error fetching payment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/payments/order/{order_id}", response_model=List[PaymentResponse])
async def get_payments_by_order(
    order_id: int, 
    payment_repo: PaymentRepository = Depends(get_payment_repository),
    current_user: dict = Depends(get_current_user)
):
    logger.info(f"Fetching payments for order {order_id} by user {current_user['id']}")
    
    try:
        payments = payment_repo.get_payments_by_order_id(order_id)
        logger.info(f"Successfully fetched {len(payments)} payments for order {order_id}")
        return payments
    except SQLAlchemyError as e:
        logger.error(f"Error fetching payments for order {order_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch payments")
    except Exception as e:
        logger.error(f"Unexpected error fetching payments: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/payments/{payment_id}/order/{order_id}", response_model=PaymentResponse)
async def update_payment_order_id(
    payment_id: int,
    order_id: int,
    payment_repo: PaymentRepository = Depends(get_payment_repository),
    current_user: dict = Depends(get_current_user)
):
    logger.info(f"Updating payment {payment_id} with order ID {order_id}")
    
    try:
        payment = payment_repo.update_payment_order_id(payment_id, order_id)
        if payment is None:
            logger.warning(f"Payment not found with ID {payment_id}")
            raise HTTPException(status_code=404, detail="Payment not found")
        
        logger.info(f"Successfully updated payment {payment_id} with order ID {order_id}")
        return payment
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error updating payment: {e}", exc_info=True)
        payment_repo.rollback()
        raise HTTPException(status_code=500, detail="Failed to update payment due to database error")
    except Exception as e:
        logger.error(f"Unexpected error updating payment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while updating payment")