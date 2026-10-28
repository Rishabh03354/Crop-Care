"""Predictor boundary and output-mapping tests."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.exceptions import ModelNotAvailableError
from app.ml.model_loader import ModelLoader
from app.ml.predictor import (
    CropDiseasePredictor,
    ModelInferenceError,
    _select_top_prediction,
)


def test_highest_score_maps_to_authoritative_label() -> None:
    result = _select_top_prediction(
        [0.05, 0.9, 0.05],
        ["synthetic-a", "synthetic-b", "synthetic-c"],
    )

    assert result.disease_name == "synthetic-b"
    assert result.confidence == 0.9


def test_confidence_outside_probability_range_is_rejected() -> None:
    with pytest.raises(ModelInferenceError):
        _select_top_prediction(
            [1.4, -0.4],
            ["synthetic-a", "synthetic-b"],
        )


def test_output_size_must_match_label_count() -> None:
    with pytest.raises(ModelInferenceError):
        _select_top_prediction(
            [0.25, 0.75],
            ["synthetic-a"],
        )


@pytest.mark.asyncio
async def test_predictor_raises_when_no_model_is_configured() -> None:
    settings = Settings(
        _env_file=None,
        database_url="sqlite://",
        model_artifact_path="",
        model_manifest_path="",
        model_device="cpu",
        model_warmup=False,
    )
    predictor = CropDiseasePredictor(ModelLoader(settings))

    with pytest.raises(ModelNotAvailableError):
        await predictor.predict(b"synthetic-image-bytes")
