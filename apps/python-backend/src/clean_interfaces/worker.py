"""Simple worker processing experiment jobs."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from structlog import get_logger
from sqlalchemy import select

from clean_interfaces.database import get_engine, session_scope
from clean_interfaces.db_models import (
    Experiment,
    ExperimentJob,
    InsightCandidate,
    OptimizationJob,
)
from clean_interfaces.services.optimization import (
    INTERACTIVE_ARTIFACT_ROOT,
    OptimizationService,
)
from clean_interfaces.services.datasets import init_database
from clean_interfaces.services.query_runner import QueryRunner

POLL_INTERVAL_SECONDS = 3

logger = get_logger()

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from clean_interfaces.models.dspy import QuerySpecDict


class ExperimentWorker:
    """Process pending experiment jobs sequentially."""

    def __init__(self) -> None:
        """Initialize the worker and ensure the database is ready."""
        get_engine()
        with session_scope() as session:
            init_database(session)

    def run_forever(self) -> None:
        """Continuously process jobs with a polling interval."""
        while True:
            processed = self.run_once()
            if not processed:
                time.sleep(POLL_INTERVAL_SECONDS)

    def run_once(self) -> bool:
        """Process a single pending job if available."""
        with session_scope() as session:
            job = session.scalars(
                select(ExperimentJob).where(ExperimentJob.status == "pending").limit(1),
            ).first()
            if job is None:
                return False
            job.status = "running"
            now = datetime.now(tz=UTC)
            job.started_at = now
            job.updated_at = now
            session.commit()

            runner = QueryRunner(session)
            try:
                query_spec = cast("QuerySpecDict", job.query_spec or {})
                result = runner.run(job.dataset_id, query_spec)
                summary = result.get("summary", {})
                description = self._build_description(job, summary)
                candidate = InsightCandidate(
                    experiment_id=job.experiment_id,
                    job_id=job.id,
                    dataset_id=job.dataset_id,
                    title=f"{job.job_type} @ dataset {job.dataset_id}",
                    description=description,
                    metrics=summary,
                )
                session.add(candidate)
                job.status = "completed"
                finished = datetime.now(tz=UTC)
                job.completed_at = finished
                job.updated_at = finished
                session.commit()
                self._update_experiment_status(session, job.experiment_id)
            except Exception as exc:
                job.status = "failed"
                job.error_message = str(exc)
                job.updated_at = datetime.now(tz=UTC)
                session.commit()
            return True

    def _build_description(self, job: ExperimentJob, summary: dict[str, Any]) -> str:
        metrics: list[dict[str, Any]] | None = summary.get("metrics")
        if metrics:
            metric_text = ", ".join(
                f"{m.get('agg')}({m.get('column') or 'rows'})" for m in metrics
            )
        else:
            metric_text = "集計結果なし"
        returned = summary.get("returned_rows")
        return (
            f"ジョブ {job.job_type} で {metric_text} を計算しました。"
            f"返却件数: {returned}"
        )

    def _update_experiment_status(self, session: Session, experiment_id: int) -> None:
        experiment = session.get(Experiment, experiment_id)
        if experiment is None:
            return
        all_jobs = experiment.jobs
        if all(job.status in {"completed", "failed"} for job in all_jobs):
            experiment.status = "completed"
            experiment.updated_at = datetime.now(tz=UTC)
            session.commit()


class OptimizationWorker:
    """Compile interactive programs from queued optimization jobs."""

    def __init__(self, artifact_root: Path | None = None) -> None:
        """Initialize optimization worker and ensure database is ready."""
        get_engine()
        with session_scope() as session:
            init_database(session)
        self.artifact_root = artifact_root or INTERACTIVE_ARTIFACT_ROOT

    def run_once(self) -> bool:
        """Process a single optimization job if available."""
        with session_scope() as session:
            job = session.scalars(
                select(OptimizationJob)
                .where(OptimizationJob.status == "pending")
                .limit(1),
            ).first()
            if job is None:
                return False

            job.status = "running"
            now = datetime.now(tz=UTC)
            job.started_at = now
            job.updated_at = now
            session.commit()

            service = OptimizationService(
                session=session,
                artifact_root=self.artifact_root,
            )
            try:
                trainset_path = Path(job.trainset_path)
                result = service.compile_interactive(
                    trainset_path,
                    version=job.version,
                )
                job.metric = {
                    "baseline": result.baseline_score,
                    "compiled": result.compiled_score,
                }
                job.artifact_id = result.artifact.id
                job.status = "completed"
                finished = datetime.now(tz=UTC)
                job.completed_at = finished
                job.updated_at = finished
                session.commit()
                logger.info(
                    "Optimization job completed",
                    job_id=job.id,
                    version=result.version,
                    artifact_id=result.artifact.id,
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception(
                    "Optimization job failed",
                    job_id=job.id,
                    error=str(exc),
                )
                job.status = "failed"
                job.error_message = str(exc)
                job.updated_at = datetime.now(tz=UTC)
                session.commit()
            return True


class WorkerOrchestrator:
    """Orchestrate experiment and optimization workers."""

    def __init__(self) -> None:
        """Initialize workers for experiment and optimization queues."""
        self.optimization_worker = OptimizationWorker()
        self.experiment_worker = ExperimentWorker()

    def run_forever(self) -> None:
        """Poll both queues until interrupted."""
        while True:
            processed = False
            processed |= self.optimization_worker.run_once()
            processed |= self.experiment_worker.run_once()
            if not processed:
                time.sleep(POLL_INTERVAL_SECONDS)


def main() -> None:
    """Run the worker in continuous mode."""
    orchestrator = WorkerOrchestrator()
    orchestrator.run_forever()


if __name__ == "__main__":
    main()
