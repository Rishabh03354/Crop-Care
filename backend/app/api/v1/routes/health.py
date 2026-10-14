"""Health endpoints.

- ``GET /api/v1/health``    — liveness. Contract unchanged from Phase 1.
- ``GET /api/v1/health/db`` — database reachability probe (additive).
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DbSessionDep, SettingsDep
from app.core.exceptions import DatabaseUnavailableError
from app.schemas.common import ErrorResponse
from app.schemas.health import DbHealthResponse, HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
    description="Liveness probe used by the frontend, CI and monitoring.",
)
async def health_check(settings: SettingsDep) -> HealthResponse:
    """Return the liveness payload."""
    return HealthResponse(status="ok", service=settings.app_name)


@router.get(
    "/health/db",
    response_model=DbHealthResponse,
    summary="Database health check",
    description=(
        "Runs ``SELECT 1`` against the configured database. Returns 503 "
        "``DATABASE_UNAVAILABLE`` if the database cannot be reached. This "
        "endpoint is additive — ``/health`` keeps its original shape."
    ),
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "Database is unreachable.",
        },
    },
)
def health_db(db: DbSessionDep) -> DbHealthResponse:
    """Check database connectivity.

    Declared as ``def`` (not ``async def``) so FastAPI runs it in a worker
    thread — the blocking DB call never touches the event loop.
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.warning("Database health check failed (%s).", type(exc).__name__)
        raise DatabaseUnavailableError() from exc
    return DbHealthResponse(status="ok", database="reachable")
