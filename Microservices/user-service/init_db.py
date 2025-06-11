from sqlalchemy.orm import Session
from app.models import user
from app.db import database
from app.core import security

def init_db():
    db = database.SessionLocal()
    
    # Check if users already exist
    if db.query(user.User).first() is not None:
        print("Users already exist in database")
        return

    # Create fixed users
    users = [
        {
            "username": "admin",
            "email": "admin@example.com",
            "password": "admin123",
            "is_admin": True
        },
        {
            "username": "prakhar",
            "email": "prakhar@example.com",
            "password": "prakhar123",
            "is_admin": False
        },
        {
            "username": "hrishab",
            "email": "hrishab@example.com",
            "password": "hrishab123",
            "is_admin": False
        },
        {
            "username": "parag",
            "email": "parag@example.com",
            "password": "parag123",
            "is_admin": False
        }
    ]

    for user_data in users:
        hashed_password = security.get_password_hash(user_data["password"])
        db_user = user.User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=hashed_password,
            is_admin=user_data["is_admin"]
        )
        db.add(db_user)

    db.commit()
    print("Database initialized with fixed users")

if __name__ == "__main__":
    init_db() 