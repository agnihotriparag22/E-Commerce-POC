from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Dict, Any
import requests

from app.core.security import verify_password, create_access_token, get_current_active_user, get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import Token, LoginSchema

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)  # Move to config
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=Dict[str, Any])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin
    }

@router.get("/users/me/orders", response_model=List[Dict[str, Any]])
async def get_user_orders(current_user: User = Depends(get_current_active_user)):
    """
    Fetch orders for the current user from the order service.
    This endpoint acts as a proxy to the order service.
    """
    try:
        # Make request to order service
        response = requests.get(
            f"http://localhost:8000/orders/user/{current_user.id}",
            headers={"Authorization": f"Bearer {current_user.email}"}
        )
        
        if response.status_code == 404:
            return []
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Error fetching orders from order service"
            )
            
        return response.json()
        
    except requests.RequestException:
        raise HTTPException(
            status_code=503,
            detail="Order service is currently unavailable"
        )

@router.post("/login")
async def login(login_data: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)  # Move to config
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }
    }

@router.get("/verify-token")
async def verify_token(current_user: User = Depends(get_current_user)):
    """
    Verify if the provided token is valid and return the user information.
    This endpoint is used to check if a token is still valid and get the user info.
    """
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "is_admin": current_user.is_admin
        }
    } 