"""
ArgosOS MVP - Database Engine

SQLAlchemy 2.x engine and session management for ArgosOS MVP.
Creates a local SQLite database at ./data/argos.db.
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from db.models import Base

# Database configuration
DATA_DIR = Path("./data")
DB_PATH = DATA_DIR / "argos.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Create engine with SQLAlchemy 2.x
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


def get_db_session() -> Session:
    """Get a database session for direct use"""
    return SessionLocal()


def get_db():
    """Dependency function for FastAPI - yields a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
