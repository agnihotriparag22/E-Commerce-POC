from fastapi import Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
import logging
from app.models.product import Product, Category
from app.db.database import get_db

logger = logging.getLogger(__name__)


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_products_paginated(
        self,
        skip: int,
        limit: int,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Product], int]:
        """
        Get paginated products with optional filtering
        Returns: (products, total_count)
        """
        logger.debug(f"Repository: Fetching products with skip={skip}, limit={limit}")

        # Build query
        query = self.db.query(Product)

        # Apply filters
        if category_id:
            logger.debug(f"Repository: Filtering by category_id={category_id}")
            query = query.filter(Product.category_id == category_id)

        if search:
            logger.debug(f"Repository: Searching with term='{search}'")
            search_term = f"%{search}%"
            query = query.filter(
                (Product.name.ilike(search_term))
                | (Product.description.ilike(search_term))
            )

        # Get total count
        total = query.count()

        # Get paginated results
        products = query.offset(skip).limit(limit).all()

        logger.debug(f"Repository: Found {len(products)} products (total={total})")
        return products, total

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get a single product by ID"""
        logger.debug(f"Repository: Fetching product with id={product_id}")
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if product:
            logger.debug(f"Repository: Product found: {product.name}")
        else:
            logger.debug(f"Repository: Product with id={product_id} not found")
        return product

    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Get a category by ID"""
        logger.debug(f"Repository: Fetching category with id={category_id}")
        return self.db.query(Category).filter(Category.id == category_id).first()

    def create_product(self, product_data: dict) -> Product:
        """Create a new product"""
        logger.debug(f"Repository: Creating product with data={product_data}")
        db_product = Product(**product_data)
        self.db.add(db_product)
        self.db.commit()
        self.db.refresh(db_product)
        logger.debug(f"Repository: Product created with id={db_product.id}")
        return db_product

    def update_product(self, product_id: int, update_data: dict) -> Optional[Product]:
        """Update an existing product"""
        logger.debug(
            f"Repository: Updating product id={product_id} with data={update_data}"
        )
        db_product = self.db.query(Product).filter(Product.id == product_id).first()

        if not db_product:
            logger.debug(
                f"Repository: Product with id={product_id} not found for update"
            )
            return None

        # Update only provided fields
        for field, value in update_data.items():
            logger.debug(f"Repository: Updating field '{field}' to '{value}'")
            setattr(db_product, field, value)

        self.db.commit()
        self.db.refresh(db_product)
        logger.debug(f"Repository: Product id={product_id} updated successfully")
        return db_product

    def delete_product(self, product_id: int) -> bool:
        """Delete a product by ID"""
        logger.debug(f"Repository: Deleting product with id={product_id}")
        db_product = self.db.query(Product).filter(Product.id == product_id).first()

        if not db_product:
            logger.debug(
                f"Repository: Product with id={product_id} not found for deletion"
            )
            return False

        self.db.delete(db_product)
        self.db.commit()
        logger.debug(f"Repository: Product id={product_id} deleted successfully")
        return True

    def decrease_product_stock(
        self, product_id: int, quantity: int
    ) -> Tuple[Optional[Product], str]:
        """
        Decrease product stock
        Returns: (product, error_message)
        """
        logger.debug(
            f"Repository: Decreasing stock for product id={product_id} by {quantity}"
        )
        product = self.db.query(Product).filter(Product.id == product_id).first()

        if not product:
            logger.debug(
                f"Repository: Product with id={product_id} not found for stock decrease"
            )
            return None, "Product not found"

        if product.stock < quantity:
            logger.debug(
                f"Repository: Insufficient stock for product id={product_id}: current={product.stock}, requested={quantity}"
            )
            return None, "Insufficient stock"

        product.stock -= quantity
        self.db.commit()
        self.db.refresh(product)
        logger.debug(
            f"Repository: Stock for product id={product_id} decreased successfully, new_stock={product.stock}"
        )
        return product, ""

    def increase_product_stock(
        self, product_id: int, quantity: int
    ) -> Optional[Product]:
        """Increase product stock"""
        logger.debug(
            f"Repository: Increasing stock for product id={product_id} by {quantity}"
        )
        product = self.db.query(Product).filter(Product.id == product_id).first()

        if not product:
            logger.debug(
                f"Repository: Product with id={product_id} not found for stock increase"
            )
            return None

        product.stock += quantity
        self.db.commit()
        self.db.refresh(product)
        logger.debug(
            f"Repository: Stock for product id={product_id} increased successfully, new_stock={product.stock}"
        )
        return product


def get_product_repository(db: Session = Depends(get_db)) -> ProductRepository:
    """Dependency to get ProductRepository instance"""
    return ProductRepository(db)
