"""Health check and system monitoring endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
import time

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint for monitoring system status."""
    try:
        # Test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "timestamp": time.time(),
            "database": "connected"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": "Database connection failed"
            }
        )