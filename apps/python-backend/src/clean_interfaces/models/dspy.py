"""Pydantic models for DSPy-like interactive analysis."""

from __future__ import annotations

from typing import Any

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


class QuerySpecModel(BaseModel):
    """Structured representation of a query spec."""

    filters: list[QueryFilter] = Field(default_factory=list)
    group_by: list[str] = Field(default_factory=list)
    metrics: list[QueryMetric] = Field(default_factory=list)
    order_by: list[QueryOrder] = Field(default_factory=list)
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
    data: list[dict]
    stats: dict
    insight: str
