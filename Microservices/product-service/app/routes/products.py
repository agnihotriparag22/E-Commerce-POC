# from fastapi import APIRouter, Depends, HTTPException, Header, Query
# from sqlalchemy.orm import Session
# from typing import List, Optional
# import requests
# import logging
# from pydantic import BaseModel, Field
# from app.db.database import get_db
# from app.models.product import Product, Category
# from app.schemas.product import Product as ProductSchema, ProductCreate, ProductUpdate
# from app.core.auth import verify_admin, verify_token

# # Set up logging
# logger = logging.getLogger(__name__)

# router = APIRouter()

# class PaginatedProductsResponse(BaseModel):
#     products: List[ProductSchema]
#     total: int
#     page: int
#     totalPages: int

# class StockUpdate(BaseModel):
#     quantity: int = Field(..., gt=0, description="Quantity to update stock by")

# @router.get("", response_model=PaginatedProductsResponse)  # Empty string for root path
# @router.get("/", response_model=PaginatedProductsResponse)  # With trailing slash
# def read_products(
#     page: int = Query(1, ge=1, description="Page number (starts from 1)"),
#     limit: int = Query(100, ge=1, le=1000, description="Number of items per page (max 1000)"),
#     category_id: Optional[int] = Query(None, description="Filter by category ID"),
#     search: Optional[str] = Query(None, description="Search in product name and description"),
#     db: Session = Depends(get_db)
# ):
#     logger.info(f"Fetching products: page={page}, limit={limit}, category_id={category_id}, search={search}")
#     try:
#         # Calculate skip
#         skip = (page - 1) * limit
        
#         # Build query
#         query = db.query(Product)
        
#         # Apply filters
#         if category_id:
#             logger.debug(f"Filtering products by category_id={category_id}")
#             query = query.filter(Product.category_id == category_id)
#         if search:
#             logger.debug(f"Searching products with term='{search}'")
#             search_term = f"%{search}%"
#             query = query.filter(
#                 (Product.name.ilike(search_term)) | 
#                 (Product.description.ilike(search_term))
#             )
        
#         # Get total count
#         total = query.count()
        
#         # Get paginated results
#         products = query.offset(skip).limit(limit).all()
        
#         # Calculate total pages
#         total_pages = (total + limit - 1) // limit

#         logger.info(f"Returning {len(products)} products (total={total}, page={page}/{total_pages})")
#         return {
#             "products": products,
#             "total": total,
#             "page": page,
#             "totalPages": total_pages
#         }
#     except Exception as e:
#         logger.error(f"Error fetching products: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error fetching products: {str(e)}"
#         )

# @router.get("/{product_id}", response_model=ProductSchema)
# def read_product(product_id: int, db: Session = Depends(get_db)):
#     logger.info(f"Fetching product with id={product_id}")
#     product = db.query(Product).filter(Product.id == product_id).first()
#     if product is None:
#         logger.warning(f"Product with id={product_id} not found")
#         raise HTTPException(status_code=404, detail="Product not found")
#     logger.debug(f"Product found: {product}")
#     return product

# @router.post("", response_model=ProductSchema)  # Empty string for root path
# @router.post("/", response_model=ProductSchema)  # With trailing slash
# def create_product(
#     product: ProductCreate,
#     db: Session = Depends(get_db),
#     current_user: dict = Depends(verify_admin)
# ):
#     logger.info(f"Creating product: {product}")
#     # Verify category exists
#     category = db.query(Category).filter(Category.id == product.category_id).first()
#     if not category:
#         logger.warning(f"Category with id={product.category_id} not found")
#         raise HTTPException(status_code=404, detail="Category not found")
    
#     db_product = Product(**product.dict())
#     db.add(db_product)
#     db.commit()
#     db.refresh(db_product)
#     logger.info(f"Product created with id={db_product.id}")
#     return db_product

