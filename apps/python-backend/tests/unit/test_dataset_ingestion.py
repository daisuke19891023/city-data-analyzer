from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import text

from clean_interfaces.database import configure_engine, session_scope
from clean_interfaces.services.datasets import DatasetRepository, init_database

if TYPE_CHECKING:  # pragma: no cover - imports for type checking only
    from pathlib import Path


def test_import_csv_and_metadata(tmp_path: Path) -> None:
    """Verify CSV import stores metadata, records, and index columns."""
    configure_engine("sqlite+pysqlite:///:memory:")
    csv_path = tmp_path / "population.csv"
    csv_path.write_text(
        "year,ward,population\n2023,A,100\n2023,B,150\n",
        encoding="utf-8",
    )

    with session_scope() as session:
        init_database(session)
        repo = DatasetRepository(session)
        dataset = repo.import_csv(
            category_slug="population",
            dataset_slug="population_by_ward_2023",
            csv_path=csv_path,
            dataset_name="人口(区別)2023",
            description="テスト人口データ",
            year=2023,
        )
        metadata = repo.get_dataset_metadata(dataset.id)
        records = repo.get_records(dataset.id)

    assert metadata["slug"] == "population_by_ward_2023"
    assert len(metadata["columns"]) == 3
    assert len(records) == 2
    with session_scope() as session:
        session.execute(text("PRAGMA case_sensitive_like=ON"))
        index_values = session.execute(
            text(
                "SELECT index_cols FROM dataset_records WHERE dataset_id = :dataset_id",
            ),
            {"dataset_id": dataset.id},
        ).all()
    assert any("year" in row[0] for row in index_values), "year should be indexed"
