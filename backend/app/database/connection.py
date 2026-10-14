"""Database engine and session factory management (synchronous SQLAlchemy 2.x).

Nothing here connects at import time — ``create_engine()`` is lazy and only
opens a connection when the first query runs. That keeps Alembic, tests and
tooling able to import the module without a live PostgreSQL.
"""
from __future__ import annotations

import logging

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings
from app.core.exceptions import DatabaseNotConfiguredError

logger = logging.getLogger(__name__)


def create_db_engine(settings: Settings | None = None) -> Engine:
    """Build a SQLAlchemy engine from settings.

    Raises:
        DatabaseNotConfiguredError: when ``DATABASE_URL`` is not set. This is
            intentional fail-fast behaviour — the app is useless without a DB.
    """
    settings = settings or get_settings()
    if not settings.database_url:
        raise DatabaseNotConfiguredError(
            "DATABASE_URL is not configured. "
            "Copy `.env.example` to `.env` and set DATABASE_URL before starting the API."
        )

    # SQLite is used only by tests. File-based SQLite reuses connections across
    # threads when SQLAlchemy's pool is active, which requires this flag.
    connect_args: dict[str, object] = {}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_pre_ping=True,      # transparently recycle dropped connections
        connect_args=connect_args,
        future=True,
    )
    logger.debug("Created SQLAlchemy engine for %s", describe_database(settings.database_url))
    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a session factory bound to ``engine``."""
    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,   # keep attribute values available after commit
    )


def ping_database(engine: Engine) -> None:
    """Open a connection and run ``SELECT 1``. Raises on failure."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def describe_database(database_url: str) -> str:
    """Return a **credential-free** description of the target database.

    Never includes the password — safe to log.
    """
    try:
        url = make_url(database_url)
        return (
            f"{url.get_backend_name()}://"
            f"{url.username or '?'}@{url.host or '?'}:{url.port or '?'}/{url.database or '?'}"
        )
    except Exception:  # noqa: BLE001 — never fail because of a log line
        return "<unparseable database url>"
