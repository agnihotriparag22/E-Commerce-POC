# User Service

This is a microservice responsible for user authentication and management in the e-commerce system.

## Features

- User authentication (login, token generation)
- User profile management
- Integration with Order Service for fetching user orders
- JWT-based authentication
- SQLite database (can be easily changed to other databases)

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

3. Run the application:
```bash
uvicorn app.main:app --reload --port 8001
```

The service will be available at `http://localhost:8001`

## API Endpoints

### Authentication

- `POST /api/v1/token` - Get access token (OAuth2 compatible)
- `POST /api/v1/login` - Login endpoint with custom response
- `GET /api/v1/users/me` - Get current user profile
- `GET /api/v1/users/me/orders` - Get orders for current user (proxies to Order Service)

## Environment Variables

The service uses the following configuration:

- `SECRET_KEY`: JWT signing key (default provided for development)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 30 minutes)
- `SQLALCHEMY_DATABASE_URL`: Database connection URL (default: SQLite)

## Integration with Order Service

The User Service integrates with the Order Service (running on port 8000) to fetch user orders. The integration is handled through HTTP requests with JWT authentication.

## Security Notes

- In production, replace the `SECRET_KEY` with a secure key
- Update CORS settings to allow only specific origins
- Consider using environment variables for sensitive configuration
- Use HTTPS in production 