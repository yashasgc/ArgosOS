from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.engine import get_db

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        sqlite_status = "ok"
    except Exception as e:
        sqlite_status = f"error: {str(e)}"
    
    return {
        "ok": True,
        "sqlite": sqlite_status
    }
