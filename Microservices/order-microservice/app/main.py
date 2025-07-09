from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import order
from app.db.database import engine, Base
from app.kafka_logger import get_kafka_logger
from app.services.order_consumer import OrderConsumer
from app.db.database import SessionLocal
from app.models.order_item import OrderItem  
import asyncio
import os

# Configure logging
KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = 'logs.order-service'  
logger = get_kafka_logger(__name__, KAFKA_BROKER, KAFKA_TOPIC)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Order Microservice",
    description="Microservice for managing e-commerce orders",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(order.router)

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Order Microservice")
    db = SessionLocal()
    consumer = OrderConsumer(db)
    loop = asyncio.get_event_loop()
    loop.create_task(consumer.start())

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Order Microservice")