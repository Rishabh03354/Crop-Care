"""Stabilization tests for the ML predictor and prediction lifecycle."""

from __future__ import annotations

import struct
import zlib
from dataclasses import replace
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import ModelNotAvailableError
from app.domain.prediction import PredictionRecord, PredictionStatus
from app.ml.model_loader import ModelLoader
from app.ml.predictor import (
    CropDiseasePredictor,
    ModelInferenceError,
    PredictionResult,
    _select_top_prediction,
)
from app.repositories.prediction_repository import InMemoryPredictionRepository
from app.services.prediction_service import PredictionService
from app.utils.images import ValidatedImage
from app.utils.time import utcnow


class StubImageStorage:
    """Small synchronous storage substitute for service tests."""

    def __init__(self, read_error: Exception | None = None) -> None:
        self.saved: list[ValidatedImage] = []
        self.deleted: list[str] = []
        self._read_error = read_error

    def save(self, image: ValidatedImage) -> str:
        self.saved.append(image)
        return ("a" * 32) + image.extension

    def read_bytes(self, stored_filename: str) -> bytes:
        if self._read_error is not None:
            raise self._read_error
        return b"validated-image-bytes"

    def delete(self, stored_filename: str) -> None:
        self.deleted.append(stored_filename)


class StubPredictor:
    """Predictor boundary substitute used by service tests."""

    def __init__(
        self,
        *,
        available: bool = True,
        result: PredictionResult | None = None,
        warm_up_error: Exception | None = None,
        predict_error: Exception | None = None,
    ) -> None:
        self.available = available
        self.result = result
        self.warm_up_error = warm_up_error
        self.predict_error = predict_error
        self.warm_up_calls = 0
        self.predict_calls = 0
        self.last_image_bytes: bytes | None = None

    async def warm_up(self) -> bool:
        self.warm_up_calls += 1
        if self.warm_up_error is not None:
            raise self.warm_up_error
        return self.available

    async def predict(self, image_bytes: bytes) -> PredictionResult:
        self.predict_calls += 1
        self.last_image_bytes = image_bytes

        if self.predict_error is not None:
            raise self.predict_error

        assert self.result is not None
        return self.result


class RecordingPredictionRepository(InMemoryPredictionRepository):
    """In-memory repository that records status transitions."""

    def __init__(self) -> None:
        super().__init__()
        self.status_updates: list[PredictionStatus] = []

    async def update(self, record: PredictionRecord) -> PredictionRecord:
        self.status_updates.append(record.status)
        return await super().update(record)


class CompletionFailureRepository(RecordingPredictionRepository):
    """Fail exactly once when the service attempts a completed update."""

    def __init__(self) -> None:
        super().__init__()
        self._fail_completion_once = True

    async def update(self, record: PredictionRecord) -> PredictionRecord:
        if (
            record.status == PredictionStatus.COMPLETED
            and self._fail_completion_once
        ):
            self._fail_completion_once = False
            raise RuntimeError("forced completion persistence failure")

        return await super().update(record)


class FailingPredictionRepository:
    """Repository substitute that always fails on add."""

    async def add(self, record: PredictionRecord) -> PredictionRecord:
        raise RuntimeError("forced persistence failure")


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


def _png_1x1_red() -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(
                ">I",
                zlib.crc32(kind + data) & 0xFFFFFFFF,
            )
        )

    signature = b"\x89PNG\r\n\x1a\n"
    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    image_data = zlib.compress(b"\x00\xff\x00\x00")

    return (
        signature
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", image_data)
        + chunk(b"IEND", b"")
    )


def test_top_prediction_maps_to_configured_label() -> None:
    result = _select_top_prediction(
        [0.05, 0.90, 0.05],
        ["synthetic-class-a", "synthetic-class-b", "synthetic-class-c"],
    )

    assert result.disease_name == "synthetic-class-b"
    assert result.confidence == 0.90


def test_top_prediction_rejects_confidence_outside_probability_range() -> None:
    with pytest.raises(ModelInferenceError):
        _select_top_prediction(
            [1.4, -0.4],
            ["synthetic-class-a", "synthetic-class-b"],
        )


