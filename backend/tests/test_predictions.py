"""Tests for the prediction upload + status endpoints."""
from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings

PREDICTIONS_URL = "/api/v1/predictions"
_GENERATED_NAME_RE = re.compile(r"^[0-9a-f]{32}\.(jpg|png|webp)$")


# ---------------------------------------------------------------------------
# POST /api/v1/predictions — happy path
# ---------------------------------------------------------------------------


def test_upload_valid_image_returns_201_with_pending_status(
    client: TestClient, png_bytes: bytes
) -> None:
    files = {"image": ("my leaf photo.png", png_bytes, "image/png")}

    response = client.post(PREDICTIONS_URL, files=files)

    assert response.status_code == 201
    body = response.json()

    assert body["status"] == "pending"
    uuid.UUID(body["prediction_id"])                       # parseable UUID
    assert _GENERATED_NAME_RE.fullmatch(body["filename"])  # server-generated name
    assert "/" not in body["filename"] and "\\" not in body["filename"]


def test_uploaded_image_is_stored_under_generated_name(
    client: TestClient, app_settings: Settings, png_bytes: bytes
) -> None:
    body = client.post(
        PREDICTIONS_URL,
        files={"image": ("../evil path.png", png_bytes, "image/png")},
    ).json()

    stored_path: Path = app_settings.upload_dir / body["filename"]
    assert stored_path.is_file()
    assert stored_path.read_bytes() == png_bytes


def test_uploaded_prediction_is_persisted_in_the_database(
    client: TestClient, png_bytes: bytes
) -> None:
    """The 201 response and the DB row describe the same record."""
    created = client.post(
        PREDICTIONS_URL, files={"image": ("leaf.png", png_bytes, "image/png")}
    ).json()

    # A subsequent GET (which reads from the DB) must return the same record.
    fetched = client.get(f"{PREDICTIONS_URL}/{created['prediction_id']}").json()
    assert fetched["prediction_id"] == created["prediction_id"]
    assert fetched["status"] == "pending"


# ---------------------------------------------------------------------------
# POST /api/v1/predictions — rejections
# ---------------------------------------------------------------------------


def test_upload_rejects_unsupported_content_type(client: TestClient) -> None:
    response = client.post(
        PREDICTIONS_URL, files={"image": ("notes.txt", b"hello", "text/plain")}
    )

    assert response.status_code == 415
    error = response.json()["error"]
    assert error["code"] == "INVALID_IMAGE"


def test_upload_rejects_fake_image_content(client: TestClient) -> None:
    """Declared as PNG but the bytes are not a PNG — rejected by magic bytes."""
    response = client.post(
        PREDICTIONS_URL,
        files={"image": ("fake.png", b"this is not an image", "image/png")},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "INVALID_IMAGE"


def test_upload_rejects_empty_file(client: TestClient) -> None:
    response = client.post(
        PREDICTIONS_URL, files={"image": ("empty.png", b"", "image/png")}
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "INVALID_IMAGE"


def test_upload_rejects_oversized_image(client: TestClient) -> None:
    # conftest sets max_upload_size_mb = 1
    oversized = b"\x89PNG\r\n\x1a\n" + b"\x00" * (1024 * 1024 + 1)

    response = client.post(
        PREDICTIONS_URL, files={"image": ("big.png", oversized, "image/png")}
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_upload_missing_image_field_returns_422(
    client: TestClient, png_bytes: bytes
) -> None:
    response = client.post(
        PREDICTIONS_URL, files={"photo": ("leaf.png", png_bytes, "image/png")}
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["details"]


# ---------------------------------------------------------------------------
# GET /api/v1/predictions/{prediction_id}
# ---------------------------------------------------------------------------


def test_get_prediction_returns_pending_record(
    client: TestClient, png_bytes: bytes
) -> None:
    created = client.post(
        PREDICTIONS_URL, files={"image": ("leaf.png", png_bytes, "image/png")}
    ).json()

    response = client.get(f"{PREDICTIONS_URL}/{created['prediction_id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["prediction_id"] == created["prediction_id"]
    assert body["status"] == "pending"
    # No fake results before the ML model is connected:
    assert body["crop"] is None
    assert body["disease"] is None
    assert body["confidence"] is None
    assert "created_at" in body


def test_get_prediction_unknown_id_returns_404(client: TestClient) -> None:
    response = client.get(f"{PREDICTIONS_URL}/{uuid.uuid4()}")

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "PREDICTION_NOT_FOUND"
    assert set(error) >= {"code", "message", "details"}


def test_get_prediction_malformed_id_returns_422(client: TestClient) -> None:
    response = client.get(f"{PREDICTIONS_URL}/not-a-uuid")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
