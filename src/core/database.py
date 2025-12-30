from sqlmodel import SQLModel, create_engine, Session, text
from typing import Generator
import logging

from .config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(settings.DATABASE_URL, echo=False)

def check_database_connection() -> bool:
    """Check if database connection is successful"""
    try:
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        logger.info("✅ Database connection successful!")
        logger.info(f"📍 Connected to: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        return False

def init_db():
    """Initialize database tables"""
    # First check connection
    if check_database_connection():
        SQLModel.metadata.create_all(engine)
        logger.info("✅ Database tables initialized successfully!")
    else:
        logger.error("❌ Cannot initialize database - connection failed!")
        raise Exception("Database connection failed")

def get_session() -> Generator[Session, None, None]:
    """Get database session"""
    with Session(engine) as session:
        yield session