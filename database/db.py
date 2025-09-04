"""
Datenbank-Basisfunktionen und SQLAlchemy-Setup.

Stellt Engine, SessionLocal, Base und die FastAPI-Dependency `get_db` bereit.
"""

from typing import Iterator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

DATABASE_URL = "sqlite:///./erp.db"  # ggf. per ENV variabel machen

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
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
