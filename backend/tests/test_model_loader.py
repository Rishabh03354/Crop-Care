"""Tests for lazy model loading without requiring a real model."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import Settings
from app.ml.model_loader import ModelLoader


def _manifest_payload() -> dict:
    return {
        "artifact_format": "torchscript_image_classifier",
        "class_labels": ["synthetic-class-a", "synthetic-class-b"],
        "input": {
            "width": 32,
            "height": 32,
            "mean": [0.0, 0.0, 0.0],
            "std": [1.0, 1.0, 1.0],
        },
        "output_activation": "softmax",
    }


def _write_model_files(
    tmp_path: Path,
    *,
    write_artifact: bool = True,
    write_manifest: bool = True,
) -> tuple[Path, Path]:
    artifact_path = tmp_path / "model.pt"
    manifest_path = tmp_path / "model_manifest.json"

    if write_artifact:
        artifact_path.write_bytes(b"synthetic non-model test artifact")

    if write_manifest:
        manifest_path.write_text(
            json.dumps(_manifest_payload()),
            encoding="utf-8",
        )

    return artifact_path, manifest_path


def _settings(
    artifact_path: Path,
    manifest_path: Path,
) -> Settings:
    return Settings(
        _env_file=None,
        database_url="sqlite://",
        model_artifact_path=str(artifact_path),
        model_manifest_path=str(manifest_path),
        model_device="cpu",
        model_warmup=False,
    )


def test_missing_artifact_returns_unavailable(tmp_path: Path) -> None:
    artifact_path, manifest_path = _write_model_files(
        tmp_path,
        write_artifact=False,
    )
    loader = ModelLoader(_settings(artifact_path, manifest_path))

    assert loader.load() is None
    assert loader.is_available is False
    assert "not found" in loader.unavailable_reason.lower()


def test_successful_loader_caches_the_model(
    tmp_path: Path,
    monkeypatch,
) -> None:
    artifact_path, manifest_path = _write_model_files(tmp_path)
    loader = ModelLoader(_settings(artifact_path, manifest_path))

    monkeypatch.setattr(
        loader,
        "_load_backend_model",
        lambda path, device: object(),
    )

    first = loader.load()
    second = loader.load()

    assert first is not None
    assert second is first
    assert loader.is_available is True


def test_initialization_error_does_not_leak_exception_text(
    tmp_path: Path,
    monkeypatch,
) -> None:
    artifact_path, manifest_path = _write_model_files(tmp_path)
    loader = ModelLoader(_settings(artifact_path, manifest_path))

    def _raise_failure(path: Path, device: str):
        raise RuntimeError("sensitive-internal-value")

    monkeypatch.setattr(loader, "_load_backend_model", _raise_failure)

    assert loader.load() is None
    assert "sensitive-internal-value" not in loader.unavailable_reason
    assert loader.is_available is False
