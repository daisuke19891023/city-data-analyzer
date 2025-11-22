from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from clean_interfaces.database import configure_engine, get_session
from clean_interfaces.db_models import Experiment, ExperimentJob, InsightCandidate
from clean_interfaces.services.datasets import DatasetRepository, init_database
from clean_interfaces.services.plan_experiments import PlanExperiments
from clean_interfaces.worker import ExperimentWorker


def setup_in_memory_session() -> Session:
    """Create an in-memory session for experiment tests."""
    os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:?cache=shared"
    configure_engine(os.environ["DATABASE_URL"])
    session = get_session()
    init_database(session)
    return session


def seed_dataset(session: Session) -> Experiment:
    """Seed minimal dataset data for experiment execution."""
    repo = DatasetRepository(session)
    dataset = repo.ensure_dataset(
        category_slug="population",
        dataset_slug="population_trend",
        dataset_name="人口推移",
        description="テスト用人口データ",
        year=2020,
    )
    repo.upsert_columns(
        dataset,
        [
            {"name": "year", "data_type": "number", "is_index": True},
            {"name": "population", "data_type": "number", "is_index": False},
        ],
    )
    repo.add_record(dataset, {"year": 2020, "population": 100}, {"year": 2020})
    repo.add_record(dataset, {"year": 2021, "population": 120}, {"year": 2021})
    return dataset


def test_plan_experiments_returns_jobs() -> None:
    """PlanExperiments returns at least one job per dataset."""
    session = setup_in_memory_session()
    dataset = seed_dataset(session)
    repo = DatasetRepository(session)
    meta = repo.get_dataset_metadata(dataset.id)
    planner = PlanExperiments()
    jobs = planner.plan("人口の推移を把握したい", [meta])
    assert len(jobs) >= 1
    assert jobs[0].dataset_id == dataset.id
    assert jobs[0].query_spec.metrics


def test_worker_generates_insight_candidate() -> None:
    """Worker processes the pending job and stores an insight candidate."""
    session = setup_in_memory_session()
    dataset = seed_dataset(session)
    experiment = Experiment(
        goal_description="人口の概要を知りたい",
        dataset_ids=[dataset.id],
        status="pending",
    )
    session.add(experiment)
    session.commit()
    session.refresh(experiment)

    job = ExperimentJob(
        experiment_id=experiment.id,
        dataset_id=dataset.id,
        job_type="metric_summary",
        description="人口の平均を確認",
        query_spec={
            "filters": [],
            "group_by": ["year"],
            "metrics": [{"agg": "avg", "column": "population"}],
            "order_by": [],
            "limit": 10,
        },
        status="pending",
    )
    session.add(job)
    session.commit()
    session.close()

    worker = ExperimentWorker()
    processed = worker.run_once()
    assert processed is True

    check_session = get_session()
    candidates = check_session.query(InsightCandidate).all()
    assert candidates
    assert candidates[0].experiment_id == experiment.id
    check_session.close()
