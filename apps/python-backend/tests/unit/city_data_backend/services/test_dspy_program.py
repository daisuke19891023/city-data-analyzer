from __future__ import annotations

import os
from pathlib import Path

from city_data_backend.database import configure_engine, get_session
from city_data_backend.db_models import AnalysisQuery
from city_data_backend.models.dspy import (
    InteractiveRequest,
    QueryMetric,
    QueryOrder,
    QuerySpecModel,
)
from city_data_backend.services.datasets import DatasetRepository, init_database
from city_data_backend.services.dspy_program import (
    CompiledInteractiveProgram,
    InteractiveAnalysisProgram,
    load_compiled_program,
    persist_compiled_program,
    set_active_program,
)
from city_data_backend.services.query_runner import QueryRunner


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


def test_persist_compiled_program_writes_file_and_record(tmp_path: Path) -> None:
    """Persisting a compiled program stores metadata and file."""
    os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:?cache=shared"
    configure_engine(os.environ["DATABASE_URL"])
    session = get_session()
    init_database(session)

    artifact = persist_compiled_program(
        version="v1",
        trainset=[{"question": "Q", "query_spec": {"filters": []}}],
        metric={"score": 0.8},
        session=session,
        base_dir=tmp_path,
    )

    assert artifact.id is not None
    assert Path(artifact.path).exists()
    assert Path(artifact.path).parent == tmp_path
    assert artifact.active is False


def test_load_compiled_program_prefers_active_version(tmp_path: Path) -> None:
    """Load the active compiled program when available."""
    os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:?cache=shared"
    configure_engine(os.environ["DATABASE_URL"])
    session = get_session()
    init_database(session)

    first = persist_compiled_program(
        version="v1",
        trainset=[{"question": "Q1", "query_spec": {"filters": []}}],
        metric=None,
        session=session,
        base_dir=tmp_path,
    )
    second = persist_compiled_program(
        version="v2",
        trainset=[{"question": "Q2", "query_spec": {"filters": []}}],
        metric=None,
        session=session,
        base_dir=tmp_path,
    )

    set_active_program(second.id, active=True, session=session)

    program = load_compiled_program(session=session)

    assert program is not None
    assert program.version == "v2"
    assert program.trainset[0]["question"] == "Q2"

    set_active_program(first.id, active=True, session=session)
    program_latest = load_compiled_program(session=session)
    assert program_latest is not None
    assert program_latest.version == "v1"
