"""Execution engine for query specs against dataset records."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

from clean_interfaces.services.datasets import DatasetRepository

if TYPE_CHECKING:  # pragma: no cover - type checking imports
    from sqlalchemy.orm import Session

class QueryValidationError(ValueError):
    """Raised when a query spec references invalid columns."""


class QueryRunner:
    """Run QuerySpecs on stored dataset records."""

    def __init__(self, session: Session) -> None:
        """Initialize the runner with a dataset repository."""
        self.repo = DatasetRepository(session)

    def run(self, dataset_id: int, query_spec: dict[str, Any]) -> dict[str, Any]:
        """Execute the provided query spec and return data, summary, and schema."""
        dataset_meta = self.repo.get_dataset_metadata(dataset_id)
        valid_columns = {col["name"] for col in dataset_meta["columns"]}
        self._validate(query_spec, valid_columns)

        records = self.repo.get_records(dataset_id)
        frame = pd.DataFrame(records)
        frame = self._apply_filters(frame, query_spec.get("filters", []))
        frame = self._ensure_columns(frame, valid_columns)

        result_frame = self._apply_group_and_metrics(frame, query_spec)
        result_frame = self._apply_order_and_limit(result_frame, query_spec)

        summary = self._build_summary(frame, result_frame, query_spec)
        return {
            "data": result_frame.to_dict(orient="records"),
            "summary": summary,
            "schema": dataset_meta["columns"],
        }

    def _validate(self, query_spec: dict[str, Any], valid_columns: set[str]) -> None:
        for filter_item in query_spec.get("filters", []) or []:
            column = filter_item.get("column")
            if column and column not in valid_columns:
                msg = f"Unknown filter column: {column}"
                raise QueryValidationError(msg)

        for group in query_spec.get("group_by", []) or []:
            if group not in valid_columns:
                msg = f"Unknown group_by column: {group}"
                raise QueryValidationError(msg)

        allowed_aggs = {"count", "avg", "sum", "max", "min"}
        for metric in query_spec.get("metrics", []) or []:
            agg = metric.get("agg", "count")
            column = metric.get("column")
            if agg not in allowed_aggs:
                msg = f"Unsupported aggregator: {agg}"
                raise QueryValidationError(msg)
            if column and column not in valid_columns:
                msg = f"Unknown metric column: {column}"
                raise QueryValidationError(msg)

        for order in query_spec.get("order_by", []) or []:
            column = order.get("column")
            if column and column not in valid_columns:
                msg = f"Unknown order_by column: {column}"
                raise QueryValidationError(msg)

    def _ensure_columns(
        self, frame: pd.DataFrame, valid_columns: set[str],
    ) -> pd.DataFrame:
        missing_columns = [col for col in frame.columns if col not in valid_columns]
        if missing_columns:
            frame = frame.drop(columns=missing_columns)
        return frame

    def _apply_filters(self, frame: pd.DataFrame, filters: list[dict]) -> pd.DataFrame:
        filtered = frame.copy()
        for filter_item in filters:
            column = filter_item.get("column")
            op = filter_item.get("op", "eq")
            value = filter_item.get("value")
            if column not in filtered.columns:
                msg = f"Unknown filter column: {column}"
                raise QueryValidationError(msg)
            if op == "eq":
                filtered = filtered[filtered[column] == value]
            elif op == "gte":
                filtered = filtered[filtered[column] >= value]
            elif op == "lte":
                filtered = filtered[filtered[column] <= value]
            elif op == "gt":
                filtered = filtered[filtered[column] > value]
            elif op == "lt":
                filtered = filtered[filtered[column] < value]
            else:
                msg = f"Unsupported operator: {op}"
                raise QueryValidationError(msg)
        return filtered

    def _apply_group_and_metrics(
        self, frame: pd.DataFrame, query_spec: dict[str, Any],
    ) -> pd.DataFrame:
        group_by = query_spec.get("group_by") or []
        metrics = query_spec.get("metrics") or []

        agg_map = {
            "avg": "mean",
            "sum": "sum",
            "max": "max",
            "min": "min",
            "count": "count",
        }

        if not group_by:
            return self._apply_metrics(frame, metrics)

        grouped = frame.groupby(group_by, dropna=False)
        agg_mapping: dict[str, list[str]] = {}
        count_requested = False
        for metric in metrics:
            agg = metric.get("agg", "count")
            column = metric.get("column")
            if agg == "count" and column is None:
                count_requested = True
                continue
            if column:
                agg_mapping.setdefault(column, []).append(agg_map.get(agg, agg))

        if agg_mapping:
            aggregated = grouped.agg(agg_mapping)
        else:
            aggregated = grouped.size().to_frame("count")

        if hasattr(aggregated, "columns") and isinstance(
            aggregated.columns, pd.MultiIndex,
        ):
            aggregated.columns = [
                "_".join(
                    filter(
                        None, [col if isinstance(col, str) else col[0] for col in cols],
                    ),
                )
                for cols in aggregated.columns.to_flat_index()
            ]

        aggregated = aggregated.reset_index()

        if count_requested:
            aggregated["count"] = grouped.size().to_numpy()
        return aggregated

    def _apply_metrics(self, frame: pd.DataFrame, metrics: list[dict]) -> pd.DataFrame:
        result: dict[str, Any] = {}
        agg_map = {
            "avg": "mean",
            "sum": "sum",
            "max": "max",
            "min": "min",
            "count": "count",
        }
        for metric in metrics:
            agg = agg_map.get(metric.get("agg", "count"), metric.get("agg", "count"))
            column = metric.get("column")
            if agg == "count":
                result["count"] = len(frame)
            elif column and agg == "mean":
                result[f"avg_{column}"] = frame[column].mean()
            elif column and agg == "sum":
                result[f"sum_{column}"] = frame[column].sum()
            elif column and agg == "max":
                result[f"max_{column}"] = frame[column].max()
            elif column and agg == "min":
                result[f"min_{column}"] = frame[column].min()
        return pd.DataFrame([result])

    def _apply_order_and_limit(
        self, frame: pd.DataFrame, query_spec: dict[str, Any],
    ) -> pd.DataFrame:
        order_by = query_spec.get("order_by") or []
        if order_by:
            resolved_columns: list[str] = []
            ascending: list[bool] = []
            for item in order_by:
                target = item.get("column")
                candidate = target
                if target not in frame.columns:
                    candidate = next(
                        (
                            col
                            for col in frame.columns
                            if col.endswith(f"_{target}")
                            or col.startswith(f"{target}_")
                        ),
                        None,
                    )
                if candidate and candidate in frame.columns:
                    resolved_columns.append(candidate)
                    ascending.append(item.get("direction", "asc") != "desc")
            if resolved_columns:
                frame = frame.sort_values(by=resolved_columns, ascending=ascending)
        limit = query_spec.get("limit")
        if isinstance(limit, int) and limit > 0:
            frame = frame.head(limit)
        return frame

    def _build_summary(
        self,
        source_frame: pd.DataFrame,
        result_frame: pd.DataFrame,
        query_spec: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "requested_rows": len(source_frame),
            "returned_rows": len(result_frame),
            "group_by": query_spec.get("group_by") or [],
            "metrics": query_spec.get("metrics") or [],
            "filters": query_spec.get("filters") or [],
        }
