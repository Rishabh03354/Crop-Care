"""Disease catalogue repository interfaces and implementations."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from starlette.concurrency import run_in_threadpool

from app.core.exceptions import PersistenceError
from app.domain.disease import DiseaseRecord
from app.models.disease import Disease

logger = logging.getLogger(__name__)


class DiseaseRepository(ABC):
    """Persistence boundary for disease catalogue records."""

    @abstractmethod
    async def get_by_name(self, name: str) -> DiseaseRecord | None:
        """Return one disease by canonical name/slug, or ``None`` if absent."""

    @abstractmethod
    async def list_all(self) -> list[DiseaseRecord]:
        """Return all available catalogue records."""

    @abstractmethod
    async def upsert(self, record: DiseaseRecord) -> DiseaseRecord:
        """Create or update one catalogue record."""


class InMemoryDiseaseRepository(DiseaseRepository):
    """In-memory repository retained for direct unit tests only."""

    def __init__(
        self,
        records: Iterable[DiseaseRecord] | Mapping[str, DiseaseRecord] | None = None,
    ) -> None:
        source = records.values() if isinstance(records, Mapping) else (records or ())
        self._records: dict[str, DiseaseRecord] = {
            record.name.strip().lower(): record for record in source
        }

    async def get_by_name(self, name: str) -> DiseaseRecord | None:
        normalized = name.strip().lower()
        return self._records.get(normalized)

    async def list_all(self) -> list[DiseaseRecord]:
        return sorted(self._records.values(), key=lambda record: record.name)

    async def upsert(self, record: DiseaseRecord) -> DiseaseRecord:
        normalized = record.name.strip().lower()
        self._records[normalized] = record
        return record


class SqlDiseaseRepository(DiseaseRepository):
    """PostgreSQL-backed disease catalogue repository.

    Public methods are asynchronous so the service boundary stays stable.
    SQLAlchemy's synchronous session work runs in Starlette's worker pool.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    async def get_by_name(self, name: str) -> DiseaseRecord | None:
        normalized_name = name.strip()
        return await run_in_threadpool(
            self._get_by_name_sync,
            normalized_name,
        )

    async def list_all(self) -> list[DiseaseRecord]:
        return await run_in_threadpool(self._list_all_sync)

    async def upsert(self, record: DiseaseRecord) -> DiseaseRecord:
        """Create or update one catalogue record.

        Idempotent: matches by canonical name and updates existing fields.
        """
        return await run_in_threadpool(self._upsert_sync, record)

    def _get_by_name_sync(self, name: str) -> DiseaseRecord | None:
        if not name:
            return None

        clean = name.strip()
        slug = clean.lower().replace(" ", "-")
        with self._session_factory() as session:
            try:
                # Flexible lookup: matches exact name, lowercase, slug, or display_name
                stmt = select(Disease).where(
                    (func.lower(Disease.name) == clean.lower())
                    | (func.lower(Disease.name) == slug)
                    | (func.lower(Disease.display_name) == clean.lower())
                )
                model = session.scalar(stmt)
                return _to_domain(model) if model is not None else None
            except SQLAlchemyError as exc:
                session.rollback()
                logger.exception("Disease repository lookup failed for %r", name)
                raise PersistenceError("The disease catalogue is temporarily unavailable.") from exc

    def _list_all_sync(self) -> list[DiseaseRecord]:
        with self._session_factory() as session:
            try:
                models = session.scalars(
                    select(Disease).order_by(Disease.name.asc())
                ).all()
                return [_to_domain(model) for model in models]
            except SQLAlchemyError as exc:
                session.rollback()
                logger.exception("Disease repository list_all failed.")
                raise PersistenceError("The disease catalogue is temporarily unavailable.") from exc

    def _upsert_sync(self, record: DiseaseRecord) -> DiseaseRecord:
        with self._session_factory() as session:
            try:
                stmt = select(Disease).where(func.lower(Disease.name) == record.name.strip().lower())
                model = session.scalar(stmt)

                if model is None:
                    model = Disease(name=record.name.strip())
                    session.add(model)

                _apply_record(model, record)
                session.commit()
                return _to_domain(model)
            except SQLAlchemyError as exc:
                session.rollback()
                logger.exception("Disease repository upsert failed for %r", record.name)
                raise PersistenceError("The disease catalogue is temporarily unavailable.") from exc


def _apply_record(model: Disease, record: DiseaseRecord) -> None:
    model.name = record.name.strip()
    model.display_name = getattr(record, "display_name", record.name)
    model.crop = record.crop
    model.description = record.description
    model.symptoms = list(record.symptoms or ())
    model.causes = getattr(record, "causes", "")
    model.treatment = list(getattr(record, "treatment", ()))
    model.severity = getattr(record, "severity", "medium")


def _to_domain(model: Disease) -> DiseaseRecord:
    return DiseaseRecord(
        name=model.name,
        display_name=model.display_name or model.name,
        crop=model.crop or "Wheat",
        description=model.description or "",
        symptoms=tuple(model.symptoms or ()),
        causes=model.causes or "",
        severity=model.severity or "medium",
    )
