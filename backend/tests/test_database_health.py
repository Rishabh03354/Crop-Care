"""Database readiness failure tests."""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError


class _UnavailableEngine:
    def connect(self):
        raise OperationalError(
            "SELECT 1",
            {},
            RuntimeError("simulated database outage"),
        )

    def dispose(self) -> None:
        pass


def test_health_db_returns_503_when_database_is_unavailable(
    app,
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(app.state, "engine", _UnavailableEngine())

    class _FailingSession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def execute(self, *args, **kwargs):
            raise OperationalError(
                "SELECT 1",
                {},
                RuntimeError("simulated database outage"),
            )

        def rollback(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(app.state, "session_factory", lambda: _FailingSession())

    response = client.get("/api/v1/health/db")

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert set(body["error"]) >= {"code", "message", "details"}
