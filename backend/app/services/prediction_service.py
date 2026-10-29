"""Prediction creation, retrieval, and inference lifecycle management."""

from __future__ import annotations

import logging
from dataclasses import replace
from uuid import UUID, uuid4

from starlette.concurrency import run_in_threadpool

from app.core.exceptions import ModelNotAvailableError, PredictionNotFoundError
from app.domain.prediction import PredictionRecord, PredictionStatus
from app.ml.predictor import CropDiseasePredictor, ModelInferenceError
from app.repositories.prediction_repository import PredictionRepository
from app.storage.image_storage import ImageStorage
from app.utils.images import ValidatedImage
from app.utils.time import utcnow

logger = logging.getLogger(__name__)

_IMAGE_UNAVAILABLE = "IMAGE_UNAVAILABLE"
_MODEL_INFERENCE_ERROR = "MODEL_INFERENCE_ERROR"


class PredictionService:
    """Coordinate image storage, prediction persistence, and inference."""

    def __init__(
        self,
        prediction_repository: PredictionRepository | None = None,
        image_storage: ImageStorage | None = None,
        predictor: CropDiseasePredictor | None = None,
        *,
        repository: PredictionRepository | None = None,
        storage: ImageStorage | None = None,
    ) -> None:
        repo = prediction_repository or repository
        stor = image_storage or storage
        if repo is None or stor is None or predictor is None:
            raise ValueError("prediction_repository, image_storage, and predictor are required")
        self._repository = repo
        self._prediction_repository = repo
        self._storage = stor
        self._image_storage = stor
        self._predictor = predictor

    async def create_prediction(
        self,
        image: ValidatedImage,
    ) -> PredictionRecord:
        """Persist a validated upload and create a pending prediction."""
        try:
            if hasattr(image, "data") and hasattr(image, "extension"):
                stored_filename = await run_in_threadpool(
                    self._image_storage.save,
                    image.data,
                    image.extension,
                )
            else:
                stored_filename = await run_in_threadpool(
                    self._image_storage.save,
                    image,
                )
        except TypeError:
            stored_filename = await run_in_threadpool(
                self._image_storage.save,
                image,
            )

        now = utcnow()
        record = PredictionRecord(
            prediction_id=uuid4(),
            status=PredictionStatus.PENDING,
            stored_filename=stored_filename,
            content_type=image.content_type,
            size_bytes=image.size_bytes,
            created_at=now,
            updated_at=now,
            crop=None,
            disease=None,
            confidence=None,
            error_code=None,
        )

        try:
            return await self._prediction_repository.add(record)
        except Exception:
            await run_in_threadpool(
                self._image_storage.delete,
                stored_filename,
            )
            raise

    async def get_prediction(
        self,
        prediction_id: UUID,
    ) -> PredictionRecord:
        """Return a prediction or raise the existing not-found error."""
        record = await self._prediction_repository.get(prediction_id)
        if record is None:
            raise PredictionNotFoundError(f"Prediction '{prediction_id}' does not exist.")
        return record

    async def process_prediction(
        self,
        prediction_id: UUID,
    ) -> None:
        """Process a pending prediction in a FastAPI background task.

        This method deliberately swallows background failures after logging
        their type. A failed persistent update is not allowed to escape as an
        unhandled background-task exception.
        """
        try:
            record = await self._prediction_repository.get(prediction_id)
        except Exception as exc:
            logger.error(
                "Could not load prediction %s for processing (%s).",
                prediction_id,
                type(exc).__name__,
            )
            return

        if record is None:
            logger.warning(
                "Prediction %s disappeared before processing.",
                prediction_id,
            )
            return

        if record.status is not PredictionStatus.PENDING:
            return

        try:
            model_ready = await self._predictor.warm_up()
        except Exception as exc:
            logger.error(
                "Model warm-up failed for prediction %s (%s).",
                prediction_id,
                type(exc).__name__,
            )
            return

        if not model_ready:
            # Preserve the existing pending contract when no compatible
            # trained model has been configured.
            logger.info(
                "Prediction %s remains pending because the ML model is unavailable.",
                prediction_id,
            )
            return

        processing_record = replace(
            record,
            status=PredictionStatus.PROCESSING,
            updated_at=utcnow(),
        )

        try:
            await self._prediction_repository.update(processing_record)
        except Exception as exc:
            logger.error(
                "Could not mark prediction %s as processing (%s).",
                prediction_id,
                type(exc).__name__,
            )
            return

        try:
            image_bytes = await run_in_threadpool(
                self._image_storage.read_bytes,
                processing_record.stored_filename,
            )
        except Exception as exc:
            logger.error(
                "Stored image for prediction %s could not be read (%s).",
                prediction_id,
                type(exc).__name__,
            )
            await self._mark_failed(
                processing_record,
                _IMAGE_UNAVAILABLE,
            )
            return

        try:
            result = await self._predictor.predict(image_bytes)
        except ModelNotAvailableError:
            # The model became unavailable after the readiness check.
            # Return to the established pending state rather than claiming
            # that inference completed or failed on a real image.
            await self._reset_to_pending(processing_record)
            return
        except ModelInferenceError as exc:
            logger.error(
                "Inference failed for prediction %s (%s).",
                prediction_id,
                type(exc).__name__,
            )
            await self._mark_failed(
                processing_record,
                _MODEL_INFERENCE_ERROR,
            )
            return
        except Exception as exc:
            logger.error(
                "Unexpected inference failure for prediction %s (%s).",
                prediction_id,
                type(exc).__name__,
            )
            await self._mark_failed(
                processing_record,
                _MODEL_INFERENCE_ERROR,
            )
            return

        completed_record = replace(
            processing_record,
            status=PredictionStatus.COMPLETED,
            crop="wheat",
            disease=result.disease_name,
            confidence=result.confidence,
            error_code=None,
            updated_at=utcnow(),
        )

        try:
            await self._prediction_repository.update(completed_record)
        except Exception as exc:
            logger.error(
                "Could not persist completion for prediction %s (%s).",
                prediction_id,
                type(exc).__name__,
            )

    async def _mark_failed(
        self,
        record: PredictionRecord,
        error_code: str,
    ) -> None:
        failed_record = replace(
            record,
            status=PredictionStatus.FAILED,
            disease=None,
            confidence=None,
            error_code=error_code,
            updated_at=utcnow(),
        )

        try:
            await self._prediction_repository.update(failed_record)
        except Exception as exc:
            logger.error(
                "Could not persist failure state for prediction %s (%s).",
                record.prediction_id,
                type(exc).__name__,
            )

    async def _reset_to_pending(
        self,
        record: PredictionRecord,
    ) -> None:
        pending_record = replace(
            record,
            status=PredictionStatus.PENDING,
            disease=None,
            confidence=None,
            error_code=None,
            updated_at=utcnow(),
        )

        try:
            await self._prediction_repository.update(pending_record)
        except Exception as exc:
            logger.error(
                "Could not restore pending state for prediction %s (%s).",
                record.prediction_id,
                type(exc).__name__,
            )
