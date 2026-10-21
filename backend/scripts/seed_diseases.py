"""Idempotently import an authoritative disease catalogue.

Usage:
    python -m scripts.seed_diseases data/wheat_diseases.json --dry-run
    python -m scripts.seed_diseases data/wheat_diseases.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.database.connection import create_db_engine, create_session_factory
from app.domain.disease import DiseaseRecord
from app.repositories.disease_repository import SqlDiseaseRepository


def _optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"'{field_name}' must be a string or null")
    normalized = value.strip()
    return normalized or None


def _string_list(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"'{field_name}' must be a list of strings")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"'{field_name}' must contain only strings")
    return tuple(
        item.strip()
        for item in value
        if item.strip()
    )


def load_records(path: Path) -> list[DiseaseRecord]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Catalogue file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("Catalogue file is not valid JSON") from exc

    if not isinstance(raw, list):
        raise ValueError("Catalogue root must be a JSON array")

    records: list[DiseaseRecord] = []
    seen: set[str] = set()

    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Record {index} must be a JSON object")

        name_value = item.get("name")
        if not isinstance(name_value, str) or not name_value.strip():
            raise ValueError(f"Record {index} requires a non-empty string 'name'")

        name = name_value.strip()
        if len(name) > 200:
            raise ValueError(f"Record {index} name exceeds 200 characters")

        normalized_key = name.casefold()
        if normalized_key in seen:
            raise ValueError(f"Duplicate disease name: {name}")
        seen.add(normalized_key)

        display_name = item.get("display_name") or name.replace("-", " ").title()
        crop = item.get("crop") or "Wheat"
        causes = item.get("causes") or ""
        severity = item.get("severity") or "medium"

        records.append(
            DiseaseRecord(
                name=name,
                display_name=display_name,
                crop=crop,
                description=_optional_text(item.get("description"), "description") or "",
                symptoms=_string_list(item.get("symptoms"), "symptoms"),
                causes=causes,
                severity=severity,
            )
        )

    return records


async def _seed(
    repository: SqlDiseaseRepository,
    records: list[DiseaseRecord],
) -> None:
    for record in records:
        await repository.upsert(record)
        print(f"Upserted: {record.display_name} ({record.name})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Import an authoritative disease catalogue into PostgreSQL."
    )
    parser.add_argument(
        "catalogue",
        type=Path,
        help="Path to the authoritative disease catalogue JSON file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print records without connecting to the database.",
    )
    args = parser.parse_args(argv)

    try:
        records = load_records(args.catalogue)
    except ValueError as exc:
        print(f"Invalid catalogue: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(f"Validated {len(records)} catalogue record(s); no writes performed.")
        for record in records:
            print(f"- {record.display_name} ({record.name}) [crop={record.crop}, severity={record.severity}]")
        return 0

    settings = get_settings()
    engine = create_db_engine(settings)
    try:
        session_factory = create_session_factory(engine)
        repository = SqlDiseaseRepository(session_factory)
        asyncio.run(_seed(repository, records))
    finally:
        engine.dispose()

    print(f"Successfully imported {len(records)} catalogue record(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
