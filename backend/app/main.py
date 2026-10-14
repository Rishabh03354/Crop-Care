"""FastAPI application entry point.

Run locally:
    uvicorn app.main:app --reload --port 8000

The application is built by ``create_app()`` (factory pattern) so tests can
build isolated instances with custom ``Settings``.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.router import api_v1_router
from app.core.config import Settings, get_settings
from app.core.exceptions import DatabaseNotConfiguredError, register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestLoggingMiddleware
from app.database.connection import (
    create_db_engine,
    create_session_factory,
    describe_database,
    ping_database,
)
from app.ml.predictor import CropDiseasePredictor
from app.repositories.disease_repository import InMemoryDiseaseRepository
from app.repositories.prediction_repository import SqlPredictionRepository
from app.services.disease_service import DiseaseService
from app.services.prediction_service import PredictionService
from app.services.recommendation_service import RecommendationService
from app.storage.image_storage import ImageStorage

logger = logging.getLogger(__name__)

_OPENAPI_TAGS = [
    {"name": "health", "description": "Service and database liveness."},
    {"name": "predictions", "description": "Upload crop images and track prediction requests."},
    {"name": "diseases", "description": "Disease information catalogue."},
    {
        "name": "recommendations",
        "description": (
            "Treatment recommendations. Contract-only for now: valid requests "
            "return 501 NOT_IMPLEMENTED until the engine is connected."
        ),
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown logic (replaces the deprecated ``on_event`` hooks)."""
    settings: Settings = app.state.settings
    storage: ImageStorage = app.state.storage

    storage.ensure_ready()
    app.state.predictor.warm_up()

    logger.info(
        "Starting %s v%s (environment=%s)",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    # Safe to log — never contains the password.
    logger.info("Database target: %s", describe_database(settings.database_url))

    # Best-effort connectivity check. Never crashes the app: if PostgreSQL is
    # temporarily unavailable, /health/db reports it while the app stays up.
    try:
        ping_database(app.state.engine)
        logger.info("Database connection OK.")
    except SQLAlchemyError as exc:
        logger.error(
            "Database connection FAILED (%s). Check DATABASE_URL and that "
            "PostgreSQL is running.",
            type(exc).__name__,
        )

    yield

    # Release pooled connections on shutdown.
    app.state.engine.dispose()
    logger.info("%s stopped.", settings.app_name)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    # ------------------------------------------------------------------
    # Infrastructure: engine + session factory.
    # No connection is opened here — the engine is lazy.
    # ------------------------------------------------------------------
    engine = create_db_engine(settings)
    session_factory = create_session_factory(engine)

    # ------------------------------------------------------------------
    # Application singletons.
    # ------------------------------------------------------------------
    storage = ImageStorage(settings.upload_dir)
    predictor = CropDiseasePredictor()

    prediction_service = PredictionService(
        repository=SqlPredictionRepository(session_factory),
        storage=storage,
        predictor=predictor,
    )
    disease_service = DiseaseService(repository=InMemoryDiseaseRepository())
    recommendation_service = RecommendationService()

    app = FastAPI(
        title="Crop Care Crop API",
        description="AI-powered crop disease detection and recommendation backend.",
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        openapi_tags=_OPENAPI_TAGS,
    )

    # Expose process-wide objects to the dependency layer.
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.storage = storage
    app.state.predictor = predictor
    app.state.prediction_service = prediction_service
    app.state.disease_service = disease_service
    app.state.recommendation_service = recommendation_service

    # Middleware — last added runs first (outermost). CORS outermost so
    # preflight requests and error responses always carry CORS headers.
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    return app


try:
    app = create_app()
except DatabaseNotConfiguredError:
    # Allows importing create_app in tests and tools when DATABASE_URL is not set.
    # Running `uvicorn app.main:app` still requires DATABASE_URL to be set in .env.
    app = None  # type: ignore[assignment]


if __name__ == "__main__":  # convenience: `python -m app.main`
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
