"""Generate trainset JSON from positive insight feedback."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import select

from city_data_backend.database import configure_engine, get_session
from city_data_backend.db_models import AnalysisQuery, InsightCandidate, InsightFeedback
from city_data_backend.services.datasets import DatasetRepository

logger = structlog.get_logger()


def build_trainset(min_rating: int) -> list[dict[str, Any]]:
    """Extract feedback entries with rating above threshold."""
    session = get_session()
    repo = DatasetRepository(session)
    feedback_records = session.execute(
        select(InsightFeedback).where(InsightFeedback.rating >= min_rating),
    ).scalars()
    trainset: list[dict[str, Any]] = []
    for record in feedback_records:
        if record.candidate_id:
            candidate = session.get(InsightCandidate, record.candidate_id)
            if not candidate:
                continue
            job = candidate.job
            dataset_meta = repo.get_dataset_metadata(candidate.dataset_id)
            trainset.append(
                {
                    "source": "batch",
                    "feedback_id": record.id,
                    "insight_id": candidate.id,
                    "question": candidate.title,
                    "dataset_meta": dataset_meta,
                    "query_spec": job.query_spec if job else {},
                    "insight_description": candidate.description,
                },
            )
        elif record.analysis_id:
            analysis = session.get(AnalysisQuery, record.analysis_id)
            if not analysis:
                continue
            dataset_meta = repo.get_dataset_metadata(analysis.dataset_id)
            trainset.append(
                {
                    "source": "interactive",
                    "feedback_id": record.id,
                    "analysis_id": analysis.id,
                    "question": analysis.question,
                    "dataset_meta": dataset_meta,
                    "query_spec": analysis.query_spec,
                    "insight_description": analysis.result_summary,
                    "program_version": analysis.program_version,
                },
            )
    return trainset


def main() -> None:
    """Generate a trainset JSON from high-rated feedback records."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="Override DATABASE_URL for extraction",
    )
    parser.add_argument(
        "--min-rating",
        type=int,
        default=1,
        help="Minimum rating to include",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "apps/python-backend/dspy/interactive/trainset_from_feedback.json",
        ),
        help="Where to write the generated trainset",
    )
    args = parser.parse_args()

    if args.database_url:
        configure_engine(args.database_url)

    trainset = build_trainset(args.min_rating)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(trainset, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(
        "Exported trainset from feedback",
        count=len(trainset),
        output=str(args.output),
        min_rating=args.min_rating,
    )


if __name__ == "__main__":
    main()
