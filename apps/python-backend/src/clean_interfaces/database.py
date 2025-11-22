"""Database utilities and configuration for the backend.

This module centralizes SQLAlchemy engine/session setup so tests and runtime can
share the same initialization logic. The default database is a local SQLite
file under ``./data/city_data.db`` but it can be overridden with the
``DATABASE_URL`` environment variable.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

if TYPE_CHECKING:  # pragma: no cover - imports for type checking only
    from collections.abc import Generator
    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import Session

Base = declarative_base()

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_database_url() -> str:
    """Return the configured database URL or a sensible SQLite default."""
    return os.getenv("DATABASE_URL", "sqlite:///./data/city_data.db")


def _build_engine(
    database_url: str | None = None,
) -> tuple[Engine, sessionmaker]:
    """Create an engine and sessionmaker for the provided URL."""
    url = database_url or get_database_url()
    connect_args: dict[str, object] = {}
    pool_kwargs: dict[str, object] = {}

    if url.startswith("sqlite+pysqlite:///:memory:"):
        connect_args = {"check_same_thread": False}
        pool_kwargs = {"poolclass": StaticPool}
    elif url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        if url.startswith("sqlite:///"):
            db_path = Path(url.removeprefix("sqlite:///"))
            db_path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        url, echo=False, future=True, connect_args=connect_args, **pool_kwargs,
    )
    session_local = sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False, future=True,
    )
    return engine, session_local


def configure_engine(database_url: str | None = None) -> Engine:
    """Configure the global engine/session objects."""
    global _engine, _SessionLocal
    _engine, _SessionLocal = _build_engine(database_url)
    return _engine


def get_engine() -> Engine:
    """Return the configured engine, initializing it if necessary."""
    if _engine is None:
        configure_engine()
    if _engine is None:
        msg = "Engine configuration failed"
        raise RuntimeError(msg)
    return _engine


def get_session() -> Session:
    """Return a new Session bound to the configured engine."""
    if _SessionLocal is None:
        configure_engine()
    if _SessionLocal is None:
        msg = "Session factory is not configured"
        raise RuntimeError(msg)
    return _SessionLocal()


@contextmanager
def session_scope() -> Generator[Session]:
    """Context manager yielding a session and ensuring cleanup."""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(engine: Engine | None = None) -> None:
    """Create tables for all models registered to the Base metadata."""
    engine_to_use = engine or get_engine()
    Base.metadata.create_all(engine_to_use)
