"""Dependency-injection wiring.

Routes declare dependencies using the ``Annotated`` aliases below; FastAPI
resolves them per request. Tests can replace any of them via
``app.dependency_overrides``.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.services.disease_service import DiseaseService
from app.services.prediction_service import PredictionService
from app.services.recommendation_service import RecommendationService


# ---------------------------------------------------------------------------
# Application-object dependencies (unchanged from Phase 1)
# ---------------------------------------------------------------------------


def get_app_settings(request: Request) -> Settings:
    """Return the Settings instance the application was created with."""
    return request.app.state.settings


def get_prediction_service(request: Request) -> PredictionService:
    """Return the process-wide prediction service."""
    return request.app.state.prediction_service


def get_disease_service(request: Request) -> DiseaseService:
    """Return the process-wide disease service."""
    return request.app.state.disease_service


def get_recommendation_service(request: Request) -> RecommendationService:
    """Return the process-wide recommendation service."""
    return request.app.state.recommendation_service


# ---------------------------------------------------------------------------
# Database dependencies (added in the Database Integration milestone)
# ---------------------------------------------------------------------------


def get_db_session(request: Request) -> Iterator[Session]:
    """Yield a request-scoped database session.

    Transaction policy: this dependency does NOT commit. The repository (or,
    for read-only endpoints, the query itself) owns commit behaviour. If an
    exception escapes downstream, the session is rolled back before being
    closed so no partial transaction leaks to the next request.
    """
    session_factory: sessionmaker[Session] = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
PredictionServiceDep = Annotated[PredictionService, Depends(get_prediction_service)]
DiseaseServiceDep = Annotated[DiseaseService, Depends(get_disease_service)]
RecommendationServiceDep = Annotated[
    RecommendationService, Depends(get_recommendation_service)
]
DbSessionDep = Annotated[Session, Depends(get_db_session)]
