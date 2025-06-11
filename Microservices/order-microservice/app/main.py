from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import order
from app.db.database import engine, Base
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Order Microservice") 