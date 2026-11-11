"""SQLAlchemy 2.0 database engine and session management (SQLite WAL mode)."""

from __future__ import annotations

from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import Settings, get_settings


class Base(DeclarativeBase):
    """Base declarative class for all Math Mayhem ORM models."""


def _configure_sqlite_pragma(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.execute("PRAGMA busy_timeout=5000;")
    cursor.close()


def create_db_engine(database_url: Optional[str] = None, settings: Optional[Settings] = None) -> Engine:
    cfg = settings or get_settings()
    url = database_url or cfg.database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, future=True)
    if url.startswith("sqlite"):
        event.listen(engine, "connect", _configure_sqlite_pragma)
    return engine


def init_db(engine: Engine) -> None:
    """Create all tables registered on Base metadata."""
    import app.models  # noqa: F401 — ensure models and triggers are imported

    Base.metadata.create_all(bind=engine)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
