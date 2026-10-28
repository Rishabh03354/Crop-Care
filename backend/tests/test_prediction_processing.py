"""Service lifecycle tests using a mocked predictor boundary."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.domain.prediction import PredictionRecord, PredictionStatus
from app.ml.predictor import ModelInferenceError, PredictionResult
from app.repositories.prediction_repository import InMemoryPredictionRepository
from app.services.prediction_service import PredictionService
from app.utils.time import utcnow


class StubImageStorage:
    def read_bytes(self, stored_filename: str) -> bytes:
        return b"synthetic-image-bytes"

    def delete(self, stored_filename: str) -> None:
        return None


class FakePredictor:
    def __init__(
        self,
        *,
        available: bool = True,
        result: PredictionResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self._available = available
        self._result = result
        self._error = error

    async def warm_up(self) -> bool:
        return self._available

    async def predict(self, image_bytes: bytes) -> PredictionResult:
        if self._error is not None:
            raise self._error
        assert self._result is not None
        return self._result


def _pending_record() -> PredictionRecord:
    now = utcnow()
    return PredictionRecord(
        prediction_id=uuid4(),
        status=PredictionStatus.PENDING,
        stored_filename=("a" * 32) + ".png",
        content_type="image/png",
        size_bytes=17,
        created_at=now,
        updated_at=now,
        crop=None,
        disease=None,
        confidence=None,
        error_code=None,
    )


@pytest.mark.asyncio
async def test_processing_completes_with_real_plumbing_result() -> None:
    repository = InMemoryPredictionRepository()
    record = _pending_record()
    await repository.add(record)

    predict_result = PredictionResult(
        disease_name="synthetic-class-b",
        confidence=0.9123,
    )
    predictor = FakePredictor(result=predict_result)
    service = PredictionService(repository, StubImageStorage(), predictor)

    await service.process_prediction(record.prediction_id)

    updated = await repository.get(record.prediction_id)
    assert updated is not None
    assert updated.status is PredictionStatus.COMPLETED
    assert updated.disease == "synthetic-class-b"
    assert updated.confidence == 0.9123
    assert updated.error_code is None


@pytest.mark.asyncio
async def test_unavailable_model_leaves_record_pending() -> None:
    repository = InMemoryPredictionRepository()
    record = _pending_record()
    await repository.add(record)

    service = PredictionService(
        repository,
        StubImageStorage(),
        FakePredictor(available=False),
    )

    await service.process_prediction(record.prediction_id)

    updated = await repository.get(record.prediction_id)
    assert updated is not None
    assert updated.status is PredictionStatus.PENDING
    assert updated.disease is None
    assert updated.confidence is None


@pytest.mark.asyncio
async def test_inference_failure_marks_record_failed() -> None:
    repository = InMemoryPredictionRepository()
    record = _pending_record()
    await repository.add(record)

    service = PredictionService(
        repository,
        StubImageStorage(),
        FakePredictor(error=ModelInferenceError("synthetic forced failure")),
    )

    await service.process_prediction(record.prediction_id)

    updated = await repository.get(record.prediction_id)
    assert updated is not None
    assert updated.status is PredictionStatus.FAILED
    assert updated.error_code == "MODEL_INFERENCE_ERROR"
    assert updated.disease is None
    assert updated.confidence is None
