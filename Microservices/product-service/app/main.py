from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import products_router, categories_router
from app.db.database import engine, SessionLocal
from app.models.product import Base
from app.kafka_logger import get_kafka_logger
from app.services.product_consumer import ProductConsumer
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Product Service",
    description="Product management microservice",
    version="1.0.0"
)

# Configure CORS
origins = [
    "http://localhost:3000",     # React default port
    "http://localhost:5173",     # Vite default port
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    # Add any other frontend URLs you need
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:3000",     # React default port
    "http://localhost:5173",     # Vite default port
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    # Add any other frontend URLs you need
],
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
    expose_headers=["*"]
)

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = 'logs.product-service' 
logger = get_kafka_logger(__name__, KAFKA_BROKER, KAFKA_TOPIC)

# Include routers
app.include_router(products_router, prefix="/api/v1/products", tags=["products"])
app.include_router(categories_router, prefix="/api/v1/categories", tags=["categories"])

@app.get("/")
async def root():
    return {
        "message": "Product Service API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.on_event("startup")
async def start_product_consumer():
    db = SessionLocal()
    consumer = ProductConsumer(db)
    loop = asyncio.get_event_loop()
    loop.create_task(consumer.start())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)