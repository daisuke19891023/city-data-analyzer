from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import pytest
from fastapi.testclient import TestClient

from city_data_backend.database import configure_engine, session_scope
from city_data_backend.interfaces.restapi import RestAPIInterface
from city_data_backend.models.dspy import OptimizationArtifactRequest
from city_data_backend.services import dspy_program
from city_data_backend.services.datasets import init_database

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Configure in-memory DB and return a FastAPI test client."""
    token = "test-token"  # noqa: S105
    monkeypatch.setenv("API_TOKEN", token)
    configure_engine("sqlite+pysqlite:///:memory:")
    with session_scope() as session:
        init_database(session)
    dspy_program.DEFAULT_ARTIFACT_ROOT = tmp_path
    interface = RestAPIInterface()
    return TestClient(interface.app, headers={"Authorization": f"Bearer {token}"})


def test_optimization_lifecycle(client: TestClient) -> None:
    """End-to-end lifecycle for optimization endpoints."""
    trainset_v1: list[dict[str, Any]] = [
        {"question": "Q1", "query_spec": {"filters": []}},
    ]
    payload = OptimizationArtifactRequest(
        version="v1",
        trainset=trainset_v1,
        metric={"score": 0.9},
    )
    create_resp = client.post("/dspy/optimization", json=payload.model_dump())
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["version"] == "v1"
    assert created["active"] is False

    history = client.get("/dspy/optimization/history")
    assert history.status_code == 200
    assert len(history.json()) == 1

    trainset_v2: list[dict[str, Any]] = [
        {"question": "Q2", "query_spec": {"filters": []}},
    ]
    payload_v2 = OptimizationArtifactRequest(
        version="v2",
        trainset=trainset_v2,
        metric=None,
    )
    create_resp_v2 = client.post("/dspy/optimization", json=payload_v2.model_dump())
    assert create_resp_v2.status_code == 201
    created_v2 = create_resp_v2.json()

    client_with_patch = cast("Any", client)
    activate = client_with_patch.patch(
        f"/dspy/optimization/{created_v2['id']}",
        json={"active": True},
    )
    assert activate.status_code == 200
    assert activate.json()["active"] is True

    latest = client.get("/dspy/optimization")
    assert latest.status_code == 200
    assert latest.json()["id"] == created_v2["id"]


def test_optimization_validation_and_toggle_errors(client: TestClient) -> None:
    """Ensure validation and activation errors return appropriate responses."""
    invalid_payload: dict[str, object] = {
        "version": "v-invalid",
        "trainset": "bad",
        "metric": {},
    }
    invalid_resp = client.post("/dspy/optimization", json=invalid_payload)
    assert invalid_resp.status_code == 400

    traversal_payload: dict[str, object] = {
        "version": "../escape",  # path traversal attempt
        "trainset": [{"question": "Q", "query_spec": {"filters": []}}],
        "metric": None,
    }
    traversal_resp = client.post("/dspy/optimization", json=traversal_payload)
    assert traversal_resp.status_code == 400
    assert traversal_resp.json()["detail"]

    # Ensure nothing was written for the traversal attempt
    assert not list(dspy_program.DEFAULT_ARTIFACT_ROOT.glob("**/*.json"))

    client_with_patch = cast("Any", client)
    toggle_resp = client_with_patch.patch(
        "/dspy/optimization/999",
        json={"active": True},
    )
    assert toggle_resp.status_code == 404
