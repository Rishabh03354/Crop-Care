"""Schemas for the health endpoints."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness payload returned by ``GET /api/v1/health``."""

    status: Literal["ok"] = "ok"
    service: str = Field(..., examples=["crop-care-backend"])


class DbHealthResponse(BaseModel):
    """Payload returned by ``GET /api/v1/health/db``.

    Reports whether the database answered ``SELECT 1``. Additive endpoint —
    the existing ``/health`` contract is unchanged.
    """

    status: Literal["ok"] = "ok"
    database: Literal["reachable"] = "reachable"
