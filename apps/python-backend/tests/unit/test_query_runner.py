from __future__ import annotations

from typing import TYPE_CHECKING

from clean_interfaces.database import configure_engine, session_scope
from clean_interfaces.services.datasets import DatasetRepository, init_database
from clean_interfaces.services.query_runner import QueryRunner

if TYPE_CHECKING:  # pragma: no cover - imports for type checking only
    from pathlib import Path


def test_group_and_metric_execution(tmp_path: Path) -> None:
    """Ensure query runner executes filters, grouping, and metrics."""
    configure_engine("sqlite+pysqlite:///:memory:")
    csv_path = tmp_path / "population.csv"
    csv_path.write_text(
        "year,ward,population\n2023,A,100\n2023,B,150\n2022,A,120\n",
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
        runner = QueryRunner(session)
        query_spec = {
            "filters": [{"column": "year", "op": "eq", "value": 2023}],
            "group_by": ["ward"],
            "metrics": [{"agg": "sum", "column": "population"}],
            "order_by": [{"column": "population", "direction": "desc"}],
            "limit": 10,
        }
        result = runner.run(dataset.id, query_spec)

    assert result["summary"]["returned_rows"] == 2
    assert result["data"][0]["population_sum"] == 150
    assert {row["ward"] for row in result["data"]} == {"A", "B"}