# @router.put("/{product_id}", response_model=ProductSchema)
# def update_product(
#     product_id: int,
#     product: ProductUpdate,
#     db: Session = Depends(get_db),
#     current_user: dict = Depends(verify_admin)
# ):
#     logger.info(f"Updating product id={product_id} with data={product}")
#     db_product = db.query(Product).filter(Product.id == product_id).first()
#     if db_product is None:
#         logger.warning(f"Product with id={product_id} not found for update")
#         raise HTTPException(status_code=404, detail="Product not found")
    
#     # Update only provided fields
#     update_data = product.dict(exclude_unset=True)
#     for field, value in update_data.items():
#         logger.debug(f"Updating field '{field}' to '{value}'")
#         setattr(db_product, field, value)
    
#     db.commit()
#     db.refresh(db_product)
#     logger.info(f"Product id={product_id} updated successfully")
#     return db_product

# @router.delete("/{product_id}")
# def delete_product(
#     product_id: int,
#     db: Session = Depends(get_db),
#     current_user: dict = Depends(verify_admin)
# ):
#     logger.info(f"Deleting product with id={product_id}")
#     db_product = db.query(Product).filter(Product.id == product_id).first()
#     if db_product is None:
#         logger.warning(f"Product with id={product_id} not found for deletion")
#         raise HTTPException(status_code=404, detail="Product not found")
    
#     db.delete(db_product)
#     db.commit()
#     logger.info(f"Product id={product_id} deleted successfully")
#     return {"message": "Product deleted successfully"}

# @router.post("/{product_id}/decrease-stock")
# def decrease_stock(
#     product_id: int,
#     stock_update: StockUpdate,
#     db: Session = Depends(get_db)
# ):
#     logger.info(f"Decreasing stock for product id={product_id} by {stock_update.quantity}")
#     product = db.query(Product).filter(Product.id == product_id).first()
#     if product is None:
#         logger.warning(f"Product with id={product_id} not found for stock decrease")
#         raise HTTPException(status_code=404, detail="Product not found")
    
#     if product.stock < stock_update.quantity:
#         logger.warning(f"Insufficient stock for product id={product_id}: current={product.stock}, requested={stock_update.quantity}")
#         raise HTTPException(status_code=400, detail="Insufficient stock")
    
#     product.stock -= stock_update.quantity
#     db.commit()
#     db.refresh(product)
#     logger.info(f"Stock for product id={product_id} decreased successfully, new_stock={product.stock}")
#     return {"message": "Stock decreased successfully", "new_stock": product.stock}

# @router.post("/{product_id}/increase-stock")
# def increase_stock(
#     product_id: int,
#     stock_update: StockUpdate,
#     db: Session = Depends(get_db)
# ):
#     logger.info(f"Increasing stock for product id={product_id} by {stock_update.quantity}")
#     product = db.query(Product).filter(Product.id == product_id).first()
#     if product is None:
#         logger.warning(f"Product with id={product_id} not found for stock increase")
#         raise HTTPException(status_code=404, detail="Product not found")
    
#     product.stock += stock_update.quantity
#     db.commit()
#     db.refresh(product)
#     logger.info(f"Stock for product id={product_id} increased successfully, new_stock={product.stock}")
#     return {"message": "Stock increased successfully", "new_stock": product.stock}

# # Debug endpoints
# @router.get("/debug-token")
# async def debug_token(authorization: str = Header(None)):
#     logger.info("Debugging token endpoint called")
#     if not authorization:
#         logger.warning("No authorization header provided")
#         return {"error": "No authorization header provided"}
    
#     try:
#         # Extract token from header
#         token = authorization.replace("Bearer ", "")
#         logger.info(f"Received token: {token[:10]}...")  # Log first 10 chars for debugging
        
#         # Try to verify with User Service directly
#         logger.info("Attempting to connect to User Service...")
#         response = requests.get(
#             "http://localhost:8001/api/v1/users/me",
#             headers={"Authorization": f"Bearer {token}"}
#         )
#         logger.info(f"User Service response: {response.status_code}")
        
