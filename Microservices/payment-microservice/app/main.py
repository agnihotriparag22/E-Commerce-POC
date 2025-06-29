from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from app.routes.payment import router as payment_router
from app.core.auth import get_current_user
from app.kafka_logger import get_kafka_logger
from app.services.payment_consumer import PaymentConsumer
from app.database import SessionLocal
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Configure logging
KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = 'logs.payment-service' 
logger = get_kafka_logger(__name__, KAFKA_BROKER, KAFKA_TOPIC)
logger.info("TEST: Logger initialized in main.py")
logger.error("TEST: This is a forced error log from main.py")

app = FastAPI(title="Payment Microservice")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with authentication
app.include_router(
    payment_router,
    prefix="/api/v1",
    tags=["payments"],
    dependencies=[Depends(get_current_user)]
)

@app.get("/")
def read_root():
    return {"message": "Payment Microservice mein aapka swagat hai!!!"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error handler caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred"}
    )

@app.on_event("startup")
async def startup_event():
    print("Startup event called")  # Add this line
    logger.info("FastAPI startup_event triggered")
    db = SessionLocal()
    consumer = PaymentConsumer(db)
    loop = asyncio.get_event_loop()
    try:
        consumer_task = loop.create_task(consumer.start())
        app.state.payment_consumer = consumer
        app.state.payment_consumer_task = consumer_task
    except Exception as e:
        logger.error(f"Failed to start PaymentConsumer: {e}", exc_info=True)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Payment Service is shutting down...")
    consumer = getattr(app.state, "payment_consumer", None)
    if consumer:
        await consumer.stop()
    consumer_task = getattr(app.state, "payment_consumer_task", None)
    if consumer_task:
        consumer_task.cancel()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)