"""Authentication middleware for protecting routes."""

from fastapi import Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database.db import get_db
from app.utils.auth_utils import get_current_user
from app.models.user import User
from typing import Optional


def get_session_token(request: Request) -> Optional[str]:
    """Extract session token from cookies."""
    return request.cookies.get("session_token")


def require_auth(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Dependency to require authentication. Redirects to login if not authenticated."""
    token = get_session_token(request)

    if not token:
        # Check if this is a setup request
        if request.url.path in ["/setup", "/login"]:
            # Allow setup and login pages
            return None
        # Check if user exists for setup flow
        from app.models.user import User
        user_count = db.query(User).count()
        if user_count == 0:
            raise HTTPException(status_code=307, headers={"Location": "/setup"})
        else:
            raise HTTPException(status_code=307, headers={"Location": "/login"})

    user = get_current_user(db, token)
    if not user:
        raise HTTPException(status_code=307, headers={"Location": "/login"})

    return user


def optional_auth(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Optional authentication - returns user if logged in, None otherwise."""
    token = get_session_token(request)
    if not token:
        return None
    return get_current_user(db, token)


def check_setup_required(db: Session = Depends(get_db)) -> bool:
    """Check if initial setup is required."""
    from app.models.user import User
    user_count = db.query(User).count()
    return user_count == 0