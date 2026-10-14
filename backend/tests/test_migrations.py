"""Verify the initial Alembic migration matches the SQLAlchemy models.

If this test ever fails, the migration and the ORM model have drifted apart
and you need to generate a new migration.
"""
from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

PROJECT_ROOT = Path(__file__).resolve().parent.parent

_EXPECTED_COLUMNS = {
    "id",
    "image_path",
    "content_type",
    "size_bytes",
    "status",
    "crop_name",
    "disease_name",
    "confidence",
    "error_code",
    "created_at",
    "updated_at",
}


def test_initial_migration_creates_predictions_table(tmp_path: Path) -> None:
    """Run `alembic upgrade head` and check the resulting schema."""
    db_url = f"sqlite:///{tmp_path / 'migration.db'}"

    cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)

    command.upgrade(cfg, "head")

    engine = create_engine(db_url)
    try:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        assert "predictions" in table_names

        columns = {col["name"] for col in inspector.get_columns("predictions")}
        assert _EXPECTED_COLUMNS <= columns

        index_names = {idx["name"] for idx in inspector.get_indexes("predictions")}
        assert {"ix_predictions_status", "ix_predictions_created_at"} <= index_names
    finally:
        engine.dispose()
