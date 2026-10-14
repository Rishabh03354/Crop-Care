"""Application error types and global FastAPI exception handlers.

Every deliberate failure raises an ``AppError`` subclass; the handlers below
map them to ONE uniform JSON envelope:

    {
      "error": {
        "code": "INVALID_IMAGE",
        "message": "...",
        "details": null
      }
    }
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error types — codes and statuses are part of the public API contract.
# ---------------------------------------------------------------------------


class AppError(Exception):
    """Base class for errors the application raises deliberately."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "INTERNAL_ERROR"
    default_message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class InvalidImageError(AppError):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    code = "INVALID_IMAGE"
    default_message = "Uploaded file is not a supported image."


class FileTooLargeError(AppError):
    status_code = getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413)
    code = "FILE_TOO_LARGE"
    default_message = "Uploaded file exceeds the maximum allowed size."


class PredictionNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "PREDICTION_NOT_FOUND"
    default_message = "The requested prediction does not exist."


class DiseaseNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "DISEASE_NOT_FOUND"
    default_message = "The requested disease is not in the catalogue."


class ModelNotAvailableError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "MODEL_NOT_AVAILABLE"
    default_message = "The disease prediction model is not available."


class NotImplementedFeatureError(AppError):
    status_code = status.HTTP_501_NOT_IMPLEMENTED
    code = "NOT_IMPLEMENTED"
    default_message = "This feature is not implemented yet."


FeatureNotImplementedError = NotImplementedFeatureError


class StorageError(AppError):
    """Internal storage failure. Never leaks filesystem paths to clients."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "STORAGE_ERROR"
    default_message = "The uploaded file could not be stored."


# ---------------------------------------------------------------------------
# Database errors (added in the Database Integration milestone)
# ---------------------------------------------------------------------------


class DatabaseNotConfiguredError(AppError):
    """Raised when DATABASE_URL is missing at app startup."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "DATABASE_NOT_CONFIGURED"
    default_message = "The database is not configured."


class DatabaseUnavailableError(AppError):
    """Raised when the database cannot be reached (e.g. /health/db)."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "DATABASE_UNAVAILABLE"
    default_message = "The database is currently unavailable."


class PersistenceError(AppError):
    """Raised when a database write fails for a reason other than 'not found'.

    The cause (an ``SQLAlchemyError``) is chained on the server side for logs,
    but the client only ever sees the sanitised default message.
    """

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "PERSISTENCE_ERROR"
    default_message = "The record could not be saved."


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

_HTTP_CODE_MAP: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
}


def _envelope(code: str, message: str, details: Any = None) -> dict[str, Any]:
    """Build the standard error envelope (details always present)."""
    return {"error": {"code": code, "message": message, "details": details}}


def register_exception_handlers(app: FastAPI) -> None:
    """Attach the global exception handlers to the application."""

    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "%s %s -> %s (%s)",
            request.method,
            request.url.path,
            exc.status_code,
            exc.code,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            content=_envelope(
                "VALIDATION_ERROR",
                "Request validation failed.",
                jsonable_encoder(exc.errors()),
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        code = _HTTP_CODE_MAP.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(code, message),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope("INTERNAL_ERROR", "Internal server error."),
        )
