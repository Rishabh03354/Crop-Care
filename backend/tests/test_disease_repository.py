"""Database tests for the SQL disease catalogue repository."""
from __future__ import annotations

from dataclasses import replace

import pytest

from app.core.exceptions import PersistenceError
from app.domain.disease import DiseaseRecord
from app.repositories.disease_repository import SqlDiseaseRepository


@pytest.fixture
def disease_session_factory(app):
    return app.state.session_factory


async def test_sql_disease_repository_round_trip(
    disease_session_factory,
) -> None:
    repository = SqlDiseaseRepository(disease_session_factory)
    record = DiseaseRecord(
        name="round-trip-test",
        display_name="Round Trip Test",
        crop="Wheat",
        description="Testing direct SQL round trip",
        symptoms=("Symptom 1", "Symptom 2"),
        causes="Testing causes",
        severity="medium",
    )

    saved = await repository.upsert(record)
    assert saved.name == record.name
    assert saved.display_name == record.display_name

    fetched = await repository.get_by_name(record.name)
    assert fetched is not None
    assert fetched.name == record.name
    assert fetched.display_name == record.display_name
    assert fetched.symptoms == record.symptoms

    assert await repository.get_by_name("not-in-catalogue-xyz") is None

    records = await repository.list_all()
    assert any(item.name == record.name for item in records)


async def test_sql_disease_upsert_is_idempotent(
    disease_session_factory,
) -> None:
    repository = SqlDiseaseRepository(disease_session_factory)
    record = DiseaseRecord(
        name="upsert-test",
        display_name="Upsert Test",
        crop="Wheat",
        description="Initial description",
        symptoms=("Symptom A",),
        causes="Initial causes",
        severity="low",
    )

    await repository.upsert(record)
    updated_record = replace(record, description="Updated description for test", severity="high")
    await repository.upsert(updated_record)

    records = await repository.list_all()
    matching = [item for item in records if item.name == record.name]
    assert len(matching) == 1
    assert matching[0].description == "Updated description for test"
    assert matching[0].severity == "high"


async def test_sql_disease_upsert_rolls_back_on_database_failure(
    app,
    disease_session_factory,
) -> None:
    if app.state.engine.dialect.name != "sqlite":
        pytest.skip("This forced-failure test uses a SQLite trigger.")

    name = "rollback-test-only"

    with app.state.engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TRIGGER disease_insert_failure
            BEFORE INSERT ON diseases
            WHEN NEW.name = 'rollback-test-only'
            BEGIN
                SELECT RAISE(ABORT, 'forced database failure');
            END;
            """
        )

    repository = SqlDiseaseRepository(disease_session_factory)

    with pytest.raises(PersistenceError):
        await repository.upsert(
            DiseaseRecord(
                name=name,
                display_name="Rollback Test",
                crop="Wheat",
                description="Failure test",
                symptoms=(),
                causes="",
                severity="medium",
            )
        )

    assert await repository.get_by_name(name) is None
