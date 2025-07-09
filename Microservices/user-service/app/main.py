import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth
from app.db.database import engine
from app.models import user
from app.kafka_logger import get_kafka_logger
import os

# Create database tables
user.Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Welcome to User Service API"}

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = 'logs.user-service' 
logger = get_kafka_logger(__name__, KAFKA_BROKER, KAFKA_TOPIC)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)