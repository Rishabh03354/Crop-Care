"""SQLAlchemy ORM model for prediction requests.

The ``predictions`` table stores one row per upload. It holds the *storage
reference* (the filename written by ``ImageStorage``), never the image bytes
and never an absolute filesystem path.

Result columns (``crop_name``, ``disease_name``, ``confidence``) stay NULL
until the ML Integration task connects a real model and updates the row.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.utils.time import utcnow

# The set of statuses is enforced in Python (see app.domain.prediction).
# Stored as VARCHAR(20) so no ALTER TYPE is needed if a new status is added.
_STATUS_MAX_LENGTH = 20


class Prediction(Base):
    """One uploaded crop image and the state of its prediction request."""

    __tablename__ = "predictions"

    # --- Identity ---
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # --- Uploaded image storage reference ---
    image_path: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Lifecycle ---
    status: Mapped[str] = mapped_column(
        String(_STATUS_MAX_LENGTH),
        nullable=False,
        default="pending",
        index=True,
    )

    # --- Real ML results (NULL until the model is connected) ---
    crop_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    disease_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)

    # --- Error reporting (set only when status == "failed") ---
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # --- Timestamps ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_predictions_confidence_range",
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover — debugging helper
        return f"<Prediction id={self.id} status={self.status!r}>"
