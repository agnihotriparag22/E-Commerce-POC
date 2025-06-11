from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import products_router, categories_router
from app.db.database import engine
from app.models.product import Base

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
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
    expose_headers=["*"]
)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 