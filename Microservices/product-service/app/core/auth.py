from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import requests
import os
from app.kafka_logger import get_kafka_logger

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = 'logs.product-service'  
logger = get_kafka_logger(__name__, KAFKA_BROKER, KAFKA_TOPIC)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8001/api/v1/token")

async def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        logger.info(f"Attempting to verify token with User Service")
        # Verify token with user service - using /api/v1 prefix
        response = requests.get(
            "http://localhost:8001/api/v1/users/me",  # Updated endpoint
            headers={"Authorization": f"Bearer {token}"}
        )
        logger.info(f"User Service response status: {response.status_code}")
        logger.info(f"User Service response body: {response.text}")
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication credentials. User Service response: {response.text}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error connecting to User Service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"User service unavailable: {str(e)}"
        )

async def verify_admin(token: str = Depends(oauth2_scheme)):
    user = await verify_token(token)
    if not user.get("is_admin"):
        logger.warning(f"Non-admin user attempted admin access: {user}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return user 