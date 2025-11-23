"""Lightweight DSPy-inspired interactive analysis pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from structlog import get_logger
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from clean_interfaces.models.dspy import (
    InteractiveRequest,
    InteractiveResponse,
    QuerySpecDict,
    QuerySpecModel,
)
from clean_interfaces.services.query_runner import QueryRunner
from clean_interfaces.services.query_spec import RuleBasedQueryGenerator
from clean_interfaces.database import get_session
from clean_interfaces.db_models import CompiledProgramArtifact

if TYPE_CHECKING:  # pragma: no cover - type checking imports
    from sqlalchemy.orm import Session

    from clean_interfaces.services.datasets import DatasetMetadata, DatasetRepository


logger = get_logger()

DEFAULT_ARTIFACT_ROOT = Path(__file__).resolve().parents[3] / "dspy" / "optimization"


def _artifact_root(base_dir: Path | None = None) -> Path:
    """Return artifact root directory, creating it if necessary."""
    root = base_dir or DEFAULT_ARTIFACT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    return root


def persist_compiled_program(
    version: str,
    trainset: list[dict[str, Any]],
    metric: dict[str, Any] | None,
    session: Session | None = None,
    base_dir: Path | None = None,
) -> CompiledProgramArtifact:
    """Persist compiled artifact JSON and record metadata in the database."""
    managed_session = session is None
    db_session = session or get_session()
    try:
        artifact_dir = _artifact_root(base_dir)
        artifact_path = artifact_dir / f"{version}.json"
        payload = {"version": version, "trainset": trainset, "metric": metric}
        artifact_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        record = CompiledProgramArtifact(
            version=version,
            trainset=trainset,
            metric=metric,
            path=str(artifact_path),
            active=False,
        )
        db_session.add(record)
        try:
            db_session.commit()
        except IntegrityError as exc:
            db_session.rollback()
            msg = f"Artifact version '{version}' already exists"
            raise ValueError(msg) from exc
        db_session.refresh(record)
        return record
    finally:
        if managed_session:
            db_session.close()


def set_active_program(
    artifact_id: int,
    active: bool,
    session: Session | None = None,
) -> CompiledProgramArtifact:
    """Toggle active flag for a compiled program artifact."""
    managed_session = session is None
    db_session = session or get_session()
    try:
        artifact = db_session.get(CompiledProgramArtifact, artifact_id)
        if artifact is None:
            msg = "Artifact not found"
            raise LookupError(msg)

        if active:
            db_session.execute(update(CompiledProgramArtifact).values(active=False))
        artifact.active = active
        db_session.commit()
        db_session.refresh(artifact)
        return artifact
    finally:
        if managed_session:
            db_session.close()


def list_program_artifacts(
    session: Session | None = None,
) -> list[CompiledProgramArtifact]:
    """Return compiled program artifacts ordered by creation time desc."""
    managed_session = session is None
    db_session = session or get_session()
    try:
        stmt = select(CompiledProgramArtifact).order_by(
            CompiledProgramArtifact.created_at.desc(),
        )
        return list(db_session.execute(stmt).scalars().all())
    finally:
        if managed_session:
            db_session.close()


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


def _resolve_artifact_record(
    db_session: Session,
    version: str | None,
) -> CompiledProgramArtifact | None:
    if version:
        stmt = (
            select(CompiledProgramArtifact)
            .where(CompiledProgramArtifact.version == version)
            .order_by(CompiledProgramArtifact.created_at.desc())
        )
        return db_session.execute(stmt).scalar_one_or_none()

    active_stmt = (
        select(CompiledProgramArtifact)
        .where(CompiledProgramArtifact.active.is_(True))
        .order_by(CompiledProgramArtifact.created_at.desc())
    )
    artifact = db_session.execute(active_stmt).scalar_one_or_none()
    if artifact:
        return artifact

    fallback_stmt = select(CompiledProgramArtifact).order_by(
        CompiledProgramArtifact.created_at.desc(),
    )
    return db_session.execute(fallback_stmt).scalar_one_or_none()


def load_compiled_program(
    version: str | None = None,
    session: Session | None = None,
    base_dir: Path | None = None,
) -> CompiledInteractiveProgram | None:
    """Load compiled interactive program artifact from disk if present."""
    managed_session = session is None
    db_session = session or get_session()
    artifact_record: CompiledProgramArtifact | None = None

    try:
        try:
            artifact_record = _resolve_artifact_record(db_session, version)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to resolve artifact record", error=str(exc))

        if artifact_record:
            artifact_path = Path(artifact_record.path)
        elif version:
            artifact_path = _artifact_root(base_dir) / f"{version}.json"
        else:
            artifact_path = (
                Path(__file__).resolve().parents[3]
                / "dspy"
                / "interactive"
                / "compiled_program.json"
            )

        if not artifact_path.exists():
            logger.info(
                "No compiled program found, falling back to rule-based pipeline",
            )
            return None

        payload = artifact_path.read_text(encoding="utf-8")
        data = json.loads(payload)
        version_value = (
            data.get("version")
            or (artifact_record.version if artifact_record else None)
            or artifact_path.stem
        )
        return CompiledInteractiveProgram(
            version=str(version_value),
            trainset=data.get("trainset", []),
            metric=data.get("metric"),
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to load compiled program", error=str(exc))
        return None
    finally:
        if managed_session:
            db_session.close()


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
