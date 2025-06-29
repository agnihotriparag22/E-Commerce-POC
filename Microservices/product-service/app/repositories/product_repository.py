from fastapi import Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from app.models.product import Product, Category
from app.services.rest_proxy import RestProxyService
from app.db.database import get_db
from app.schemas.schema_registry import SchemaRegistryService
import json
import os
from app.kafka_logger import get_kafka_logger

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = 'logs.product-service'  
logger = get_kafka_logger(__name__, KAFKA_BROKER, KAFKA_TOPIC)


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db
        self.rest_proxy = RestProxyService()
        self.schema_registry = SchemaRegistryService(subject = "product-events-value")
        product_event_schema = {
            "type": "record",
            "name": "ProductEvent",
            "fields": [
                {"name": "event", "type": "string"},
                {"name": "product_id", "type": "int"},
                {"name": "product_data", "type": {
                    "type": "record",
                    "name": "ProductData",
                    "fields": [
                        {"name": "name", "type": "string"},
                        {"name": "description", "type": "string"},
                        {"name": "price", "type": "double"},
                        {"name": "category_id", "type": "int"},
                        {"name": "stock", "type": "int"}
                    ]
                }}
            ]
        }
        schema_json = json.dumps(product_event_schema)
        # Async registration must be called outside __init__
        self._schema_json = schema_json
        self._schema_registered = False

    async def async_register_schema(self):
        if not self._schema_registered:
            await self.schema_registry.register_schema(self._schema_json)
            self._schema_registered = True

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

    async def create_product(self, product_data: dict) -> Product:
        """Create a new product"""
        logger.debug(f"Repository: Creating product with data={product_data}")
        db_product = Product(**product_data)
        self.db.add(db_product)
        self.db.commit()
        
        # Rest Proxy implementation for product creation
        await self.rest_proxy.send_event({
            "event": "product-created",
            "product_id": db_product.id,
            "product_data": product_data
        }, topic="product-events")
        
        self.db.refresh(db_product)
        logger.debug(f"Repository: Product created with id={db_product.id}")
        return db_product

    async def update_product(self, product_id: int, update_data: dict) -> Optional[Product]:
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
        
        # Rest Proxy implementation for product update
        await self.rest_proxy.send_event({
            "event": "product-updated",
            "product_id": db_product.id,
            "updated_data": update_data
        }, topic="product-events")
        
        self.db.refresh(db_product)
        logger.debug(f"Repository: Product id={product_id} updated successfully")
        return db_product

    async def delete_product(self, product_id: int) -> bool:
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
        
        # Rest Proxy implementation for product deletion
        await self.rest_proxy.send_event({
            "event": "product-deleted",
            "product_id": product_id
        }, topic="product-events")
        
        logger.debug(f"Repository: Product id={product_id} deleted successfully")
        return True

    async def decrease_product_stock(
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
        
        # Rest Proxy implementation for stock decrease
        await self.rest_proxy.send_event({
            "event": "product-stock-decreased",
            "product_id": product.id,
            "quantity": quantity,
            "new_stock": product.stock
        }, topic="product-events")
        if product.stock == 0:
            await self.rest_proxy.send_event({
                "event": "product-out-of-stock",
                "product_id": product.id
            }, topic="product-events")
            logger.debug(f"Repository: Product id={product_id} is now out of stock")
            
        self.db.refresh(product)
        logger.debug(
            f"Repository: Stock for product id={product_id} decreased successfully, new_stock={product.stock}"
        )
        return product, ""

    async def increase_product_stock(
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
        
        # Rest Proxy implementation for stock increase
        await self.rest_proxy.send_event({
            "event": "product-stock-increased",
            "product_id": product.id,
            "quantity": quantity,
            "new_stock": product.stock
        }, topic="product-events")
        if product.stock > 0:
            await self.rest_proxy.send_event({
                "event": "product-in-stock",
                "product_id": product.id
            }, topic="product-events")
            logger.debug(f"Repository: Product id={product_id} is now in stock")
            
        self.db.refresh(product)
        logger.debug(
            f"Repository: Stock for product id={product_id} increased successfully, new_stock={product.stock}"
        )
        return product


def get_product_repository(db: Session = Depends(get_db)) -> ProductRepository:
    """Dependency to get ProductRepository instance"""
    return ProductRepository(db)
