"""Lightweight DSPy-inspired interactive analysis pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from clean_interfaces.models.dspy import (
    InteractiveRequest,
    InteractiveResponse,
    QuerySpecDict,
    QuerySpecModel,
)
from clean_interfaces.services.query_runner import QueryRunner
from clean_interfaces.services.query_spec import RuleBasedQueryGenerator

if TYPE_CHECKING:  # pragma: no cover - type checking imports
    from clean_interfaces.services.datasets import DatasetRepository


class InteractiveAnalysisProgram:
    """Chain NL question -> QuerySpec -> query execution -> summarization."""

    def __init__(
        self, repo: DatasetRepository, runner: QueryRunner | None = None,
    ) -> None:
        """Initialize the program with a repository and optional runner."""
        self.repo = repo
        self.generator = RuleBasedQueryGenerator()
        self.runner = runner or QueryRunner(repo.session)

    def run(self, request: InteractiveRequest) -> InteractiveResponse:
        """Execute NL question to query to result pipeline."""
        dataset_meta = self.repo.get_dataset_metadata(request.dataset_id)
        query_spec = self.generator.generate(request.question, dataset_meta)
        query_spec_dict: QuerySpecDict = query_spec.model_dump()
        result = self.runner.run(request.dataset_id, query_spec_dict)
        insight = self._summarize(request.question, result)
        self.repo.record_analysis(
            dataset_id=request.dataset_id,
            question=request.question,
            query_spec=dict(query_spec_dict),
            result_summary=result["summary"],
            provider=request.provider,
            model=request.model,
        )
        query_spec_payload: dict[str, Any] = dict(query_spec_dict)

        return InteractiveResponse(
            dataset_id=request.dataset_id,
            question=request.question,
            query_spec=QuerySpecModel(**query_spec_payload),
            data=result["data"],
            stats=result["summary"],
            insight=insight,
        )

    def _summarize(self, question: str, result: dict[str, Any]) -> str:
        summary = result.get("summary", {})
        metrics = summary.get("metrics", [])
        if metrics:
            metric_descriptions = [
                f"{metric.get('agg')}({metric.get('column') or 'rows'})"
                for metric in metrics
            ]
            joined_metrics = ", ".join(metric_descriptions)
            returned_rows = summary.get("returned_rows")
            return (
                f"質問『{question}』に対し、{joined_metrics} を計算しました。"
                f"返却件数: {returned_rows}件。"
            )
        returned_rows = summary.get("returned_rows", 0)
        return f"質問『{question}』に対し {returned_rows} 件のレコードを返却しました。"
