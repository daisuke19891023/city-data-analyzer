"""Experiment planning logic using dataset metadata."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

from clean_interfaces.models.dspy import QueryMetric, QueryOrder, QuerySpecModel
from clean_interfaces.models.experiments import PlannedJob


class PlanExperiments:
    """Generate experiment jobs from a goal and dataset metadata."""

    def plan(
        self, goal_description: str, datasets_meta: Iterable[dict],
    ) -> list[PlannedJob]:
        """Create planned jobs for each dataset based on the goal."""
        jobs: list[PlannedJob] = []
        for meta in datasets_meta:
            dataset_id = int(meta["id"])
            columns = meta.get("columns", [])
            index_columns = [col["name"] for col in columns if col.get("is_index")]
            numeric_columns = [
                col["name"] for col in columns if col.get("data_type") == "number"
            ]
            group_by = index_columns[:1]
            metrics = [QueryMetric(agg="count", column=None)]
            if numeric_columns:
                metrics.append(QueryMetric(agg="avg", column=numeric_columns[0]))
            query_spec = QuerySpecModel(
                filters=[],
                group_by=group_by,
                metrics=metrics,
                order_by=[QueryOrder(column=group_by[0], direction="asc")]
                if group_by
                else [],
                limit=50,
            )
            jobs.append(
                PlannedJob(
                    dataset_id=dataset_id,
                    job_type="metric_summary",
                    description=(
                        f"{goal_description} に基づき "
                        f"{meta.get('name')} を集計するジョブ"
                    ),
                    query_spec=query_spec,
                ),
            )
            if numeric_columns:
                query_spec_detail = QuerySpecModel(
                    filters=[],
                    group_by=group_by,
                    metrics=[QueryMetric(agg="max", column=numeric_columns[0])],
                    order_by=[QueryOrder(column=numeric_columns[0], direction="desc")],
                    limit=10,
                )
                jobs.append(
                    PlannedJob(
                        dataset_id=dataset_id,
                        job_type="top_values",
                        description=(
                            f"{meta.get('name')} の主要指標 {numeric_columns[0]} を確認"
                        ),
                        query_spec=query_spec_detail,
                    ),
                )
        return jobs
