from __future__ import annotations

import os

from clean_interfaces.database import configure_engine, get_session
from clean_interfaces.db_models import AnalysisQuery
from clean_interfaces.models.dspy import (
    InteractiveRequest,
    QueryMetric,
    QueryOrder,
    QuerySpecModel,
)
from clean_interfaces.services.datasets import DatasetRepository, init_database
from clean_interfaces.services.dspy_program import (
    CompiledInteractiveProgram,
    InteractiveAnalysisProgram,
)
from clean_interfaces.services.query_runner import QueryRunner


class DummyCompiled(CompiledInteractiveProgram):
    """Predict a static query spec for testing program version recording."""

    def __init__(self) -> None:
        """Seed the parent with a version and empty trainset."""
        super().__init__(version="compiled-test", trainset=[])

    def predict(  # type: ignore[override]
        self,
        _question: str,
        _dataset_meta: dict[str, object],
    ) -> QuerySpecModel:
        """Return a fixed query spec regardless of input."""
        return QuerySpecModel(
            filters=[],
            group_by=["ward"],
            metrics=[QueryMetric(agg="sum", column="population")],
            order_by=[QueryOrder(column="population", direction="desc")],
            limit=5,
        )


def setup_dataset() -> tuple[DatasetRepository, QueryRunner]:
    """Prepare a dataset and runner for interactive program tests."""
    os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:?cache=shared"
    configure_engine(os.environ["DATABASE_URL"])
    session = get_session()
    init_database(session)
    repo = DatasetRepository(session)
    dataset = repo.ensure_dataset(
        category_slug="population",
        dataset_slug="population_compiled",
        dataset_name="人口コンパイル",
        description="",
        year=2024,
    )
    repo.upsert_columns(
        dataset,
        [
            {"name": "ward", "data_type": "text", "is_index": True},
            {"name": "population", "data_type": "number", "is_index": False},
        ],
    )
    repo.add_record(dataset, {"ward": "A", "population": 10}, {"ward": "A"})
    repo.add_record(dataset, {"ward": "B", "population": 5}, {"ward": "B"})
    runner = QueryRunner(session)
    return repo, runner


def test_interactive_program_records_program_version() -> None:
    """Store compiled program_version on responses and persisted analyses."""
    repo, runner = setup_dataset()
    compiled = DummyCompiled()
    program = InteractiveAnalysisProgram(repo, runner=runner, compiled_program=compiled)
    response = program.run(
        InteractiveRequest(
            dataset_id=repo.list_datasets()[0]["id"],
            question="人口の合計をみたい",
            provider="openai",
            model="test",
        ),
    )

    assert response.program_version == "compiled-test"
    assert response.analysis_id is not None

    session = repo.session
    stored = session.query(AnalysisQuery).first()
    assert stored is not None
    assert stored.program_version == "compiled-test"
