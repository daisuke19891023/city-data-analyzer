from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from clean_interfaces.database import configure_engine, session_scope
from clean_interfaces.interfaces.restapi import RestAPIInterface
from clean_interfaces.services.datasets import DatasetRepository, init_database

if TYPE_CHECKING:  # pragma: no cover - imports for type checking only
    from pathlib import Path


def test_interactive_endpoint_returns_stats(tmp_path: Path) -> None:
    """Ensure interactive endpoint returns stats and insights."""
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
    client = TestClient(interface.app)

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
