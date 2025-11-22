from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from clean_interfaces.database import configure_engine, get_session
from clean_interfaces.db_models import (
    AnalysisQuery,
    Experiment,
    ExperimentJob,
    InsightCandidate,
    InsightFeedback,
)
from clean_interfaces.interfaces.restapi import RestAPIInterface
from clean_interfaces.services.datasets import DatasetRepository, init_database

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def setup_in_memory() -> None:
    """Configure a shared in-memory SQLite database for tests."""
    os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:?cache=shared"
    configure_engine(os.environ["DATABASE_URL"])
    session = get_session()
    init_database(session)


def seed_analysis(session: Session) -> AnalysisQuery:
    """Insert a minimal dataset and analysis record for feedback tests."""
    repo = DatasetRepository(session)
    dataset = repo.ensure_dataset(
        category_slug="population",
        dataset_slug="population_test",
        dataset_name="人口テスト",
        description="",
        year=2024,
    )
    repo.upsert_columns(
        dataset,
        [
            {"name": "year", "data_type": "number", "is_index": True},
            {"name": "population", "data_type": "number", "is_index": False},
        ],
    )
    repo.add_record(dataset, {"year": 2024, "population": 100}, {"year": 2024})
    return repo.record_analysis(
        dataset_id=dataset.id,
        question="テスト質問",
        query_spec={"filters": [], "group_by": [], "metrics": [], "order_by": []},
        result_summary={"returned_rows": 1},
        provider=None,
        model=None,
        program_version="compiled-test",
    )


def seed_candidate(session: Session) -> InsightCandidate:
    """Insert a minimal insight candidate linked to an experiment job."""
    repo = DatasetRepository(session)
    dataset = repo.ensure_dataset(
        category_slug="population",
        dataset_slug="population_candidate",
        dataset_name="人口候補",
        description="",
        year=2023,
    )
    repo.upsert_columns(
        dataset,
        [
            {"name": "ward", "data_type": "text", "is_index": True},
            {"name": "population", "data_type": "number", "is_index": False},
        ],
    )
    repo.add_record(dataset, {"ward": "A", "population": 10}, {"ward": "A"})

    experiment = Experiment(
        goal_description="test",
        dataset_ids=[dataset.id],
        status="pending",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(experiment)
    session.flush()

    job = ExperimentJob(
        experiment_id=experiment.id,
        dataset_id=dataset.id,
        job_type="metric_summary",
        description="",
        query_spec={
            "filters": [],
            "group_by": [],
            "metrics": [],
            "order_by": [],
            "limit": 5,
        },
        status="pending",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(job)
    session.flush()

    candidate = InsightCandidate(
        experiment_id=experiment.id,
        job_id=job.id,
        dataset_id=dataset.id,
        title="候補A",
        description="説明",
        metrics=None,
        adopted=False,
        created_at=datetime.now(UTC),
    )
    session.add(candidate)
    session.commit()
    return candidate


def test_feedback_requires_target() -> None:
    """Return 400 when neither insight_id nor analysis_id is provided."""
    setup_in_memory()
    api = RestAPIInterface()
    client = TestClient(api.app)

    response = client.post(
        "/feedback",
        json={"rating": 1, "target_module": "interactive"},
    )
    assert response.status_code == 400


def test_feedback_for_analysis_is_stored() -> None:
    """Persist interactive feedback and store program version."""
    setup_in_memory()
    session = get_session()
    analysis = seed_analysis(session)
    session.close()

    api = RestAPIInterface()
    client = TestClient(api.app)
    response = client.post(
        "/feedback",
        json={
            "analysis_id": analysis.id,
            "rating": 1,
            "comment": "良い",
            "target_module": "interactive",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["analysis_id"] == analysis.id

    check_session = get_session()
    stored = check_session.query(InsightFeedback).all()
    assert len(stored) == 1
    assert stored[0].rating == 1
    assert stored[0].target_module == "interactive"
    check_session.close()


def test_feedback_for_candidate_marks_adopted() -> None:
    """Persist batch feedback and flip adopted flag when rating is negative."""
    setup_in_memory()
    session = get_session()
    candidate = seed_candidate(session)
    session.close()

    api = RestAPIInterface()
    client = TestClient(api.app)
    response = client.post(
        "/feedback",
        json={
            "insight_id": candidate.id,
            "rating": -1,
            "comment": "もう少し精度を上げたい",
            "target_module": "batch",
        },
    )
    assert response.status_code == 201

    check_session = get_session()
    refreshed = check_session.get(InsightCandidate, candidate.id)
    assert refreshed is not None
    assert refreshed.adopted is False
    check_session.close()
