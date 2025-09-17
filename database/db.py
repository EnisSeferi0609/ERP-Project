"""Database foundation functions and SQLAlchemy setup.

Provides engine, SessionLocal, Base and FastAPI dependency `get_db`.
"""

from typing import Iterator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from config import config

engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Iterator[Session]:
    """Liefert eine DB-Session für FastAPI-Dependencies.

    Yields:
        Session: geöffnete SQLAlchemy-Session, wird nach Nutzung geschlossen.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()