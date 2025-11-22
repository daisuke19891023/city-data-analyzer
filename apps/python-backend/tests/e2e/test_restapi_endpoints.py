"""FastAPI API tests covering key endpoints with in-memory SQLite."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from clean_interfaces.database import configure_engine, get_session
from clean_interfaces.db_models import Experiment, ExperimentJob, InsightCandidate
from clean_interfaces.interfaces.restapi import RestAPIInterface
from clean_interfaces.models.dspy import QueryMetric, QueryOrder, QuerySpecModel
from clean_interfaces.models.experiments import PlannedJob
from clean_interfaces.services.datasets import DatasetRepository, init_database
from clean_interfaces.services.dspy_program import (
    InteractiveAnalysisProgram,
    InteractiveResponse,
)
from clean_interfaces.services.plan_experiments import PlanExperiments


@pytest.fixture(autouse=True)
def configure_in_memory_db(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configure shared in-memory SQLite for API tests."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:?cache=shared")
    configure_engine(os.environ["DATABASE_URL"])
    session = get_session()
    init_database(session)
    session.close()


@pytest.fixture
def seed_dataset() -> int:
    """Seed a minimal dataset and return its id."""
    session = get_session()
    repo = DatasetRepository(session)
    dataset = repo.ensure_dataset(
        category_slug="population",
        dataset_slug="population_seed",
        dataset_name="人口シード",
        description="テスト用データセット",
        year=2024,
    )
    repo.upsert_columns(
        dataset,
        [
            {"name": "ward", "data_type": "text", "is_index": True},
            {"name": "population", "data_type": "number", "is_index": False},
        ],
    )
    repo.add_record(
        dataset,
        {"ward": "A", "population": 1000},
        {"ward": "A"},
    )
    repo.add_record(
        dataset,
        {"ward": "B", "population": 500},
        {"ward": "B"},
    )
    session.close()
    return dataset.id


@pytest.fixture
def api_client() -> TestClient:
    """Return TestClient bound to RestAPI interface."""
    interface = RestAPIInterface()
    return TestClient(interface.app)


@pytest.fixture(autouse=True)
def stub_planner(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub PlanExperiments to return deterministic jobs."""

    def _plan(
        _self: PlanExperiments,
        _goal_description: str,
        datasets_meta: list[dict[str, object]],
    ) -> list[PlannedJob]:
        return [
            PlannedJob(
                dataset_id=int(meta["id"]),
                job_type="metric_summary",
                description=f"plan for {meta.get('name')}",
                query_spec=QuerySpecModel(
                    filters=[],
                    group_by=["ward"],
                    metrics=[QueryMetric(agg="count", column=None)],
                    order_by=[QueryOrder(column="ward", direction="asc")],
                    limit=10,
                ),
            )
            for meta in datasets_meta
        ]

    monkeypatch.setattr(PlanExperiments, "plan", _plan)


@pytest.fixture
def experiment_with_insight(seed_dataset: int) -> InsightCandidate:
    """Create an experiment/job/insight tuple for downstream tests."""
    session = get_session()
    experiment = Experiment(
        goal_description="テスト実験",
        dataset_ids=[seed_dataset],
        status="pending",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(experiment)
    session.flush()

    job = ExperimentJob(
        experiment_id=experiment.id,
        dataset_id=seed_dataset,
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
        dataset_id=seed_dataset,
        title="候補",
        description="説明",
        metrics=None,
        adopted=False,
        created_at=datetime.now(UTC),
    )
    session.add(candidate)
    session.commit()
    session.close()
    return candidate


def test_list_datasets_returns_seeded_metadata(
    api_client: TestClient, seed_dataset: int,
) -> None:
    """Ensure seeded dataset metadata is returned by /datasets."""
    response = api_client.get("/datasets")
    assert response.status_code == 200
    datasets = response.json()
    assert any(item["id"] == seed_dataset for item in datasets)


def test_interactive_analysis_returns_response(
    api_client: TestClient, seed_dataset: int, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return interactive analysis response with stubbed program."""
    stubbed_response = InteractiveResponse(
        dataset_id=seed_dataset,
        question="人口を教えて",
        query_spec=QuerySpecModel(
            filters=[],
            group_by=[],
            metrics=[QueryMetric(agg="count", column=None)],
            order_by=[],
            limit=5,
        ),
        data=[],
        stats={"returned_rows": 0},
        insight="",
        summary="",
        analysis_id=1,
        program_version="stubbed",
    )

    def _run(
        _self: InteractiveAnalysisProgram, _payload: dict[str, object],
    ) -> InteractiveResponse:  # type: ignore[override]
        return stubbed_response

    monkeypatch.setattr(InteractiveAnalysisProgram, "run", _run)

    response = api_client.post(
        "/dspy/interactive",
        json={"dataset_id": seed_dataset, "question": "人口を教えて"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == seed_dataset
    assert data["analysis_id"] == 1
    assert data["query_spec"]["metrics"][0]["agg"] == "count"


def test_interactive_requires_payload(api_client: TestClient) -> None:
    """Reject interactive analysis without required payload."""
    response = api_client.post("/dspy/interactive", json={})
    assert response.status_code == 400


def test_create_and_list_experiments(api_client: TestClient, seed_dataset: int) -> None:
    """Create experiment then verify it appears in listing and detail."""
    create_resp = api_client.post(
        "/experiments",
        json={"goal_description": "人口分析", "dataset_ids": [seed_dataset]},
    )
    assert create_resp.status_code == 201
    experiment_id = create_resp.json()["experiment_id"]

    list_resp = api_client.get("/experiments")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert any(item["id"] == experiment_id for item in items)

    detail_resp = api_client.get(f"/experiments/{experiment_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == experiment_id


def test_experiment_detail_not_found(api_client: TestClient) -> None:
    """Return 404 when experiment does not exist."""
    response = api_client.get("/experiments/9999")
    assert response.status_code == 404


def test_insights_listing(
    api_client: TestClient, experiment_with_insight: InsightCandidate,
) -> None:
    """List insights for experiment including seeded candidate."""
    response = api_client.get(
        f"/experiments/{experiment_with_insight.experiment_id}/insights",
    )
    assert response.status_code == 200
    insights = response.json()["insights"]
    assert any(item["id"] == experiment_with_insight.id for item in insights)


def test_feedback_happy_path(
    api_client: TestClient, experiment_with_insight: InsightCandidate,
) -> None:
    """Post feedback for existing insight and receive confirmation."""
    response = api_client.post(
        "/feedback",
        json={
            "insight_id": experiment_with_insight.id,
            "rating": 1,
            "comment": "採用",
            "target_module": "batch",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["insight_id"] == experiment_with_insight.id


def test_feedback_requires_target(api_client: TestClient) -> None:
    """Validate feedback requires target module."""
    response = api_client.post(
        "/feedback",
        json={"rating": 1, "target_module": "interactive"},
    )
    assert response.status_code == 400


def test_feedback_missing_candidate_returns_404(api_client: TestClient) -> None:
    """Return 404 when posting feedback for missing insight."""
    response = api_client.post(
        "/feedback",
        json={
            "insight_id": 9999,
            "rating": -1,
            "comment": "なし",
            "target_module": "batch",
        },
    )
    assert response.status_code == 404
