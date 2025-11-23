from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class FeedbackRequest(BaseModel):
    """Payload for recording feedback from interactive or batch insights."""

    insight_id: int | None = Field(
        default=None,
        description="Insight candidate ID from batch exploration",
    )
    analysis_id: int | None = Field(
        default=None,
        description="AnalysisQuery ID from interactive mode",
    )
    rating: int = Field(..., description="+1 for thumbs up, -1 for thumbs down")
    comment: str | None = Field(default=None, description="Free-form feedback")
    target_module: Literal["interactive", "batch", "other"] = Field(
        ...,
        description="UI surface that collected the feedback",
    )

    @model_validator(mode="after")
    def validate_targets(self) -> FeedbackRequest:  # pragma: no cover - pydantic
        """Ensure either insight_id or analysis_id is supplied and rating is nonzero."""
        if self.insight_id is None and self.analysis_id is None:
            msg = "Either insight_id or analysis_id must be provided"
            raise ValueError(msg)
        if self.rating == 0:
            msg = "rating must be positive or negative"
            raise ValueError(msg)
        return self


class FeedbackResponse(BaseModel):
    """Response returned after storing feedback."""

    feedback_id: int
    target_module: str
    rating: int
    analysis_id: int | None = None
    insight_id: int | None = None
    message: str
