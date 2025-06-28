from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import requests
from app.kafka_logger import get_kafka_logger
import os
from dotenv import load_dotenv

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = 'logs.payment-service'  
logger = get_kafka_logger(__name__, KAFKA_BROKER, KAFKA_TOPIC)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8001/api/v1/token")

async def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        logger.info(f"Attempting to verify token with User Service")
        # Verify token with user service
        response = requests.get(
            "http://localhost:8001/api/v1/users/me",
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

async def get_current_user(token_data: dict = Depends(verify_token)) -> dict:
    """
    Get current user from verified token
    """
    return {
        "id": token_data["id"],
        "email": token_data["email"],
        "token": token_data.get("token", "")  # Token might not be in response
    }

async def verify_admin(token: str = Depends(oauth2_scheme)):
    user = await verify_token(token)
    if not user.get("is_admin"):
        logger.warning(f"Non-admin user attempted admin access: {user}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return user 