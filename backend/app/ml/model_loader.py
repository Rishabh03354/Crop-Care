"""Lazy loading of a configured TorchScript image-classification artifact."""

from __future__ import annotations

import json
import logging
import math
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.core.config import Settings

logger = logging.getLogger(__name__)


class ModelInputSpec(BaseModel):
    """Preprocessing values supplied by the model author or training pipeline."""

    model_config = ConfigDict(extra="forbid")

    width: int = Field(gt=0, le=4096)
    height: int = Field(gt=0, le=4096)
    mean: tuple[float, float, float]
    std: tuple[float, float, float]

    @field_validator("mean")
    @classmethod
    def _validate_mean(
        cls,
        value: tuple[float, float, float],
    ) -> tuple[float, float, float]:
        if any(not math.isfinite(item) for item in value):
            raise ValueError("normalization mean values must be finite")
        return value

    @field_validator("std")
    @classmethod
    def _validate_std(
        cls,
        value: tuple[float, float, float],
    ) -> tuple[float, float, float]:
        if any(not math.isfinite(item) or item <= 0 for item in value):
            raise ValueError("normalization std values must be positive and finite")
        return value


class ModelManifest(BaseModel):
    """Authoritative metadata required to interpret the trained model output."""

    model_config = ConfigDict(extra="forbid")

    artifact_format: Literal["torchscript_image_classifier"]
    class_labels: list[str] = Field(min_length=1)
    input: ModelInputSpec
    output_activation: Literal["softmax", "none"]

    @field_validator("class_labels")
    @classmethod
    def _validate_class_labels(cls, labels: list[str]) -> list[str]:
        if any(not label or label != label.strip() for label in labels):
            raise ValueError("class labels must be non-empty and have no outer whitespace")

        if len(set(labels)) != len(labels):
            raise ValueError("class labels must be unique")

        return labels


@dataclass(frozen=True, slots=True)
class LoadedModel:
    """An initialized model and the metadata required to use it."""

    model: Any
    manifest: ModelManifest
    device: str


class _ModelSetupError(RuntimeError):
    """Internal error used to produce a safe unavailable-model reason."""


class ModelLoader:
    """Load one configured model artifact lazily and cache the result.

    The loader never imports PyTorch at module import time. A failed attempt is
    cached until the process restarts so that every web request does not retry
    a missing or incompatible artifact.
    """

    def __init__(self, settings: Settings) -> None:
        self._artifact_path = _configured_path(settings.model_artifact_path)
        self._manifest_path = _configured_path(settings.model_manifest_path)
        self._device = (settings.model_device or "cpu").strip().lower() or "cpu"

        self._lock = threading.Lock()
        self._attempted = False
        self._loaded: LoadedModel | None = None
        self._failure_reason: str | None = None

    @property
    def configured(self) -> bool:
        """Return whether any model configuration was supplied."""

        return self._artifact_path is not None or self._manifest_path is not None

    @property
    def is_available(self) -> bool:
        """Return whether a model has been loaded successfully."""

        return self._loaded is not None

    @property
    def unavailable_reason(self) -> str:
        """Return a safe explanation without exposing database or file secrets."""

        if self._failure_reason:
            return self._failure_reason
        if not self.configured:
            return "ML model artifact and manifest are not configured."
        return "ML model has not been loaded."

    def load(self) -> LoadedModel | None:
        """Load and return the configured model, or return ``None`` safely."""

        with self._lock:
            if self._attempted:
                return self._loaded

            self._attempted = True
            if not self.configured:
                self._failure_reason = "ML model artifact and manifest are not configured."
                return None

            try:
                loaded = self._load_configured()
            except _ModelSetupError as exc:
                self._failure_reason = str(exc)
                logger.warning("ML model unavailable: %s", self._failure_reason)
                return None
            except Exception as exc:
                self._failure_reason = "model initialization failed"
                logger.warning(
                    "ML model unavailable: %s",
                    type(exc).__name__,
                )
                return None

            self._loaded = loaded
            self._failure_reason = None
            logger.info("ML model loaded on device '%s'.", loaded.device)
            return loaded

    def _load_configured(self) -> LoadedModel:
        if self._artifact_path is None or self._manifest_path is None:
            raise _ModelSetupError(
                "model artifact and model manifest must both be configured"
            )

        if not self._artifact_path.is_file():
            raise _ModelSetupError("model artifact file was not found")

        if not self._manifest_path.is_file():
            raise _ModelSetupError("model manifest file was not found")

        manifest = self._read_manifest(self._manifest_path)

        if manifest.artifact_format != "torchscript_image_classifier":
            raise _ModelSetupError("configured model format is not supported")

        model = self._load_backend_model(
            self._artifact_path,
            self._device,
        )

        return LoadedModel(
            model=model,
            manifest=manifest,
            device=self._device,
        )

    @staticmethod
    def _read_manifest(path: Path) -> ModelManifest:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise _ModelSetupError("model manifest could not be read") from exc

        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise _ModelSetupError("model manifest is not valid JSON") from exc

        try:
            return ModelManifest.model_validate(raw)
        except ValidationError as exc:
            raise _ModelSetupError("model manifest is invalid") from exc

    @staticmethod
    def _load_backend_model(path: Path, device: str) -> Any:
        """Load the explicitly configured backend.

        Only TorchScript classifiers are supported in this phase. This is not
        an assumption that the project's eventual model uses TorchScript.
        """

        try:
            import numpy  # noqa: F401
            from PIL import Image  # noqa: F401
            import torch
        except ImportError as exc:
            raise _ModelSetupError(
                "inference dependencies are not installed"
            ) from exc

        if device.startswith("cuda") and not torch.cuda.is_available():
            raise _ModelSetupError("configured CUDA device is unavailable")

        if device.startswith("mps"):
            mps_backend = getattr(torch.backends, "mps", None)
            if mps_backend is None or not mps_backend.is_available():
                raise _ModelSetupError("configured MPS device is unavailable")

        try:
            model = torch.jit.load(str(path), map_location=device)
        except Exception as exc:
            raise _ModelSetupError(
                "model artifact could not be loaded by the TorchScript backend"
            ) from exc

        if not callable(model):
            raise _ModelSetupError("loaded model artifact is not callable")

        try:
            model.eval()
        except Exception as exc:
            raise _ModelSetupError("loaded model could not enter evaluation mode") from exc

        return model


def _configured_path(value: str) -> Path | None:
    normalized = (value or "").strip()
    if not normalized:
        return None
    return Path(normalized).expanduser()
