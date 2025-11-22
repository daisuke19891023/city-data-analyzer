"""Pydantic models for DSPy-like interactive analysis."""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from pydantic import BaseModel, Field


class QueryFilter(BaseModel):
    """Filter condition for a query specification."""

    column: str
    op: str = Field(default="eq")
    value: Any


class QueryMetric(BaseModel):
    """Aggregation metric description."""

    agg: str
    column: str | None = None


class QueryOrder(BaseModel):
    """Ordering directive for query results."""

    column: str
    direction: str = Field(default="asc")


class QueryFilterDict(TypedDict):
    """Dict representation of a query filter."""

    column: str
    op: str
    value: Any


class QueryMetricDict(TypedDict):
    """Dict representation of a query metric."""

    agg: str
    column: str | None


class QueryOrderDict(TypedDict):
    """Dict representation of an order by clause."""

    column: str
    direction: str


class QuerySpecDict(TypedDict, total=False):
    """Loosely-typed dictionary form of QuerySpecModel."""

    filters: list[QueryFilterDict]
    group_by: list[str]
    metrics: list[QueryMetricDict]
    order_by: list[QueryOrderDict]
    limit: int | None


class QuerySpecModel(BaseModel):
    """Structured representation of a query spec."""

    filters: Annotated[list[QueryFilter], Field(default_factory=list)]
    group_by: Annotated[list[str], Field(default_factory=list)]
    metrics: Annotated[list[QueryMetric], Field(default_factory=list)]
    order_by: Annotated[list[QueryOrder], Field(default_factory=list)]
    limit: int | None = None


class InteractiveRequest(BaseModel):
    """Request payload for the interactive DSPy endpoint."""

    dataset_id: int
    question: str
    provider: str | None = None
    model: str | None = None


class InteractiveResponse(BaseModel):
    """Response payload including query spec, data, stats, and insight."""

    dataset_id: int
    question: str
    query_spec: QuerySpecModel
    data: list[dict[str, Any]]
    stats: dict[str, Any]
    insight: str
    summary: str | None = None
    analysis_id: int | None = None
    program_version: str | None = None
