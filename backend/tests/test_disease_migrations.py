"""Verify that the complete migration history matches the disease model."""
from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_alembic_upgrade_creates_disease_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "disease_migration_test.db"
    db_url = f"sqlite:///{database_path.as_posix()}"

    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", db_url)

    command.upgrade(config, "head")

    engine = create_engine(db_url)
    try:
        inspector = inspect(engine)

        tables = inspector.get_table_names()
        assert "predictions" in tables
        assert "diseases" in tables

        columns = {column["name"] for column in inspector.get_columns("diseases")}
        assert {
            "id",
            "name",
            "display_name",
            "crop",
            "description",
            "symptoms",
            "causes",
            "treatment",
            "severity",
            "created_at",
            "updated_at",
        } <= columns

        unique_constraints = inspector.get_unique_constraints("diseases")
        assert any(
            constraint["name"] == "uq_diseases_name"
            for constraint in unique_constraints
        )
    finally:
        engine.dispose()
