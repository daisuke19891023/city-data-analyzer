from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from clean_interfaces.database import configure_engine, get_session
from clean_interfaces.db_models import OptimizationJob
from clean_interfaces.services.datasets import init_database
from clean_interfaces.worker import OptimizationWorker

if TYPE_CHECKING:
    from pathlib import Path


def _setup_database() -> None:
    os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:?cache=shared"
    configure_engine(os.environ["DATABASE_URL"])
    session = get_session()
    init_database(session)


def _create_trainset(tmp_path: Path) -> Path:
    data: list[dict[str, object]] = [
        {
            "question": "人口は?",
            "query_spec": {"filters": [], "group_by": [], "metrics": []},
        },
    ]
    path = tmp_path / "trainset.json"
    path.write_text(json.dumps(data))
    return path


def test_optimization_worker_processes_job(tmp_path: Path) -> None:
    """Optimization jobs are compiled and recorded in the database."""
    _setup_database()
    trainset_path = _create_trainset(tmp_path)
    session = get_session()
    job = OptimizationJob(
        trainset_path=str(trainset_path),
        version="worker-v1",
        status="pending",
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )
    session.add(job)
    session.commit()

    worker = OptimizationWorker(artifact_root=tmp_path)
    processed = worker.run_once()

    assert processed is True
    session.close()
    refreshed = get_session().get(OptimizationJob, job.id)
    assert refreshed is not None
    assert refreshed.status == "completed"
    assert refreshed.metric is not None
    assert refreshed.artifact_id is not None
    artifact_path = tmp_path / "worker-v1.json"
    assert artifact_path.exists()
