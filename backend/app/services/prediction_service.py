"""Prediction lifecycle business logic.

Lifecycle:  pending -> processing -> completed | failed

Where everything plugs in:
  * POST /api/v1/predictions        -> create_prediction()    (status: pending)
  * GET  /api/v1/predictions/{id}   -> get_prediction()
  * process_prediction()            -> called by the future ML worker
"""
from __future__ import annotations

import logging
from uuid import UUID, uuid4

from starlette.concurrency import run_in_threadpool

from app.core.exceptions import AppError, PredictionNotFoundError
from app.domain.prediction import PredictionRecord, PredictionStatus
from app.ml.predictor import CropDiseasePredictor
from app.repositories.prediction_repository import PredictionRepository
from app.storage.image_storage import ImageStorage
from app.utils.images import ValidatedImage
from app.utils.time import utcnow

logger = logging.getLogger(__name__)


class PredictionService:
    """Coordinates the prediction lifecycle."""

    def __init__(
        self,
        repository: PredictionRepository,
        storage: ImageStorage,
        predictor: CropDiseasePredictor,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._predictor = predictor

    async def create_prediction(self, image: ValidatedImage) -> PredictionRecord:
        """Store the validated image and persist a new prediction request.

        The image is written to disk first, then the database row. If the
        database write fails, the orphaned file is deleted so the two stores
        stay consistent.
        """
        stored_filename = self._storage.save(image.data, image.extension)
        now = utcnow()

        record = PredictionRecord(
            prediction_id=uuid4(),
            status=PredictionStatus.PENDING,
            stored_filename=stored_filename,
            content_type=image.content_type,
            size_bytes=image.size_bytes,
            created_at=now,
            updated_at=now,
        )

        try:
            await self._repository.add(record)
        except AppError:
            # Roll back the file write so we don't leak orphaned uploads.
            self._storage.delete(stored_filename)
            raise

        logger.info(
            "Prediction %s created (file=%s, %d bytes, status=%s)",
            record.prediction_id,
            stored_filename,
            image.size_bytes,
            record.status.value,
        )
        return record

    async def get_prediction(self, prediction_id: UUID) -> PredictionRecord:
        """Fetch a prediction record.

        Raises:
            PredictionNotFoundError: when the id is unknown.
        """
        record = await self._repository.get(prediction_id)
        if record is None:
            raise PredictionNotFoundError(f"Prediction '{prediction_id}' does not exist.")
        return record

    async def process_prediction(self, prediction_id: UUID) -> PredictionRecord:
        """Run inference for one stored image and update its record.

        **Not called by any route today.** A prediction worker (FastAPI
        ``BackgroundTasks``, a queue consumer or a cron job) will call this
        once the ML model is connected. Implemented now so the integration
        seam is explicit.
        """
        record = await self.get_prediction(prediction_id)

        record.status = PredictionStatus.PROCESSING
        record.updated_at = utcnow()
        await self._repository.update(record)

        try:
            image_bytes = self._storage.read_bytes(record.stored_filename)
            # Inference is CPU-bound and synchronous: run it off the event loop.
            result = await run_in_threadpool(self._predictor.predict, image_bytes)
        except AppError as exc:
            record.status = PredictionStatus.FAILED
            record.error_code = exc.code
            record.updated_at = utcnow()
            await self._repository.update(record)
            logger.warning(
                "Prediction %s failed (%s): %s", prediction_id, exc.code, exc.message
            )
            return record

        record.status = PredictionStatus.COMPLETED
        record.crop = result.crop
        record.disease = result.disease
        record.confidence = result.confidence
        record.updated_at = utcnow()
        await self._repository.update(record)

        logger.info(
            "Prediction %s completed: %s / %s (%.4f)",
            prediction_id,
            result.crop,
            result.disease,
            result.confidence,
        )
        return record
