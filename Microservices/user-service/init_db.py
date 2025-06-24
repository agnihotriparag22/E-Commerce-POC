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
        },
        {
            "username": "ishita",
            "email": "ishita@example.com",
            "password": "ishita123",
            "is_admin": False
        },
        {
            "username": "sanika",
            "email": "sanika@example.com",
            "password": "sanika123",
            "is_admin": False
        },
        {
            "username": "viral",
            "email": "viral@example.com",
            "password": "viral123",
            "is_admin": False
        },
        {
            "username": "rachit",
            "email": "rachit@example.com",
            "password": "rachit123",
            "is_admin": False
        },
        {
            "username": "abhishek",
            "email": "abhishek@example.com",
            "password": "abhishek123",
            "is_admin": False
        },
        {
            "username": "shefali",
            "email": "shefali@example.com",
            "password": "shefali123",
            "is_admin": False
        },
        {
            "username": "anshu",
            "email": "anshu@example.com",
            "password": "anshu123",
            "is_admin": False
        },
        {
            "username": "vividh",
            "email": "vividh@example.com",
            "password": "vividh123",
            "is_admin": False
        },
        {
            "username": "durgesh",
            "email": "durgesh@example.com",
            "password": "durgesh123",
            "is_admin": False
        },
        {
            "username": "aditya",
            "email": "aditya@example.com",
            "password": "aditya123",
            "is_admin": False
        },
        {
            "username": "rajkuwar",
            "email": "rajkuwar@example.com",
            "password": "rajkuwar123",
            "is_admin": False
        },
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