"""Direct tests for ``SqlPredictionRepository`` (no HTTP layer).

These tests exercise the exact persistence contract the service depends on:
create a record, read it back, update it, and handle a missing id cleanly.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import FastAPI

from app.domain.prediction import PredictionRecord, PredictionStatus
from app.repositories.prediction_repository import SqlPredictionRepository


def _make_record(**overrides: object) -> PredictionRecord:
    """Build a valid domain record with sensible defaults."""
    now = datetime.now(timezone.utc)
    values: dict[str, object] = {
        "prediction_id": uuid4(),
        "status": PredictionStatus.PENDING,
        "stored_filename": "a" * 32 + ".png",
        "content_type": "image/png",
        "size_bytes": 128,
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return PredictionRecord(**values)  # type: ignore[arg-type]


@pytest.fixture()
def repository(app: FastAPI) -> SqlPredictionRepository:
    """Repository bound to the app's isolated test session factory."""
    return SqlPredictionRepository(app.state.session_factory)


async def test_add_returns_persisted_record(repository: SqlPredictionRepository) -> None:
    record = _make_record()

    created = await repository.add(record)

    assert created.prediction_id == record.prediction_id
    assert created.status is PredictionStatus.PENDING
    assert created.stored_filename == record.stored_filename
    assert created.size_bytes == record.size_bytes


async def test_get_returns_previously_stored_record(
    repository: SqlPredictionRepository,
) -> None:
    record = _make_record()
    await repository.add(record)

    fetched = await repository.get(record.prediction_id)

    assert fetched is not None
    assert fetched.prediction_id == record.prediction_id
    assert fetched.status is PredictionStatus.PENDING
    assert fetched.content_type == "image/png"


async def test_get_returns_none_for_unknown_id(
    repository: SqlPredictionRepository,
) -> None:
    assert await repository.get(uuid4()) is None


async def test_update_persists_completed_result(
    repository: SqlPredictionRepository,
) -> None:
    """Simulates the future ML worker writing a completed prediction."""
    record = _make_record()
    await repository.add(record)

    record.status = PredictionStatus.COMPLETED
    record.crop = "Tomato"
    record.disease = "Late blight"
    record.confidence = 0.9731
    record.updated_at = datetime.now(timezone.utc)

    updated = await repository.update(record)

    assert updated.status is PredictionStatus.COMPLETED
    assert updated.crop == "Tomato"
    assert updated.disease == "Late blight"
    assert updated.confidence == pytest.approx(0.9731)

    # A fresh read confirms it was actually written to the database.
    reloaded = await repository.get(record.prediction_id)
    assert reloaded is not None
    assert reloaded.status is PredictionStatus.COMPLETED
    assert reloaded.confidence == pytest.approx(0.9731)


async def test_update_missing_record_raises_prediction_not_found(
    repository: SqlPredictionRepository,
) -> None:
    from app.core.exceptions import PredictionNotFoundError

    ghost = _make_record()

    with pytest.raises(PredictionNotFoundError):
        await repository.update(ghost)
