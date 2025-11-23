from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from city_data_backend.database import configure_engine, session_scope
from city_data_backend.interfaces.restapi import RestAPIInterface
from city_data_backend.services.datasets import DatasetRepository, init_database

if TYPE_CHECKING:  # pragma: no cover - imports for type checking only
    from pathlib import Path

    import pytest


def test_interactive_endpoint_returns_stats(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure interactive endpoint returns stats and insights."""
    token = "test-token"  # noqa: S105
    monkeypatch.setenv("API_TOKEN", token)
    configure_engine("sqlite+pysqlite:///:memory:")
    csv_path = tmp_path / "population.csv"
    csv_path.write_text(
        "year,ward,population\n2023,A,100\n2023,B,120\n",
        encoding="utf-8",
    )

    with session_scope() as session:
        init_database(session)
        repo = DatasetRepository(session)
        dataset = repo.import_csv(
            category_slug="population",
            dataset_slug="population_by_ward",
            csv_path=csv_path,
            dataset_name="人口",
            description="テスト人口データ",
            year=2023,
        )

    interface = RestAPIInterface()
    client = TestClient(interface.app, headers={"Authorization": f"Bearer {token}"})

    response = client.post(
        "/dspy/interactive",
        json={
            "dataset_id": dataset.id,
            "question": "2023年の区別人口の平均は?",
            "provider": "test",
            "model": "test",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["dataset_id"] == dataset.id
    assert body["query_spec"]["filters"]
    assert body["stats"]["returned_rows"] >= 1
    assert "insight" in body
