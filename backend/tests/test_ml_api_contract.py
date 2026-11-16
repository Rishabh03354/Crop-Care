"""API contract tests for the ML-backed prediction workflow."""

from __future__ import annotations

import asyncio
import re
import struct
import time
import uuid
import zlib
from uuid import UUID

import pytest

from app.domain.prediction import PredictionRecord, PredictionStatus
from app.ml.predictor import (
    CropDiseasePredictor,
    ModelInferenceError,
    PredictionResult,
)
from app.repositories.prediction_repository import SqlPredictionRepository
from app.services.prediction_service import PredictionService
from app.utils.time import utcnow


def _chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(
            ">I",
            zlib.crc32(kind + data) & 0xFFFFFFFF,
        )
    )


def _png_1x1_red() -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"
    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    image_data = zlib.compress(b"\x00\xff\x00\x00")

    return (
        signature
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", image_data)
        + _chunk(b"IEND", b"")
    )


def _post_png(client):
    return client.post(
        "/api/v1/predictions",
        files={
            "image": (
                "leaf.png",
                _png_1x1_red(),
                "image/png",
            )
        },
    )


def _wait_for_status(
    client,
    prediction_id: str,
    expected_status: str,
    *,
    attempts: int = 20,
):
    response = client.get(
        f"/api/v1/predictions/{prediction_id}"
    )

    for _ in range(attempts):
        if response.status_code == 200:
            if response.json().get("status") == expected_status:
                return response
        time.sleep(0.05)
        response = client.get(
            f"/api/v1/predictions/{prediction_id}"
        )

    return response


def test_health_contract_unchanged(client) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "crop-care-backend",
    }


def test_upload_returns_pending_with_generated_filename(client) -> None:
    response = _post_png(client)

    assert response.status_code == 201
    body = response.json()

    assert body["status"] == "pending"
    uuid.UUID(body["prediction_id"])
    assert re.fullmatch(
        r"[0-9a-f]{32}\.(jpg|png|webp)",
        body["filename"],
    )
    assert "leaf.png" not in body["filename"]


def test_upload_schedules_background_processing(
    client,
    monkeypatch,
) -> None:
    called_prediction_ids: list[UUID] = []

    async def fake_process_prediction(self, prediction_id: UUID) -> None:
        called_prediction_ids.append(prediction_id)

    monkeypatch.setattr(
        PredictionService,
        "process_prediction",
        fake_process_prediction,
    )

    response = _post_png(client)

    assert response.status_code == 201
    body = response.json()

    assert len(called_prediction_ids) == 1
    assert str(called_prediction_ids[0]) == body["prediction_id"]


def test_mocked_inference_completes_and_is_retrievable(
    client,
    monkeypatch,
) -> None:
    async def fake_warm_up(self) -> bool:
        return True

    async def fake_predict(self, image_bytes: bytes) -> PredictionResult:
        assert image_bytes
        return PredictionResult(
            disease_name="synthetic-class-b",
            confidence=0.9123,
        )

    monkeypatch.setattr(
        CropDiseasePredictor,
        "warm_up",
        fake_warm_up,
    )
    monkeypatch.setattr(
        CropDiseasePredictor,
        "predict",
        fake_predict,
    )

    upload_response = _post_png(client)
    assert upload_response.status_code == 201
    upload_body = upload_response.json()
    assert upload_body["status"] == "pending"

    detail_response = _wait_for_status(
        client,
        upload_body["prediction_id"],
        "completed",
    )

    assert detail_response.status_code == 200
    detail_body = detail_response.json()

    assert detail_body["prediction_id"] == upload_body["prediction_id"]
    assert detail_body["status"] == "completed"
    assert detail_body["disease"] == "synthetic-class-b"
    assert detail_body["confidence"] == 0.9123


def test_unavailable_model_leaves_record_pending(
    client,
    monkeypatch,
) -> None:
    warm_up_calls: list[None] = []

    async def fake_warm_up(self) -> bool:
        warm_up_calls.append(None)
        return False

    async def fake_predict(self, image_bytes: bytes) -> PredictionResult:
        raise AssertionError(
            "predict must not be called when the model is unavailable"
        )

    monkeypatch.setattr(
        CropDiseasePredictor,
        "warm_up",
        fake_warm_up,
    )
    monkeypatch.setattr(
        CropDiseasePredictor,
        "predict",
        fake_predict,
    )

    upload_response = _post_png(client)
    assert upload_response.status_code == 201
    prediction_id = upload_response.json()["prediction_id"]

    detail_response = client.get(
        f"/api/v1/predictions/{prediction_id}"
    )

    assert detail_response.status_code == 200
    detail_body = detail_response.json()

    assert detail_body["status"] == "pending"
    assert detail_body["disease"] is None
    assert detail_body["confidence"] is None
    assert len(warm_up_calls) == 1