def test_top_prediction_rejects_label_count_mismatch() -> None:
    with pytest.raises(ModelInferenceError):
        _select_top_prediction(
            [0.25, 0.75],
            ["synthetic-class-a"],
        )


def test_model_loader_reports_missing_artifact(tmp_path) -> None:
    artifact_path = tmp_path / "missing.pt"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")

    settings = SimpleNamespace(
        model_artifact_path=str(artifact_path),
        model_manifest_path=str(manifest_path),
        model_device="cpu",
    )
    loader = ModelLoader(settings)

    assert loader.load() is None
    assert loader.is_available is False
    assert "not found" in loader.unavailable_reason.lower()


@pytest.mark.asyncio
async def test_predictor_reports_unconfigured_model() -> None:
    settings = SimpleNamespace(
        model_artifact_path="",
        model_manifest_path="",
        model_device="cpu",
    )
    predictor = CropDiseasePredictor(ModelLoader(settings))

    with pytest.raises(ModelNotAvailableError):
        await predictor.predict(b"synthetic-image-bytes")


def test_predictor_maps_synthetic_tensor_output() -> None:
    torch = pytest.importorskip("torch")
    pytest.importorskip("numpy")
    pytest.importorskip("PIL")

    from app.ml.model_loader import (
        LoadedModel,
        ModelInputSpec,
        ModelManifest,
    )

    class FakeModel:
        def __call__(self, tensor):
            assert tuple(tensor.shape) == (1, 3, 2, 2)
            return torch.tensor([[0.1, 0.9]], dtype=torch.float32)

    manifest = ModelManifest(
        artifact_format="torchscript_image_classifier",
        class_labels=["synthetic-class-a", "synthetic-class-b"],
        input=ModelInputSpec(
            width=2,
            height=2,
            mean=(0.0, 0.0, 0.0),
            std=(1.0, 1.0, 1.0),
        ),
        output_activation="softmax",
    )
    loaded = LoadedModel(
        model=FakeModel(),
        manifest=manifest,
        device="cpu",
    )

    predictor = CropDiseasePredictor(
        ModelLoader(
            SimpleNamespace(
                model_artifact_path="",
                model_manifest_path="",
                model_device="cpu",
            )
        )
    )

    result = predictor._predict_with_loaded_model(
        loaded,
        _png_1x1_red(),
    )

    assert result.disease_name == "synthetic-class-b"
    assert 0.68 <= result.confidence <= 0.70


@pytest.mark.asyncio
async def test_processing_records_processing_then_completed() -> None:
    repository = RecordingPredictionRepository()
    record = _pending_record()
    await repository.add(record)

    predictor = StubPredictor(
        result=PredictionResult(
            disease_name="synthetic-class-b",
            confidence=0.9123,
        )
    )
    service = PredictionService(
        repository,
        StubImageStorage(),
        predictor,
    )

    await service.process_prediction(record.prediction_id)

    stored = await repository.get(record.prediction_id)
    assert stored is not None
    assert stored.status == PredictionStatus.COMPLETED
    assert stored.disease == "synthetic-class-b"
    assert stored.confidence == 0.9123
    assert stored.error_code is None
    assert predictor.predict_calls == 1
    assert repository.status_updates == [
        PredictionStatus.PROCESSING,
        PredictionStatus.COMPLETED,
    ]


@pytest.mark.asyncio
async def test_unavailable_model_leaves_record_pending() -> None:
    repository = RecordingPredictionRepository()
    record = _pending_record()
    await repository.add(record)

    predictor = StubPredictor(available=False)
    service = PredictionService(
        repository,
        StubImageStorage(),
        predictor,
    )

    await service.process_prediction(record.prediction_id)

    stored = await repository.get(record.prediction_id)
    assert stored is not None
    assert stored.status == PredictionStatus.PENDING
    assert stored.disease is None
    assert stored.confidence is None
    assert predictor.predict_calls == 0
    assert repository.status_updates == []


