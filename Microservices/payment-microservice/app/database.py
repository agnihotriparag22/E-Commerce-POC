from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.db.base import Base
from app.models.payment import Payment  # Import here to ensure models are registered with Base
import logging
from sqlalchemy.exc import SQLAlchemyError
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    engine = create_engine(DATABASE_URL)
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Error creating database engine: {e}", exc_info=True)
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()

# Drop and recreate all tables
try:
    Base.metadata.drop_all(bind=engine)  # Drop all tables
    logger.info("Dropped all existing tables")
    Base.metadata.create_all(bind=engine)  # Create tables with new schema
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error recreating database tables: {e}", exc_info=True)
    raise 