"""Lightweight DSPy-inspired interactive analysis pipeline."""

from __future__ import annotations

from typing import Any

from clean_interfaces.models.dspy import (
    InteractiveRequest,
    InteractiveResponse,
    QuerySpecModel,
)
from clean_interfaces.services.datasets import DatasetRepository
from clean_interfaces.services.query_runner import QueryRunner
from clean_interfaces.services.query_spec import RuleBasedQueryGenerator


class InteractiveAnalysisProgram:
    """Chain NL question -> QuerySpec -> query execution -> summarization."""

    def __init__(self, repo: DatasetRepository, runner: QueryRunner | None = None):
        self.repo = repo
        self.generator = RuleBasedQueryGenerator()
        self.runner = runner or QueryRunner(repo.session)

    def run(self, request: InteractiveRequest) -> InteractiveResponse:
        dataset_meta = self.repo.get_dataset_metadata(request.dataset_id)
        query_spec = self.generator.generate(request.question, dataset_meta)
        result = self.runner.run(request.dataset_id, query_spec.model_dump())
        insight = self._summarize(request.question, result)
        self.repo.record_analysis(
            dataset_id=request.dataset_id,
            question=request.question,
            query_spec=query_spec.model_dump(),
            result_summary=result["summary"],
            provider=request.provider,
            model=request.model,
        )
        return InteractiveResponse(
            dataset_id=request.dataset_id,
            question=request.question,
            query_spec=QuerySpecModel(**query_spec.model_dump()),
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
            return f"質問『{question}』に対し、{', '.join(metric_descriptions)} を計算しました。返却件数: {summary.get('returned_rows')}件。"
        return f"質問『{question}』に対し {summary.get('returned_rows', 0)} 件のレコードを返却しました。"