@pytest.mark.asyncio
async def test_model_becoming_unavailable_restores_pending() -> None:
    repository = RecordingPredictionRepository()
    record = _pending_record()
    await repository.add(record)

    predictor = StubPredictor(
        available=True,
        predict_error=ModelNotAvailableError(),
    )
    service = PredictionService(
        repository,
        StubImageStorage(),
        predictor,
    )

    await service.process_prediction(record.prediction_id)

    stored = await repository.get(record.prediction_id)
    assert stored is not None
    assert stored.status == PredictionStatus.PENDING
    assert stored.disease is None
    assert stored.confidence is None
    assert repository.status_updates == [
        PredictionStatus.PROCESSING,
        PredictionStatus.PENDING,
    ]


@pytest.mark.asyncio
async def test_inference_error_persists_failed_state() -> None:
    repository = RecordingPredictionRepository()
    record = _pending_record()
    await repository.add(record)

    predictor = StubPredictor(
        predict_error=ModelInferenceError("forced inference failure"),
    )
    service = PredictionService(
        repository,
        StubImageStorage(),
        predictor,
    )

    await service.process_prediction(record.prediction_id)

    stored = await repository.get(record.prediction_id)
    assert stored is not None
    assert stored.status == PredictionStatus.FAILED
    assert stored.disease is None
    assert stored.confidence is None
    assert stored.error_code == "MODEL_INFERENCE_ERROR"
    assert repository.status_updates == [
        PredictionStatus.PROCESSING,
        PredictionStatus.FAILED,
    ]


@pytest.mark.asyncio
async def test_unreadable_image_persists_failed_state() -> None:
    repository = RecordingPredictionRepository()
    record = _pending_record()
    await repository.add(record)

    predictor = StubPredictor()
    service = PredictionService(
        repository,
        StubImageStorage(read_error=OSError("forced read failure")),
        predictor,
    )

    await service.process_prediction(record.prediction_id)

    stored = await repository.get(record.prediction_id)
    assert stored is not None
    assert stored.status == PredictionStatus.FAILED
    assert stored.error_code == "IMAGE_UNAVAILABLE"
    assert predictor.predict_calls == 0


@pytest.mark.asyncio
async def test_completed_record_is_not_reprocessed() -> None:
    repository = RecordingPredictionRepository()
    record = replace(
        _pending_record(),
        status=PredictionStatus.COMPLETED,
        disease="synthetic-class-a",
        confidence=0.75,
    )
    await repository.add(record)

    predictor = StubPredictor(
        result=PredictionResult(
            disease_name="synthetic-class-b",
            confidence=0.9,
        )
    )
    service = PredictionService(
        repository,
        StubImageStorage(),
        predictor,
    )

    await service.process_prediction(record.prediction_id)

    stored = await repository.get(record.prediction_id)
    assert stored is not None
    assert stored.status == PredictionStatus.COMPLETED
    assert stored.disease == "synthetic-class-a"
    assert stored.confidence == 0.75
    assert predictor.predict_calls == 0
    assert repository.status_updates == []


@pytest.mark.asyncio
async def test_completion_persistence_failure_falls_back_to_failed() -> None:
    repository = CompletionFailureRepository()
    record = _pending_record()
    await repository.add(record)

    predictor = StubPredictor(
        result=PredictionResult(
            disease_name="synthetic-class-b",
            confidence=0.9123,
        )
    )
    service = PredictionService(
        repository,
        StubImageStorage(),
        predictor,
    )

    await service.process_prediction(record.prediction_id)

    stored = await repository.get(record.prediction_id)
    assert stored is not None
    assert stored.status == PredictionStatus.FAILED
    assert stored.disease is None
    assert stored.confidence is None
    assert stored.error_code == "PERSISTENCE_ERROR"
    assert repository.status_updates == [
        PredictionStatus.PROCESSING,
        PredictionStatus.FAILED,
    ]


@pytest.mark.asyncio
async def test_create_prediction_deletes_file_when_repository_fails() -> None:
    storage = StubImageStorage()
    service = PredictionService(
        FailingPredictionRepository(),
        storage,
        StubPredictor(),
    )
    image = ValidatedImage(
        data=_png_1x1_red(),
        content_type="image/png",
        extension=".png",
        size_bytes=len(_png_1x1_red()),
    )

    with pytest.raises(RuntimeError, match="forced persistence failure"):
        await service.create_prediction(image)

    assert len(storage.saved) == 1
    assert storage.deleted == [("a" * 32) + ".png"]
