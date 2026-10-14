"""Prediction data access.

Three things live here:
  1. ``PredictionRepository``       — the abstract interface the service sees.
  2. ``InMemoryPredictionRepository`` — fast, non-persistent, used in unit tests.
  3. ``SqlPredictionRepository``      — PostgreSQL-backed implementation used
                                        by the running application.

Services depend only on the interface; swapping the implementation does not
change a single route or service file.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from starlette.concurrency import run_in_threadpool

from app.core.exceptions import PersistenceError, PredictionNotFoundError
from app.domain.prediction import PredictionRecord, PredictionStatus
from app.models.prediction import Prediction

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------


class PredictionRepository(ABC):
    """Abstract persistence interface for prediction records."""

    @abstractmethod
    async def add(self, record: PredictionRecord) -> PredictionRecord:
        """Persist a new record and return it."""

    @abstractmethod
    async def get(self, prediction_id: UUID) -> PredictionRecord | None:
        """Return the record, or None when it does not exist."""

    @abstractmethod
    async def update(self, record: PredictionRecord) -> PredictionRecord:
        """Persist changes to an existing record and return it."""


# ---------------------------------------------------------------------------
# In-memory implementation (unit tests)
# ---------------------------------------------------------------------------


class InMemoryPredictionRepository(PredictionRepository):
    """Process-local, non-persistent storage.

    Used only by unit tests that do not want to spin up a database. The running
    application always uses ``SqlPredictionRepository``.
    """

    def __init__(self) -> None:
        self._records: dict[UUID, PredictionRecord] = {}

    async def add(self, record: PredictionRecord) -> PredictionRecord:
        self._records[record.prediction_id] = record
        return record

    async def get(self, prediction_id: UUID) -> PredictionRecord | None:
        return self._records.get(prediction_id)

    async def update(self, record: PredictionRecord) -> PredictionRecord:
        self._records[record.prediction_id] = record
        return record


# ---------------------------------------------------------------------------
# SQL implementation (PostgreSQL — the production path)
# ---------------------------------------------------------------------------


class SqlPredictionRepository(PredictionRepository):
    """PostgreSQL-backed implementation using synchronous SQLAlchemy 2.x.

    Thread-safety and session lifetime
    ----------------------------------
    The repository holds a **session factory**, never a live session, so the
    instance is safe to keep as a process-wide singleton. Each public async
    method delegates to a synchronous helper executed in a worker thread
    (``run_in_threadpool``), which opens its own short-lived session, commits
    on success and rolls back on failure.

    This keeps the async event loop responsive during DB round-trips and avoids
    sharing a session across threads or requests.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # --- async public API -------------------------------------------------

    async def add(self, record: PredictionRecord) -> PredictionRecord:
        return await run_in_threadpool(self._add_sync, record)

    async def get(self, prediction_id: UUID) -> PredictionRecord | None:
        return await run_in_threadpool(self._get_sync, prediction_id)

    async def update(self, record: PredictionRecord) -> PredictionRecord:
        return await run_in_threadpool(self._update_sync, record)

    # --- sync implementations (run in a worker thread) --------------------

    def _add_sync(self, record: PredictionRecord) -> PredictionRecord:
        with self._session_factory() as session:
            try:
                orm = _domain_to_orm(record)
                session.add(orm)
                session.commit()
                return _orm_to_domain(orm)
            except SQLAlchemyError as exc:
                session.rollback()
                logger.exception(
                    "Failed to persist prediction %s", record.prediction_id
                )
                raise PersistenceError() from exc

    def _get_sync(self, prediction_id: UUID) -> PredictionRecord | None:
        with self._session_factory() as session:
            orm = session.get(Prediction, prediction_id)
            return _orm_to_domain(orm) if orm is not None else None

    def _update_sync(self, record: PredictionRecord) -> PredictionRecord:
        with self._session_factory() as session:
            try:
                orm = session.get(Prediction, record.prediction_id)
                if orm is None:
                    # Nothing to roll back yet — no writes have happened.
                    raise PredictionNotFoundError(
                        f"Prediction '{record.prediction_id}' does not exist."
                    )
                _apply_domain(orm, record)
                session.commit()
                return _orm_to_domain(orm)
            except PredictionNotFoundError:
                session.rollback()
                raise
            except SQLAlchemyError as exc:
                session.rollback()
                logger.exception(
                    "Failed to update prediction %s", record.prediction_id
                )
                raise PersistenceError() from exc


# ---------------------------------------------------------------------------
# Domain ↔ ORM mapping (pure functions, easy to unit-test)
# ---------------------------------------------------------------------------


def _domain_to_orm(record: PredictionRecord) -> Prediction:
    """Build a fresh ORM row from a domain record."""
    return Prediction(
        id=record.prediction_id,
        image_path=record.stored_filename,
        content_type=record.content_type,
        size_bytes=record.size_bytes,
        status=record.status.value,
        crop_name=record.crop,
        disease_name=record.disease,
        confidence=record.confidence,
        error_code=record.error_code,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _apply_domain(orm: Prediction, record: PredictionRecord) -> None:
    """Copy mutable fields from a domain record onto an existing ORM row.

    Identity fields (``id``, ``image_path``, ``content_type``, ``size_bytes``,
    ``created_at``) are immutable after creation and are deliberately not
    updated.
    """
    orm.status = record.status.value
    orm.crop_name = record.crop
    orm.disease_name = record.disease
    orm.confidence = record.confidence
    orm.error_code = record.error_code
    orm.updated_at = record.updated_at


def _orm_to_domain(orm: Prediction) -> PredictionRecord:
    """Build a domain record from an ORM row."""
    return PredictionRecord(
        prediction_id=orm.id,
        status=PredictionStatus(orm.status),
        stored_filename=orm.image_path,
        content_type=orm.content_type,
        size_bytes=orm.size_bytes,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
        crop=orm.crop_name,
        disease=orm.disease_name,
        confidence=float(orm.confidence) if orm.confidence is not None else None,
        error_code=orm.error_code,
    )
