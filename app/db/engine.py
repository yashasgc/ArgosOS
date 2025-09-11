from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.db.models import Base

# Database configuration
DATA_DIR = Path("./data")
DB_PATH = DATA_DIR / "argos.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database():
    """Initialize database - create all tables if they don't exist"""
    Base.metadata.create_all(bind=engine)
    print(f"✓ Database initialized at {DB_PATH}")

def create_tables():
    """Create all tables - alias for init_database for compatibility"""
    init_database()


def get_db() -> Session:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """Get a database session for direct use"""
    return SessionLocal()
