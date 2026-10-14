"""Declarative base for all ORM models.

Every model in ``app.models`` inherits from ``Base``. Alembic's autogenerate
reads ``Base.metadata`` to diff the desired schema against the database.
"""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class every ORM model inherits from."""
