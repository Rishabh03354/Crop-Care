"""Alembic environment for Crop Care Crop.

The database URL is resolved at runtime — never hard-coded here or in
``alembic.ini``. Precedence (first hit wins):

  1. ``-x db_url=...`` on the command line (e.g. CI / one-off runs)
  2. ``sqlalchemy.url`` set programmatically (used by tests)
  3. ``DATABASE_URL`` from the environment / ``.env`` (the normal path)
"""
from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Importing the package below registers every ORM model on ``Base.metadata``.
# Without this import, `alembic revision --autogenerate` produces an
# empty migration (the #1 cause of "my migration detected no changes").
from app import models  # noqa: F401
from app.core.config import get_settings
from app.database.base import Base

# Alembic Config object — gives access to values in `alembic.ini`.
config = context.config

if config.config_file_name is not None:
    # `disable_existing_loggers=False` keeps our app loggers alive when
    # Alembic reconfigures logging (important inside pytest).
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# --------------------------------------------------------------------------
# Resolve the database URL
# --------------------------------------------------------------------------
_url_from_x: str | None = context.get_x_argument(as_dictionary=True).get("db_url")
_url_from_config: str = (config.get_main_option("sqlalchemy.url") or "").strip()
database_url: str = _url_from_x or _url_from_config or get_settings().database_url

if not database_url:
    raise RuntimeError(
        "DATABASE_URL is not configured. Set it in `.env`, export it as an "
        "environment variable, or pass `-x db_url=...` to the alembic command."
    )

config.set_main_option("sqlalchemy.url", database_url)

# Metadata that `--autogenerate` compares the database against.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout without opening a database connection."""
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