#         return {
#             "token_received": bool(token),
#             "token_length": len(token),
#             "token_preview": f"{token[:10]}...",  # Show first 10 chars
#             "user_service_status": response.status_code,
#             "user_service_response": response.text,
#             "headers_sent": {"Authorization": "Bearer [token]"}  # Don't log full token
#         }
#     except requests.RequestException as e:
#         logger.error(f"Request error: {str(e)}")
#         return {"error": f"Request error: {str(e)}"}
#     except Exception as e:
#         logger.error(f"Unexpected error: {str(e)}")
#         return {"error": f"Unexpected error: {str(e)}"}

# @router.get("/test-auth")
# async def test_auth(current_user: dict = Depends(verify_token)):
#     logger.info("test-auth endpoint called, token is valid")
#     return {"message": "Token is valid", "user": current_user}

# @router.get("/test-admin")
# async def test_admin(current_user: dict = Depends(verify_admin)):
#     logger.info("test-admin endpoint called, admin token is valid")
#     return {"message": "Admin token is valid", "user": current_user}

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import requests
import logging
from pydantic import BaseModel, Field
from app.db.database import get_db
from app.schemas.product import Product as ProductSchema, ProductCreate, ProductUpdate
from app.core.auth import verify_admin, verify_token
from app.repositories.product_repository import ProductRepository, get_product_repository

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

class PaginatedProductsResponse(BaseModel):
    products: List[ProductSchema]
    total: int
    page: int
    totalPages: int

class StockUpdate(BaseModel):
    quantity: int = Field(..., gt=0, description="Quantity to update stock by")

@router.get("", response_model=PaginatedProductsResponse)  # Empty string for root path
@router.get("/", response_model=PaginatedProductsResponse)  # With trailing slash
def read_products(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items per page (max 1000)"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    search: Optional[str] = Query(None, description="Search in product name and description"),
    product_repo: ProductRepository = Depends(get_product_repository)
):
    logger.info(f"Fetching products: page={page}, limit={limit}, category_id={category_id}, search={search}")
    try:
        # Calculate skip
        skip = (page - 1) * limit
        
        # Get products from repository
        products, total = product_repo.get_products_paginated(
            skip=skip, 
            limit=limit, 
            category_id=category_id, 
            search=search
        )
        
        # Calculate total pages
        total_pages = (total + limit - 1) // limit

        logger.info(f"Returning {len(products)} products (total={total}, page={page}/{total_pages})")
        return {
            "products": products,
            "total": total,
            "page": page,
            "totalPages": total_pages
        }
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching products: {str(e)}"
        )

@router.get("/{product_id}", response_model=ProductSchema)
def read_product(
    product_id: int, 
    product_repo: ProductRepository = Depends(get_product_repository)
):
    logger.info(f"Fetching product with id={product_id}")
    product = product_repo.get_product_by_id(product_id)
    if product is None:
        logger.warning(f"Product with id={product_id} not found")
        raise HTTPException(status_code=404, detail="Product not found")
    logger.debug(f"Product found: {product}")
    return product

@router.post("", response_model=ProductSchema)  # Empty string for root path
@router.post("/", response_model=ProductSchema)  # With trailing slash
def create_product(
    product: ProductCreate,
    product_repo: ProductRepository = Depends(get_product_repository),
    current_user: dict = Depends(verify_admin)
):
    logger.info(f"Creating product: {product}")
    
    # Verify category exists
    category = product_repo.get_category_by_id(product.category_id)
    if not category:
        logger.warning(f"Category with id={product.category_id} not found")
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Create product
    db_product = product_repo.create_product(product.dict())
    logger.info(f"Product created with id={db_product.id}")
    return db_product

