"""Shared pytest fixtures.

Isolation guarantees:
  * a fresh SQLite file per test (in pytest's ``tmp_path``) — real PostgreSQL is
    never touched;
  * ``_env_file=None`` so the developer's ``.env`` cannot leak into test runs;
  * a fresh app + upload directory per test;
  * ``Base.metadata.create_all`` (not migrations) so tests stay fast — the
    migration itself is verified separately in ``test_migrations.py``.
"""
from __future__ import annotations

import struct
import zlib
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.database.base import Base
from app.main import create_app


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    payload = chunk_type + data
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + payload + struct.pack(">I", crc)


def make_test_png() -> bytes:
    """Build a genuinely valid 1x1 red PNG without external libraries."""
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw_scanline = b"\x00\xff\x00\x00"   # filter byte + one red RGB pixel
    idat = _png_chunk(b"IDAT", zlib.compress(raw_scanline))
    iend = _png_chunk(b"IEND", b"")
    return signature + ihdr + idat + iend


@pytest.fixture()
def app_settings(tmp_path: Path) -> Settings:
    """Isolated settings pointing at a per-test SQLite database file."""
    db_path = tmp_path / "test.db"
    return Settings(
        _env_file=None,
        database_url=f"sqlite:///{db_path}",
        upload_dir=tmp_path / "uploads",
        max_upload_size_mb=1,
    )


@pytest.fixture()
def app(app_settings: Settings) -> Iterator[FastAPI]:
    """Fresh app instance with the schema created on its isolated SQLite file."""
    application = create_app(app_settings)
    Base.metadata.create_all(application.state.engine)
    try:
        yield application
    finally:
        application.state.engine.dispose()


@pytest.fixture()
def client(app: FastAPI) -> Iterator[TestClient]:
    """TestClient with lifespan startup/shutdown, exactly like a real server run."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def png_bytes() -> bytes:
    """A valid 1x1 PNG image."""
    return make_test_png()
