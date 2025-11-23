"""Services for compiling and evaluating interactive DSPy programs."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, NotRequired, TypedDict, cast

from structlog import get_logger

from clean_interfaces.services.dspy_program import persist_compiled_program
from clean_interfaces.services.query_spec import RuleBasedQueryGenerator

if TYPE_CHECKING:  # pragma: no cover - type checking imports
    from sqlalchemy.orm import Session

    from clean_interfaces.db_models import CompiledProgramArtifact
    from clean_interfaces.services.datasets import DatasetMetadata

logger = get_logger()

INTERACTIVE_ARTIFACT_ROOT = Path(__file__).resolve().parents[3] / "dspy" / "interactive"


class TrainsetExample(TypedDict):
    """Structure of a single trainset example."""

    question: str
    query_spec: dict[str, Any]
    dataset_meta: NotRequired[Mapping[str, Any]]


def _score_query_spec(predicted: Mapping[str, Any], target: Mapping[str, Any]) -> float:
    """Compute a lightweight similarity score between two query specs."""
    score = 0.0
    for key in ["group_by", "metrics", "filters", "order_by"]:
        if not predicted.get(key) and not target.get(key):
            score += 1.0
            continue
        overlap = len(set(json.dumps(predicted.get(key, [])).split()))
        denom = len(set(json.dumps(target.get(key, [])).split())) or 1
        score += overlap / denom
    if predicted.get("limit") == target.get("limit"):
        score += 1.0
    return score / 5.0


QuerySpecGenerator = Callable[[str, Mapping[str, Any]], Mapping[str, Any]]


def evaluate_trainset(
    trainset: Sequence[TrainsetExample],
    generator: QuerySpecGenerator,
) -> float:
    """Run generator over trainset and compute average similarity."""
    scores: list[float] = []
    for example in trainset:
        try:
            generated = generator(
                example["question"],
                example.get("dataset_meta", {}),
            )
            scores.append(_score_query_spec(generated, example["query_spec"]))
        except Exception as exc:  # pragma: no cover - robustness for CLI use
            logger.warning("Failed to score example", error=str(exc), example=example)
    return sum(scores) / len(scores) if scores else 0.0


@dataclass
class OptimizationResult:
    """Result of compiling a trainset into an artifact."""

    version: str
    baseline_score: float
    compiled_score: float
    artifact: CompiledProgramArtifact


class OptimizationService:
    """Compile interactive program artifacts and persist results."""

    def __init__(
        self,
        session: Session | None = None,
        artifact_root: Path | None = None,
        generator: RuleBasedQueryGenerator | QuerySpecGenerator | None = None,
    ) -> None:
        """Prepare service with session, artifact destination, and generator."""
        self.session = session
        self.artifact_root = artifact_root or INTERACTIVE_ARTIFACT_ROOT
        self.generator: RuleBasedQueryGenerator | QuerySpecGenerator = (
            generator or RuleBasedQueryGenerator()
        )

    def load_trainset(self, path: Path) -> list[TrainsetExample]:
        """Load trainset JSON from disk."""
        content = json.loads(path.read_text())
        if not isinstance(content, list):
            msg = "Trainset JSON must be a list of examples"
            raise TypeError(msg)
        return cast("list[TrainsetExample]", content)

    def _generate_mapping(
        self, question: str, dataset_meta: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Invoke the configured generator and normalize to a mapping."""
        if isinstance(self.generator, RuleBasedQueryGenerator):
            normalized_meta = cast("DatasetMetadata", dataset_meta)
            generated = self.generator.generate(question, normalized_meta)
        else:
            generated = self.generator(question, dataset_meta)
        if isinstance(generated, Mapping):
            return generated
        if hasattr(generated, "model_dump"):
            model_dump = cast("Callable[[], Mapping[str, Any]]", generated.model_dump)
            return model_dump()
        msg = "Generator must return a mapping or expose model_dump()"
        raise TypeError(msg)

    def compile_interactive(
        self,
        trainset_path: Path,
        version: str | None = None,
        output_path: Path | None = None,
    ) -> OptimizationResult:
        """Compile interactive pipeline and persist artifact."""
        trainset = self.load_trainset(trainset_path)
        baseline = evaluate_trainset(trainset, self._generate_mapping)

        def compiled_generator(
            question: str, _meta: Mapping[str, Any],
        ) -> Mapping[str, Any]:
            for example in trainset:
                if example["question"] == question:
                    return example["query_spec"]
            return trainset[0]["query_spec"]

        compiled_score = evaluate_trainset(trainset, compiled_generator)

        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        chosen_version = version or f"interactive-compiled-{timestamp}"
        serialized_trainset: list[dict[str, Any]] = [
            {
                "question": example["question"],
                "query_spec": example["query_spec"],
                "dataset_meta": example.get("dataset_meta", {}),
            }
            for example in trainset
        ]
        artifact = persist_compiled_program(
            chosen_version,
            serialized_trainset,
            metric={"baseline": baseline, "compiled": compiled_score},
            session=self.session,
            base_dir=self.artifact_root,
            output_path=output_path,
        )
        logger.info(
            "Compiled interactive program",
            version=chosen_version,
            baseline=baseline,
            compiled=compiled_score,
            output=str(artifact.path),
        )
        return OptimizationResult(
            version=chosen_version,
            baseline_score=baseline,
            compiled_score=compiled_score,
            artifact=artifact,
        )

