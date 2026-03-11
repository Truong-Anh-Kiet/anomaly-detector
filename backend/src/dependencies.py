"""FastAPI dependencies for shared components across routes"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.config import get_settings, Settings
from src.database import SessionLocal

# Database dependency
def get_db() -> Session:
    """Get database session for route handlers"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Settings dependency
def get_app_settings() -> Settings:
    """Get application settings"""
    return get_settings()
