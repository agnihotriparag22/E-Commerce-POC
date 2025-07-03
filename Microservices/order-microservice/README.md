# Order Microservice

This is the Order Microservice component of the E-Commerce platform. It handles order management, including creation, tracking, and status updates, while integrating with the Product and Payment microservices.

## Features

- Create and manage orders
- Real-time stock verification
- Payment processing integration
- Order status tracking
- User-specific order history
- Admin order management

## Prerequisites

- Python 3.8+
- PostgreSQL
- Docker (optional)

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
ORDER_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/order_db
AUTH_SERVICE_URL=http://localhost:8001
PRODUCT_SERVICE_URL=http://localhost:8002
PAYMENT_SERVICE_URL=http://localhost:8003
```

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

3. Set up the database:
```bash
# Create PostgreSQL database
createdb order_db

# Run migrations (if using Alembic)
alembic upgrade head
```

## Running the Service

Start the service with uvicorn:

```bash
uvicorn app.main:app --reload --port 8000
```

The service will be available at `http://localhost:8004`

## API Documentation

Once the service is running, you can access:
- Swagger UI: `http://localhost:8004/docs`
- ReDoc: `http://localhost:8004/redoc`

## API Endpoints

### Orders

- `POST /api/v1/orders/` - Create a new order
- `GET /api/v1/orders/{order_id}` - Get order details
- `GET /api/v1/orders/user/{user_id}` - Get user's orders
- `GET /api/v1/orders/` - Get all orders (admin only)
- `POST /api/v1/orders/{order_id}/complete` - Complete an order
- `POST /api/v1/orders/{order_id}/cancel` - Cancel an order
- `PATCH /api/v1/orders/{order_id}` - Update order status (admin only)

## Testing

Run tests with pytest:

```bash
pytest
```

## Docker Support

Build and run with Docker:

```bash
docker build -t order-microservice .
docker run -p 8004:8004 order-microservice
```

## Error Handling

The service includes comprehensive error handling for:
- Invalid requests
- Authentication failures
- Database errors
- External service communication issues
- Stock validation
- Payment processing

## Logging

Logs are configured to output to stdout with the following format:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 