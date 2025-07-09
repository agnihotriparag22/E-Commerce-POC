# Payment Microservice

A simple payment microservice that handles basic payment processing with card validation.

## Features

- Basic payment processing
- Card validation (16-digit card number, MM/YY expiry date, 3-digit CVV)
- Payment status tracking
- Order-based payment history

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

3. Set up environment variables:
Create a `.env` file in the root directory with:
```
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/payment_service_db
```

4. Create MySQL database:
```sql
CREATE DATABASE payment_service_db;
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Create Payment
- **POST** `/api/v1/payments/`
- Request body:
```json
{
    "order_id": 1,
    "amount": 100.00,
    "card_number": "1234567890123456",
    "card_holder_name": "John Doe",
    "expiry_date": "12/25",
    "cvv": "123"
}
```

### Get Payment by ID
- **GET** `/api/v1/payments/{payment_id}`

### Get Payments by Order ID
- **GET** `/api/v1/payments/order/{order_id}`

## Validation Rules

- Card number must be exactly 16 digits
- Expiry date must be in MM/YY format
- CVV must be exactly 3 digits 