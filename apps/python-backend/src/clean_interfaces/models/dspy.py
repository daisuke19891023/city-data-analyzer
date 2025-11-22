"""Pydantic models for DSPy-like interactive analysis."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QueryFilter(BaseModel):
    column: str
    op: str = Field(default="eq")
    value: Any


class QueryMetric(BaseModel):
    agg: str
    column: str | None = None


class QueryOrder(BaseModel):
    column: str
    direction: str = Field(default="asc")


class QuerySpecModel(BaseModel):
    filters: list[QueryFilter] = Field(default_factory=list)
    group_by: list[str] = Field(default_factory=list)
    metrics: list[QueryMetric] = Field(default_factory=list)
    order_by: list[QueryOrder] = Field(default_factory=list)
    limit: int | None = None


class InteractiveRequest(BaseModel):
    dataset_id: int
    question: str
    provider: str | None = None
    model: str | None = None


class InteractiveResponse(BaseModel):
    dataset_id: int
    question: str
    query_spec: QuerySpecModel
    data: list[dict]
    stats: dict
    insight: str
