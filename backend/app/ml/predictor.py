"""Image prediction interface backed by a configured model loader."""

from __future__ import annotations

import io
import math
from collections.abc import Sequence
from dataclasses import dataclass

from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.core.exceptions import ModelNotAvailableError
from app.ml.model_loader import LoadedModel, ModelLoader


class ModelInferenceError(RuntimeError):
    """Raised when a loaded model cannot produce a valid prediction."""


@dataclass(frozen=True, slots=True)
class PredictionResult:
    """A single real model result."""

    disease_name: str
    confidence: float


def _select_top_prediction(
    scores: Sequence[float],
    class_labels: Sequence[str],
) -> PredictionResult:
    """Validate model scores and select the highest-scoring class."""

    if not scores:
        raise ModelInferenceError("model returned no class scores")

    if len(scores) != len(class_labels):
        raise ModelInferenceError(
            "model output size does not match the configured class labels"
        )

    best_index = max(range(len(scores)), key=lambda index: scores[index])
    confidence = float(scores[best_index])

    if not math.isfinite(confidence):
        raise ModelInferenceError("model returned a non-finite confidence score")

    if not 0.0 <= confidence <= 1.0:
        raise ModelInferenceError(
            "model returned a confidence score outside the range 0..1"
        )

    return PredictionResult(
        disease_name=str(class_labels[best_index]),
        confidence=round(confidence, 4),
    )


class CropDiseasePredictor:
    """Application-facing predictor.

    The predictor does not know about HTTP, PostgreSQL, or image storage.
    It receives image bytes and returns a validated model result.
    """

    def __init__(self, model_loader: ModelLoader | None = None) -> None:
        self._model_loader = model_loader if model_loader is not None else ModelLoader(Settings())

    @property
    def configured(self) -> bool:
        return self._model_loader.configured

    @property
    def is_available(self) -> bool:
        return self._model_loader.is_available

    async def warm_up(self) -> bool:
        """Load the model once if configured and report availability."""

        return await run_in_threadpool(self._warm_up_sync)

    def _warm_up_sync(self) -> bool:
        self._model_loader.load()
        return self._model_loader.is_available

    async def predict(self, image_bytes: bytes) -> PredictionResult:
        """Run inference on already-validated image bytes."""

        if not isinstance(image_bytes, (bytes, bytearray)) or not image_bytes:
            raise ModelInferenceError("image data is empty or invalid")

        loaded = await run_in_threadpool(self._model_loader.load)
        if loaded is None:
            raise ModelNotAvailableError()

        return await run_in_threadpool(
            self._predict_with_loaded_model,
            loaded,
            bytes(image_bytes),
        )

    def _predict_with_loaded_model(
        self,
        loaded: LoadedModel,
        image_bytes: bytes,
    ) -> PredictionResult:
        try:
            import numpy as np
            import torch
            from PIL import Image
        except ImportError as exc:
            raise ModelInferenceError(
                "inference dependencies are unavailable"
            ) from exc

        manifest = loaded.manifest
        input_spec = manifest.input

        try:
            with Image.open(io.BytesIO(image_bytes)) as source_image:
                rgb_image = source_image.convert("RGB")
                resized = rgb_image.resize(
                    (input_spec.width, input_spec.height),
                    Image.Resampling.BILINEAR,
                )
                pixels = np.asarray(resized, dtype=np.float32) / 255.0
        except Exception as exc:
            raise ModelInferenceError(
                "uploaded image could not be preprocessed"
            ) from exc

        mean = np.asarray(input_spec.mean, dtype=np.float32).reshape(1, 1, 3)
        std = np.asarray(input_spec.std, dtype=np.float32).reshape(1, 1, 3)
        normalized = (pixels - mean) / std
        contiguous = np.ascontiguousarray(normalized)

        try:
            tensor = torch.from_numpy(contiguous).permute(2, 0, 1).unsqueeze(0)
            tensor = tensor.to(torch.device(loaded.device))

            with torch.inference_mode():
                output = loaded.model(tensor)
        except Exception as exc:
            raise ModelInferenceError("model inference failed") from exc

        if not hasattr(output, "detach"):
            raise ModelInferenceError("model output format is not supported")

        try:
            scores_tensor = output.detach().to(
                device="cpu",
                dtype=torch.float32,
            )
        except Exception as exc:
            raise ModelInferenceError(
                "model output could not be converted to scores"
            ) from exc

        if scores_tensor.ndim == 2:
            if scores_tensor.shape[0] != 1:
                raise ModelInferenceError(
                    "model output contains an unsupported batch size"
                )
            scores_tensor = scores_tensor.squeeze(0)

        if scores_tensor.ndim != 1:
            raise ModelInferenceError(
                "model output must be a one-dimensional score vector"
            )

        if scores_tensor.numel() != len(manifest.class_labels):
            raise ModelInferenceError(
                "model output size does not match the configured class labels"
            )

        if manifest.output_activation == "softmax":
            scores_tensor = torch.softmax(scores_tensor, dim=0)

        scores = scores_tensor.tolist()
        return _select_top_prediction(scores, manifest.class_labels)
