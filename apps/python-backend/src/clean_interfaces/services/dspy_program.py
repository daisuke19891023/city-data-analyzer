"""Lightweight DSPy-inspired interactive analysis pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from structlog import get_logger

from clean_interfaces.models.dspy import (
    InteractiveRequest,
    InteractiveResponse,
    QuerySpecDict,
    QuerySpecModel,
)
from clean_interfaces.services.query_runner import QueryRunner
from clean_interfaces.services.query_spec import RuleBasedQueryGenerator

if TYPE_CHECKING:  # pragma: no cover - type checking imports
    from clean_interfaces.services.datasets import DatasetMetadata, DatasetRepository


logger = get_logger()


@dataclass
class CompiledInteractiveProgram:
    """Simple nearest-neighbor matcher backed by a compiled artifact."""

    version: str
    trainset: list[dict[str, Any]]
    metric: dict[str, Any] | None = None

    def predict(
        self,
        question: str,
        dataset_meta: DatasetMetadata,
    ) -> QuerySpecModel | None:
        """Return the closest query_spec from the compiled trainset."""

        def _score(example: dict[str, Any]) -> int:
            tokens = set(question.lower().split())
            example_tokens = set(str(example.get("question", "")).lower().split())
            overlap = len(tokens & example_tokens)
            dataset_meta_dict = example.get("dataset_meta", {})
            dataset_match = int(dataset_meta_dict.get("id") == dataset_meta["id"])
            return overlap + dataset_match

        if not self.trainset:
            return None

        ranked = sorted(self.trainset, key=_score, reverse=True)
        best = ranked[0]
        best_score = _score(best)
        if best_score == 0:
            return None

        query_spec = cast("QuerySpecDict", best.get("query_spec") or {})
        return QuerySpecModel.model_validate(query_spec)


def load_compiled_program() -> CompiledInteractiveProgram | None:
    """Load compiled interactive program artifact from disk if present."""
    artifact_path = (
        Path(__file__).resolve().parents[3]
        / "dspy"
        / "interactive"
        / "compiled_program.json"
    )
    if not artifact_path.exists():
        logger.info("No compiled program found, falling back to rule-based pipeline")
        return None

    try:
        payload = artifact_path.read_text(encoding="utf-8")
        data = json.loads(payload)
        version = data.get("version") or artifact_path.stem
        return CompiledInteractiveProgram(
            version=str(version),
            trainset=data.get("trainset", []),
            metric=data.get("metric"),
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to load compiled program", error=str(exc))
        return None


class InteractiveAnalysisProgram:
    """Chain NL question -> QuerySpec -> query execution -> summarization."""

    def __init__(
        self,
        repo: DatasetRepository,
        runner: QueryRunner | None = None,
        compiled_program: CompiledInteractiveProgram | None = None,
    ) -> None:
        """Initialize the program with a repository and optional runner."""
        self.repo = repo
        self.generator = RuleBasedQueryGenerator()
        self.runner = runner or QueryRunner(repo.session)
        self.compiled_program = compiled_program or load_compiled_program()
        self.program_version = (
            self.compiled_program.version if self.compiled_program else "rule-based-v1"
        )

    def run(self, request: InteractiveRequest) -> InteractiveResponse:
        """Execute NL question to query to result pipeline."""
        dataset_meta = self.repo.get_dataset_metadata(request.dataset_id)
        query_spec_model = None
        used_version = self.program_version
        if self.compiled_program:
            query_spec_model = self.compiled_program.predict(
                request.question,
                dataset_meta,
            )
        if query_spec_model is None:
            query_spec_model = self.generator.generate(request.question, dataset_meta)
            used_version = "rule-based-v1"

        query_spec_dict = cast(
            "QuerySpecDict",
            query_spec_model.model_dump(),
        )
        result = self.runner.run(request.dataset_id, query_spec_dict)
        insight = self._summarize(request.question, result)
        analysis = self.repo.record_analysis(
            dataset_id=request.dataset_id,
            question=request.question,
            query_spec=dict(query_spec_dict),
            result_summary=result["summary"],
            provider=request.provider,
            model=request.model,
            program_version=used_version,
        )
        query_spec_payload: dict[str, Any] = dict(query_spec_dict)

        return InteractiveResponse(
            dataset_id=request.dataset_id,
            question=request.question,
            query_spec=QuerySpecModel.model_validate(query_spec_payload),
            data=result["data"],
            stats=result["summary"],
            insight=insight,
            summary=insight,
            analysis_id=analysis.id,
            program_version=used_version,
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
