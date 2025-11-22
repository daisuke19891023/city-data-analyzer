"""Rule-based NL to QuerySpec generator."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class QuerySpec:
    """In-memory representation of a generated query specification."""

    filters: list[dict]
    group_by: list[str]
    metrics: list[dict]
    order_by: list[dict]
    limit: int | None = None

    def model_dump(self) -> dict:
        """Return a plain dictionary representation."""
        return {
            "filters": self.filters,
            "group_by": self.group_by,
            "metrics": self.metrics,
            "order_by": self.order_by,
            "limit": self.limit,
        }


class RuleBasedQueryGenerator:
    """Generate a QuerySpec using lightweight heuristics."""

    def __init__(self) -> None:
        """Prepare keyword mappings for metric detection."""
        self.metric_keywords = {
            "avg": ["平均", "average", "mean"],
            "sum": ["合計", "総", "sum", "total"],
            "max": ["最大", "highest", "max"],
            "min": ["最小", "lowest", "min"],
            "count": ["件数", "数", "count"],
        }

    def generate(self, question: str, dataset_meta: dict[str, Any]) -> QuerySpec:
        """Generate a QuerySpec from a question and dataset metadata."""
        columns = dataset_meta.get("columns", [])
        normalized_question = question.lower()
        group_by = self._detect_group_by(normalized_question, columns)
        metrics = self._detect_metrics(normalized_question, columns)
        filters = self._detect_filters(question, columns)
        order_by = self._detect_order(normalized_question, group_by, metrics)
        limit = 20
        return QuerySpec(
            filters=filters,
            group_by=group_by,
            metrics=metrics,
            order_by=order_by,
            limit=limit,
        )

    def _detect_group_by(self, question: str, columns: list[dict]) -> list[str]:
        candidates = []
        for column in columns:
            name = column["name"].lower()
            if re.search(r"year|年度|年", question) and re.search(
                r"year|年度|年", name,
            ):
                candidates.append(column["name"])
            if re.search(r"ward|区", question) and (
                "ward" in name or "区" in column["name"]
            ):
                candidates.append(column["name"])
        return list(dict.fromkeys(candidates))

    def _detect_metrics(self, question: str, columns: list[dict]) -> list[dict]:
        metrics: list[dict] = []
        numeric_columns = [col for col in columns if col.get("data_type") == "number"]
        for agg, keywords in self.metric_keywords.items():
            if any(keyword in question for keyword in keywords):
                target_column = numeric_columns[0]["name"] if numeric_columns else None
                metrics.append({"agg": agg, "column": target_column})
        if not metrics:
            metrics.append({"agg": "count", "column": None})
        return metrics

    def _detect_filters(self, question: str, columns: list[dict]) -> list[dict]:
        filters: list[dict] = []
        year_match = re.search(r"(20\d{2})年?", question)
        if year_match:
            year = int(year_match.group(1))
            year_columns = [
                col
                for col in columns
                if re.search(r"year|年度|年", col["name"], re.IGNORECASE)
            ]
            if year_columns:
                filters.append(
                    {"column": year_columns[0]["name"], "op": "eq", "value": year},
                )
        return filters

    def _detect_order(
        self, question: str, group_by: list[str], metrics: list[dict],
    ) -> list[dict]:
        if metrics:
            metric = metrics[0]
            column = metric["column"] or metrics[0].get("column")
            if column:
                direction = (
                    "desc"
                    if any(word in question for word in ["高い", "多い", "最大", "top"])
                    else "asc"
                )
                return [{"column": column, "direction": direction}]
        if group_by:
            return [{"column": group_by[0], "direction": "asc"}]
        return []