def test_inference_failure_is_persisted(
    client,
    app,
    monkeypatch,
) -> None:
    async def fake_warm_up(self) -> bool:
        return True

    async def fake_predict(self, image_bytes: bytes) -> PredictionResult:
        raise ModelInferenceError("forced inference failure")

    monkeypatch.setattr(
        CropDiseasePredictor,
        "warm_up",
        fake_warm_up,
    )
    monkeypatch.setattr(
        CropDiseasePredictor,
        "predict",
        fake_predict,
    )

    upload_response = _post_png(client)
    assert upload_response.status_code == 201
    prediction_id = upload_response.json()["prediction_id"]

    detail_response = _wait_for_status(
        client,
        prediction_id,
        "failed",
    )

    assert detail_response.status_code == 200
    detail_body = detail_response.json()

    assert detail_body["status"] == "failed"
    assert detail_body["disease"] is None
    assert detail_body["confidence"] is None

    session_factory = getattr(app.state, "session_factory", None)
    if session_factory is not None:
        repository = SqlPredictionRepository(session_factory)
        record = asyncio.run(
            repository.get(UUID(prediction_id))
        )

        assert record is not None
        assert record.status == PredictionStatus.FAILED
        assert record.error_code == "MODEL_INFERENCE_ERROR"


def test_get_returns_persisted_completed_record(
    client,
    app,
) -> None:
    session_factory = getattr(app.state, "session_factory", None)
    if session_factory is None:
        pytest.skip(
            "app.state.session_factory is not exposed by the current app"
        )

    repository = SqlPredictionRepository(session_factory)
    now = utcnow()

    record = PredictionRecord(
        prediction_id=uuid.uuid4(),
        status=PredictionStatus.COMPLETED,
        stored_filename=("b" * 32) + ".png",
        content_type="image/png",
        size_bytes=128,
        created_at=now,
        updated_at=now,
        crop=None,
        disease="synthetic-completed-class",
        confidence=0.8123,
        error_code=None,
    )

    asyncio.run(repository.add(record))

    response = client.get(
        f"/api/v1/predictions/{record.prediction_id}"
    )

    assert response.status_code == 200
    body = response.json()

    assert body["prediction_id"] == str(record.prediction_id)
    assert body["status"] == "completed"
    assert body["disease"] == "synthetic-completed-class"
    assert body["confidence"] == 0.8123


def test_unknown_prediction_returns_existing_error_envelope(
    client,
) -> None:
    response = client.get(
        f"/api/v1/predictions/{uuid.uuid4()}"
    )

    assert response.status_code == 404
    body = response.json()

    assert body["error"]["code"] == "PREDICTION_NOT_FOUND"
    assert set(body["error"]) == {
        "code",
        "message",
        "details",
    }


def test_malformed_prediction_id_returns_validation_error(
    client,
) -> None:
    response = client.get(
        "/api/v1/predictions/not-a-uuid"
    )

    assert response.status_code == 422
    body = response.json()

    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert set(body["error"]) == {
        "code",
        "message",
        "details",
    }


def test_invalid_image_signature_is_rejected(client) -> None:
    response = client.post(
        "/api/v1/predictions",
        files={
            "image": (
                "renamed.png",
                b"this is not a real image",
                "image/png",
            )
        },
    )

    assert response.status_code == 415
    body = response.json()

    assert body["error"]["code"] == "INVALID_IMAGE"
    assert set(body["error"]) == {
        "code",
        "message",
        "details",
    }


def test_missing_image_field_returns_validation_error(
    client,
) -> None:
    response = client.post(
        "/api/v1/predictions",
        files={
            "note": (
                "note.txt",
                b"not an image",
                "text/plain",
            )
        },
    )

    assert response.status_code == 422
    body = response.json()

    assert body["error"]["code"] == "VALIDATION_ERROR"
