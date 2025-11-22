"""Pydantic models for experiment-related endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime

    from clean_interfaces.models.dspy import QuerySpecModel
else:  # pragma: no cover - runtime types for pydantic validation
    from datetime import datetime  # noqa: TC003
    from clean_interfaces.models.dspy import QuerySpecModel  # noqa: TC001


class ExperimentCreateRequest(BaseModel):
    """Request payload for creating an experiment."""

    goal_description: str = Field(..., description="User-provided analytical goal")
    dataset_ids: list[int] = Field(
        ..., description="Target dataset identifiers", min_length=1,
    )


class ExperimentCreateResponse(BaseModel):
    """Response payload after creating an experiment."""

    experiment_id: int
    job_count: int


class ExperimentJobModel(BaseModel):
    """Serialized job for API responses."""

    id: int
    dataset_id: int
    job_type: str
    description: str | None = None
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class ExperimentModel(BaseModel):
    """Experiment representation with jobs."""

    id: int
    goal_description: str
    dataset_ids: list[int]
    status: str
    created_at: datetime
    updated_at: datetime
    jobs: list[ExperimentJobModel] = Field(default_factory=list)


class InsightCandidateModel(BaseModel):
    """Serialized insight candidate."""

    id: int
    experiment_id: int
    job_id: int | None
    dataset_id: int
    title: str
    description: str
    metrics: dict[str, Any] | None = None
    adopted: bool
    feedback_comment: str | None = None
    created_at: datetime


class InsightsResponse(BaseModel):
    """Response wrapper for insight list."""

    insights: list[InsightCandidateModel]


class InsightFeedbackRequest(BaseModel):
    """Request payload for adopting/rejecting insight candidates."""

    decision: str = Field(..., description="adopted or rejected")
    comment: str | None = None


class PlannedJob(BaseModel):
    """Job produced by PlanExperiments."""

    dataset_id: int
    job_type: str
    description: str
    query_spec: QuerySpecModel
