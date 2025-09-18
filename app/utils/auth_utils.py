"""Authentication utilities for user management."""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.orm import Session
from app.models.user import User
from config import config

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Session serializer
serializer = URLSafeTimedSerializer(config.SECRET_KEY)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_user(db: Session, username: str, email: str, password: str) -> User:
    """Create a new user with hashed password."""
    hashed_password = get_password_hash(password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None

    # Update last login
    user.last_login = datetime.now()
    db.commit()
    return user


def create_session_token(user_id: int) -> str:
    """Create a secure session token."""
    return serializer.dumps({"user_id": user_id, "timestamp": datetime.now().isoformat()})


def verify_session_token(token: str, max_age: int = 86400) -> Optional[int]:
    """Verify session token and return user_id if valid."""
    try:
        data = serializer.loads(token, max_age=max_age)
        return data.get("user_id")
    except Exception:
        return None


def get_current_user(db: Session, token: str) -> Optional[User]:
    """Get current user from session token."""
    user_id = verify_session_token(token)
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()