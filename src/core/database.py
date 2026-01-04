from sqlmodel import SQLModel, Session, create_engine, text
from typing import Generator
import logging
import bcrypt

from .config import settings

# ✅ IMPORTANT: Import in dependency order!
# 1. Base tables first (no foreign keys)
from ..models.schedule import Schedule
from ..models.specialty import Specialty
from ..models.user import User
# 2. Tables that depend only on base tables
from ..models.admin import Admin
from ..models.teacher import Teacher
from ..models.student import Student



# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Create engine with connection pool settings for Neon DB
engine = create_engine(
    settings.DATABASE_URL, 
    echo=False,
    pool_pre_ping=True,  # Check connection before using
    pool_recycle=300,    # Recycle connections after 5 minutes
    pool_size=5,
    max_overflow=10
)

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

def seed_test_users(session: Session):
    """Create test users for auth testing"""
    
    # Check if users already exist
    existing = session.exec(text("SELECT COUNT(*) FROM public.users")).first()
    if existing and existing[0] > 0:
        logger.info("📌 Test users already exist, skipping seed")
        return
    
    hashed_password = hash_password("password123")
    
    # Create Admin User
    admin_user = User(
        full_name="Admin User",
        email="admin@test.com",
        department="Administration",
        hashed_password=hashed_password,
        role="admin",
        is_active=True,
        is_superuser=True,
        is_verified=True
    )
    session.add(admin_user)
    session.commit()
    session.refresh(admin_user)
    
    admin_profile = Admin(user_id=admin_user.id)
    session.add(admin_profile)

    # Create Teacher User
    teacher_user = User(
        full_name="Teacher User",
        email="teacher@test.com",
        department="Computer Science",
        hashed_password=hashed_password,
        role="teacher",
        is_active=True,
        is_verified=True
    )
    session.add(teacher_user)
    session.commit()
    session.refresh(teacher_user)
    
    teacher_profile = Teacher(user_id=teacher_user.id)
    session.add(teacher_profile)
    
    # Create Student User
    student_user = User(
        full_name="Student User",
        email="student@test.com",
        department="Computer Science",
        hashed_password=hashed_password,
        role="student",
        is_active=True,
        is_verified=True
    )
    session.add(student_user)
    session.commit()
    session.refresh(student_user)
    
    student_profile = Student(user_id=student_user.id)
    session.add(student_profile)
    
    session.commit()
    
    logger.info("✅ Test users created successfully!")
    logger.info("📧 Test Credentials (password: password123):")
    logger.info("   - Admin:   admin@test.com")
    logger.info("   - Teacher: teacher@test.com")
    logger.info("   - Student: student@test.com")

def init_db():
    """Initialize database tables"""
    # First check connection
    if check_database_connection():
        # Drop ALL existing tables and types in public schema first
        with Session(engine) as session:
            # Drop all tables with CASCADE
            session.exec(text("""
                DO $$ 
                DECLARE 
                    r RECORD;
                BEGIN
                    -- Drop all tables
                    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                        EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
                    END LOOP;
                    
                    -- Drop all custom types (this fixes the pg_type error)
                    FOR r IN (SELECT typname FROM pg_type t 
                              JOIN pg_namespace n ON t.typnamespace = n.oid 
                              WHERE n.nspname = 'public' AND t.typtype = 'c') LOOP
                        EXECUTE 'DROP TYPE IF EXISTS public.' || quote_ident(r.typname) || ' CASCADE';
                    END LOOP;
                END $$;
            """))
            session.commit()
            logger.info("🗑️ All existing tables and types dropped!")
        
        # Create only User, Student, Teacher, Admin tables
        SQLModel.metadata.create_all(engine, checkfirst=True)
        logger.info("✅ Tables created: users, students, teacher, admins")
        
        # Seed test users
        with Session(engine) as session:
            seed_test_users(session)
    else:
        logger.error("❌ Cannot initialize database - connection failed!")
        raise Exception("Database connection failed")

def get_session() -> Generator[Session, None, None]:
    """Get database session"""
    with Session(engine) as session:
        yield session