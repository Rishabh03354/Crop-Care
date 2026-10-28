"""Prediction endpoints: image upload + status tracking."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, File, Path, UploadFile, status

from app.api.deps import PredictionServiceDep, SettingsDep
from app.schemas.common import ErrorResponse
from app.schemas.prediction import PredictionCreatedResponse, PredictionResponse
from app.utils.images import read_validated_image

router = APIRouter(prefix="/predictions", tags=["predictions"])

ImageUpload = Annotated[
    UploadFile,
    File(description="Crop or leaf image. Allowed types: JPEG, PNG, WebP."),
]

PredictionId = Annotated[
    UUID,
    Path(description="Prediction request id (UUID)."),
]


@router.post(
    "",
    response_model=PredictionCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a crop image for disease prediction",
    description=(
        "Validates and stores the uploaded image, creates a prediction request "
        "and returns its id together with the generated filename. Inference runs "
        "once the ML model is connected — track progress via GET /predictions/{id}."
    ),
    responses={
        getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413): {
            "model": ErrorResponse,
            "description": "Image exceeds the size limit",
        },
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {
            "model": ErrorResponse,
            "description": "Not a supported image",
        },
        getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422): {
            "model": ErrorResponse,
            "description": "Missing or malformed request",
        },
    },
)
async def create_prediction(
    image: ImageUpload,
    background_tasks: BackgroundTasks,
    settings: SettingsDep,
    service: PredictionServiceDep,
) -> PredictionCreatedResponse:
    """Upload an image and create a prediction request."""
    validated = await read_validated_image(
        image, max_size_bytes=settings.max_upload_size_bytes
    )
    record = await service.create_prediction(validated)
    background_tasks.add_task(
        service.process_prediction,
        record.prediction_id,
    )
    return PredictionCreatedResponse(
        prediction_id=record.prediction_id,
        status=record.status,
        filename=record.stored_filename,
    )


@router.get(
    "/{prediction_id}",
    response_model=PredictionResponse,
    summary="Get a prediction request by id",
    description=(
        "Returns the lifecycle status of a prediction. `crop`, `disease` and "
        "`confidence` stay null until the status is 'completed'."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Unknown prediction id",
        },
        getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422): {
            "model": ErrorResponse,
            "description": "Malformed prediction id",
        },
    },
)
async def get_prediction(
    prediction_id: PredictionId,
    service: PredictionServiceDep,
) -> PredictionResponse:
    """Return the current state of one prediction request."""
    record = await service.get_prediction(prediction_id)
    return PredictionResponse.from_record(record)
