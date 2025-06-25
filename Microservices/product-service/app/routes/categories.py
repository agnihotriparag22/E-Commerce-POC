from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.product import Category
from app.schemas.product import Category as CategorySchema, CategoryCreate, CategoryWithProducts
from app.core.auth import verify_admin
from app.kafka_logger import get_kafka_logger
import os

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = 'logs.product-service'  
logger = get_kafka_logger(__name__, KAFKA_BROKER, KAFKA_TOPIC)
router = APIRouter()

# @router.get("/", response_model=List[CategorySchema])
# def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     categories = db.query(Category).offset(skip).limit(limit).all()
#     return categories

@router.get("/", response_model=List[CategorySchema])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all categories"""
    try:
        categories = db.query(Category).all()
        return [{"id": cat.id, "name": cat.name, "description": cat.description} for cat in categories]
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching categories: {str(e)}"
        )

@router.get("/{category_id}", response_model=CategoryWithProducts)
def read_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.post("/", response_model=CategorySchema)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin)
):
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category 