@router.put("/{product_id}", response_model=ProductSchema)
def update_product(
    product_id: int,
    product: ProductUpdate,
    product_repo: ProductRepository = Depends(get_product_repository),
    current_user: dict = Depends(verify_admin)
):
    logger.info(f"Updating product id={product_id} with data={product}")
    
    # Update product
    update_data = product.dict(exclude_unset=True)
    db_product = product_repo.update_product(product_id, update_data)
    
    if db_product is None:
        logger.warning(f"Product with id={product_id} not found for update")
        raise HTTPException(status_code=404, detail="Product not found")
    
    logger.info(f"Product id={product_id} updated successfully")
    return db_product

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    product_repo: ProductRepository = Depends(get_product_repository),
    current_user: dict = Depends(verify_admin)
):
    logger.info(f"Deleting product with id={product_id}")
    
    success = product_repo.delete_product(product_id)
    if not success:
        logger.warning(f"Product with id={product_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Product not found")
    
    logger.info(f"Product id={product_id} deleted successfully")
    return {"message": "Product deleted successfully"}

@router.post("/{product_id}/decrease-stock")
def decrease_stock(
    product_id: int,
    stock_update: StockUpdate,
    product_repo: ProductRepository = Depends(get_product_repository)
):
    logger.info(f"Decreasing stock for product id={product_id} by {stock_update.quantity}")
    
    product, error_message = product_repo.decrease_product_stock(product_id, stock_update.quantity)
    
    if product is None:
        logger.warning(f"Failed to decrease stock for product id={product_id}: {error_message}")
        if error_message == "Product not found":
            raise HTTPException(status_code=404, detail="Product not found")
        else:  # Insufficient stock
            raise HTTPException(status_code=400, detail="Insufficient stock")
    
    logger.info(f"Stock for product id={product_id} decreased successfully, new_stock={product.stock}")
    return {"message": "Stock decreased successfully", "new_stock": product.stock}

@router.post("/{product_id}/increase-stock")
def increase_stock(
    product_id: int,
    stock_update: StockUpdate,
    product_repo: ProductRepository = Depends(get_product_repository)
):
    logger.info(f"Increasing stock for product id={product_id} by {stock_update.quantity}")
    
    product = product_repo.increase_product_stock(product_id, stock_update.quantity)
    if product is None:
        logger.warning(f"Product with id={product_id} not found for stock increase")
        raise HTTPException(status_code=404, detail="Product not found")
    
    logger.info(f"Stock for product id={product_id} increased successfully, new_stock={product.stock}")
    
    return {"message": "Stock increased successfully", "new_stock": product.stock}

# Debug endpoints
@router.get("/debug-token")
async def debug_token(authorization: str = Header(None)):
    logger.info("Debugging token endpoint called")
    if not authorization:
        logger.warning("No authorization header provided")
        return {"error": "No authorization header provided"}
    
    try:
        # Extract token from header
        token = authorization.replace("Bearer ", "")
        logger.info(f"Received token: {token[:10]}...")  # Log first 10 chars for debugging
        
        # Try to verify with User Service directly
        logger.info("Attempting to connect to User Service...")
        response = requests.get(
            "http://localhost:8001/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        logger.info(f"User Service response: {response.status_code}")
        
        return {
            "token_received": bool(token),
            "token_length": len(token),
            "token_preview": f"{token[:10]}...",  # Show first 10 chars
            "user_service_status": response.status_code,
            "user_service_response": response.text,
            "headers_sent": {"Authorization": "Bearer [token]"}  # Don't log full token
        }
    except requests.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return {"error": f"Request error: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}

@router.get("/test-auth")
async def test_auth(current_user: dict = Depends(verify_token)):
    logger.info("test-auth endpoint called, token is valid")
    return {"message": "Token is valid", "user": current_user}

@router.get("/test-admin")
async def test_admin(current_user: dict = Depends(verify_admin)):
    logger.info("test-admin endpoint called, admin token is valid")
    return {"message": "Admin token is valid", "user": current_user}