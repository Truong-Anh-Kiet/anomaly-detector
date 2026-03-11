"""Database connection and initialization"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from src.config import get_settings

settings = get_settings()

# Create engine
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
