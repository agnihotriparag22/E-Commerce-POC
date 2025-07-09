# Product Service

This is a microservice responsible for managing products and categories in the e-commerce system.

## Features

- Product management (CRUD operations)
- Category management
- Authentication and authorization
- Integration with User Service for admin verification

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create the database:
```sql
CREATE DATABASE IF NOT EXISTS product_service_db;
```

4. Initialize the database with sample data:
```bash
python -m app.db.init_db
```

## Running the Service

Start the service with:
```bash
python -m app.main
```

The service will be available at `http://localhost:8002`

## API Endpoints

### Products
- `GET /api/v1/products` - List all products
- `GET /api/v1/products/{product_id}` - Get product details
- `POST /api/v1/products` - Create a new product (admin only)
- `PUT /api/v1/products/{product_id}` - Update a product (admin only)
- `DELETE /api/v1/products/{product_id}` - Delete a product (admin only)

### Categories
- `GET /api/v1/categories` - List all categories
- `GET /api/v1/categories/{category_id}` - Get category details with products
- `POST /api/v1/categories` - Create a new category (admin only)

## Postman Testing Guide

### Prerequisites
1. Make sure both User Service (port 8001) and Product Service (port 8002) are running
2. Get an admin token from the User Service:
   - Send a POST request to `http://localhost:8001/token`
   - Body (form-data):
     ```
     username: admin@example.com
     password: admin123
     ```
   - Save the `access_token` from the response

### Setting up Postman
1. Create a new environment in Postman
2. Add a variable named `token` and paste your admin token
3. Add a variable named `base_url` with value `http://localhost:8002`

### Testing Products Endpoints

1. **List All Products**
   - Method: GET
   - URL: `{{base_url}}/api/v1/products`
   - No authentication required

2. **Get Product Details**
   - Method: GET
   - URL: `{{base_url}}/api/v1/products/1`
   - No authentication required

3. **Create Product (Admin Only)**
   - Method: POST
   - URL: `{{base_url}}/api/v1/products`
   - Headers:
     ```
     Authorization: Bearer {{token}}
     Content-Type: application/json
     ```
   - Body (raw JSON):
     ```json
     {
         "name": "Test Product",
         "description": "A test product",
         "price": 99.99,
         "stock": 100,
         "category_id": 1
     }
     ```

4. **Update Product (Admin Only)**
   - Method: PUT
   - URL: `{{base_url}}/api/v1/products/1`
   - Headers:
     ```
     Authorization: Bearer {{token}}
     Content-Type: application/json
     ```
   - Body (raw JSON):
     ```json
     {
         "price": 149.99,
         "stock": 75
     }
     ```

5. **Delete Product (Admin Only)**
   - Method: DELETE
   - URL: `{{base_url}}/api/v1/products/1`
   - Headers:
     ```
     Authorization: Bearer {{token}}
     ```

### Testing Categories Endpoints

1. **List All Categories**
   - Method: GET
   - URL: `{{base_url}}/api/v1/categories`
   - No authentication required

2. **Get Category with Products**
   - Method: GET
   - URL: `{{base_url}}/api/v1/categories/1`
   - No authentication required

3. **Create Category (Admin Only)**
   - Method: POST
   - URL: `{{base_url}}/api/v1/categories`
   - Headers:
     ```
     Authorization: Bearer {{token}}
     Content-Type: application/json
     ```
   - Body (raw JSON):
     ```json
     {
         "name": "New Category",
         "description": "A new category for testing"
     }
     ```

### Testing Tips
1. Always check the response status code and body
2. For admin endpoints, verify that requests fail without a valid token
3. Test error cases:
   - Invalid product/category IDs
   - Invalid category_id in product creation
   - Duplicate category names
   - Invalid token
   - Non-admin user token

## Authentication

The service integrates with the User Service for authentication. All admin operations require a valid JWT token with admin privileges.

## Environment Variables

The service uses the following environment variables:
- Database connection string (currently hardcoded in `app/db/database.py`)
- User Service URL (currently hardcoded in `app/core/auth.py`) 