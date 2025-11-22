from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from clean_interfaces.db_models import AnalysisQuery, InsightCandidate, InsightFeedback

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from clean_interfaces.models.feedback import FeedbackRequest


class FeedbackService:
    """Service layer for storing feedback records."""

    def __init__(self, session: Session) -> None:
        """Store the session for reuse across operations."""
        self.session = session

    def submit(self, payload: FeedbackRequest) -> InsightFeedback:
        """Persist feedback for an insight candidate or analysis."""
        if payload.insight_id is None and payload.analysis_id is None:
            msg = "Either insight_id or analysis_id is required"
            raise ValueError(msg)

        candidate = None
        analysis = None
        if payload.insight_id is not None:
            candidate = self.session.get(InsightCandidate, payload.insight_id)
            if candidate is None:
                msg = f"InsightCandidate {payload.insight_id} not found"
                raise LookupError(msg)
            candidate.adopted = payload.rating > 0
            if payload.comment:
                candidate.feedback_comment = payload.comment

        if payload.analysis_id is not None:
            analysis = self.session.get(AnalysisQuery, payload.analysis_id)
            if analysis is None:
                msg = f"AnalysisQuery {payload.analysis_id} not found"
                raise LookupError(msg)

        feedback = InsightFeedback(
            candidate_id=candidate.id if candidate else None,
            analysis_id=analysis.id if analysis else None,
            rating=payload.rating,
            comment=payload.comment,
            target_module=payload.target_module,
            created_at=datetime.now(UTC),
        )
        self.session.add(feedback)
        self.session.commit()
        self.session.refresh(feedback)
        return feedback

    def summarize(self) -> dict[str, Any]:
        """Return basic aggregates useful for monitoring feedback quality."""
        records = self.session.query(InsightFeedback).all()
        if not records:
            return {"count": 0, "avg_rating": None}
        ratings = [record.rating for record in records]
        avg_rating = sum(ratings) / len(ratings)
        return {"count": len(records), "avg_rating": avg_rating}
