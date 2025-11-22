"""Simple worker processing experiment jobs."""

from __future__ import annotations

import time
from datetime import UTC, datetime

from sqlalchemy import select

from clean_interfaces.database import get_engine, session_scope
from clean_interfaces.db_models import Experiment, ExperimentJob, InsightCandidate
from clean_interfaces.services.datasets import init_database
from clean_interfaces.services.query_runner import QueryRunner

POLL_INTERVAL_SECONDS = 3


class ExperimentWorker:
    """Process pending experiment jobs sequentially."""

    def __init__(self) -> None:
        get_engine()
        with session_scope() as session:
            init_database(session)

    def run_forever(self) -> None:
        while True:
            processed = self.run_once()
            if not processed:
                time.sleep(POLL_INTERVAL_SECONDS)

    def run_once(self) -> bool:
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
                result = runner.run(job.dataset_id, job.query_spec)
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
            except Exception as exc:  # noqa: BLE001
                job.status = "failed"
                job.error_message = str(exc)
                job.updated_at = datetime.now(tz=UTC)
                session.commit()
            return True

    def _build_description(self, job: ExperimentJob, summary: dict) -> str:
        metrics = summary.get("metrics")
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

    def _update_experiment_status(self, session, experiment_id: int) -> None:
        experiment = session.get(Experiment, experiment_id)
        if experiment is None:
            return
        all_jobs = experiment.jobs
        if all(job.status in {"completed", "failed"} for job in all_jobs):
            experiment.status = "completed"
            experiment.updated_at = datetime.now(tz=UTC)
            session.commit()


def main() -> None:
    worker = ExperimentWorker()
    worker.run_forever()


if __name__ == "__main__":
    main()
