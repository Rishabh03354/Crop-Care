"""Integration tests for the disease endpoint using SQL persistence."""
from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.domain.disease import DiseaseRecord
from app.repositories.disease_repository import SqlDiseaseRepository


@pytest.fixture
def disease_session_factory(app):
    return app.state.session_factory


def test_known_disease_is_read_from_database(
    client: TestClient,
    disease_session_factory,
) -> None:
    name = "database-api-test-only"

    repository = SqlDiseaseRepository(disease_session_factory)
    asyncio.run(
        repository.upsert(
            DiseaseRecord(
                name=name,
                display_name="Database API Test",
                crop="Wheat",
                description="Testing endpoint persistence",
                symptoms=("Spotted leaves", "Chlorosis"),
                causes="Test pathogen",
                severity="medium",
            )
        )
    )

    response = client.get(f"/api/v1/diseases/{name}")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == name
    assert body["display_name"] == "Database API Test"
    assert body["crop"] == "Wheat"
    assert body["symptoms"] == ["Spotted leaves", "Chlorosis"]
    assert body["causes"] == "Test pathogen"
    assert body["severity"] == "medium"


def test_unknown_disease_returns_existing_error_contract(client: TestClient) -> None:
    response = client.get("/api/v1/diseases/definitely-not-in-catalogue")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "DISEASE_NOT_FOUND"
    assert set(body["error"]) >= {"code", "message", "details"}


def test_slug_and_case_insensitive_disease_lookup(
    client: TestClient,
    disease_session_factory,
) -> None:
    repository = SqlDiseaseRepository(disease_session_factory)
    asyncio.run(
        repository.upsert(
            DiseaseRecord(
                name="yellow-rust",
                display_name="Yellow Rust",
                crop="Wheat",
                description="Stripe rust caused by Puccinia striiformis",
                symptoms=("Yellow stripes",),
                causes="Puccinia striiformis",
                severity="high",
            )
        )
    )

    # Lookup by exact slug
    resp1 = client.get("/api/v1/diseases/yellow-rust")
    assert resp1.status_code == 200
    assert resp1.json()["display_name"] == "Yellow Rust"

    # Lookup by name with space or case
    resp2 = client.get("/api/v1/diseases/Yellow%20Rust")
    assert resp2.status_code == 200
    assert resp2.json()["name"] == "yellow-rust"
