from sqlmodel import SQLModel, Session as SQLModelSession, create_engine, text
from typing import Generator
import logging
import bcrypt

from .config import settings

# Set up logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Import all models at once to avoid circular dependency issues
# This ensures all classes are available when relationships are configured
from ..models.user import User
from ..models.specialty import Specialty
from ..models.schedule import Schedule
from ..models.admin import Admin
from ..models.teacher import Teacher
from ..models.student import Student
from ..models.module import Module
from ..models.sday import SDay
from ..models.teacher_modules import TeacherModules
from ..models.enrollement import Enrollment
from ..models.session import Session
from ..models.attendance import AttendanceRecord
from ..models.justification import Justification
from ..models.notification import Notification
from ..models.report import Report

# ✅ Configure all mappers now that all classes are imported
from sqlalchemy.orm import configure_mappers
try:
    configure_mappers()
except Exception as e:
    logger.warning(f"⚠️ Mapper configuration warning: {e}")

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
        with SQLModelSession(engine) as session:
            session.exec(text("SELECT 1"))
        logger.info("✅ Database connection successful!")
        logger.info(f"📍 Connected to: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
        return True
    except Exception as e:
        import traceback
        logger.error(f"❌ Database connection failed: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

def seed_test_users(session: SQLModelSession):
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
    """Initialize database tables in dependency order"""
    # First check connection
    if check_database_connection():
        # Drop ALL existing tables and types in public schema first
        with SQLModelSession(engine) as session:
            # Drop all tables with CASCADE
            session.exec(text("DO $$ DECLARE r RECORD; BEGIN FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE'; END LOOP; FOR r IN (SELECT typname FROM pg_type t JOIN pg_namespace n ON t.typnamespace = n.oid WHERE n.nspname = 'public' AND t.typtype = 'c') LOOP EXECUTE 'DROP TYPE IF EXISTS public.' || quote_ident(r.typname) || ' CASCADE'; END LOOP; END $$;"))
            session.commit()
            logger.info("🗑️ All existing tables and types dropped!")
        
        # Create all tables (order matters for foreign keys)
            SQLModel.metadata.create_all(engine, checkfirst=True)
        
        # Log created tables in order
        logger.info("✅ All tables created successfully!")
        logger.info("📊 Tables created (in dependency order):")
        logger.info("   1️⃣  Base tables: users, specialty, schedule")
        logger.info("   2️⃣  User-dependent: admins, teacher")
        logger.info("   3️⃣  Multi-dependent: students, module")
        logger.info("   4️⃣  Composite: s_day, teacher_modules, enrollments")
        logger.info("   5️⃣  Advanced: sessions, attendance_records")
        logger.info("   6️⃣  Final: justifications, notifications, report")
        
        # Seed test users - do this last after all models are configured
        try:
            with SQLModelSession(engine) as session:
                seed_test_users(session)
        except Exception as e:
            logger.debug(f"ℹ️ Info: Test users seeding skipped: {str(e)}")
    else:
        logger.error("❌ Cannot initialize database - connection failed!")
        raise Exception("Database connection failed")

def get_session() -> Generator[SQLModelSession, None, None]:
    """Get database session"""
    with SQLModelSession(engine) as session:
        yield session