"""Domain types for the prediction lifecycle."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class PredictionStatus(str, Enum):
    """Lifecycle states of a prediction request.

    pending    — upload accepted and stored; inference has not run yet
    processing — the future ML worker is analysing the image (reserved)
    completed  — a real prediction result is available
    failed     — processing stopped; ``error_code`` explains why

    Note: Phase 1 used the value ``received`` for the initial state. It has
    been renamed to ``pending`` here so that the API vocabulary matches the
    database vocabulary. This is the only intentional contract change.
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PredictionRecord:
    """One prediction request and its lifecycle state (storage-agnostic).

    This is what the service layer exchanges with the repository. It is
    deliberately *not* the API schema and *not* the ORM model — the three
    shapes can evolve independently.
    """

    prediction_id: UUID
    status: PredictionStatus
    stored_filename: str          # server-generated; never the client's filename
    content_type: str
    size_bytes: int
    created_at: datetime
    updated_at: datetime
    # Filled only when status == COMPLETED (produced by the real model):
    crop: str | None = None
    disease: str | None = None
    confidence: float | None = None
    # Filled only when status == FAILED:
    error_code: str | None = None
