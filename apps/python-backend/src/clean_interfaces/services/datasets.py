"""Dataset ingestion and metadata utilities."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from typing import TYPE_CHECKING, Any, Iterable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from clean_interfaces.db_models import (
    AnalysisQuery,
    Dataset,
    DatasetColumn,
    DatasetFile,
    DatasetRecord,
    OpenDataCategory,
)
from clean_interfaces.database import init_db

if TYPE_CHECKING:  # pragma: no cover - imports for type checking only
    from pathlib import Path
    from sqlalchemy.orm import Session

DEFAULT_OPEN_DATA_CATEGORIES: list[tuple[str, str]] = [
    ("population", "人口・世帯"),
    ("economy", "経済・雇用"),
    ("welfare", "福祉"),
    ("health", "健康"),
    ("environment", "環境"),
    ("education", "教育"),
    ("culture", "文化・スポーツ"),
    ("safety", "防犯・消防"),
    ("infrastructure", "都市基盤"),
    ("transport", "交通"),
    ("childcare", "子育て"),
    ("industry", "産業振興"),
]


class DatasetRepository:
    """Repository to manage datasets and records."""

    def __init__(self, session: Session) -> None:
        """Store the SQLAlchemy session used by repository methods."""
        self.session = session

    def seed_categories(self) -> None:
        """Ensure the default 12 categories are present."""
        existing = {
            slug
            for (slug,) in self.session.execute(select(OpenDataCategory.slug)).all()
        }
        for slug, name in DEFAULT_OPEN_DATA_CATEGORIES:
            if slug not in existing:
                self.session.add(OpenDataCategory(slug=slug, name=name))
        self.session.commit()

    def ensure_category(self, slug: str, name: str) -> OpenDataCategory:
        """Fetch or create a category."""
        category = self.session.scalar(
            select(OpenDataCategory).where(OpenDataCategory.slug == slug),
        )
        if category is None:
            category = OpenDataCategory(slug=slug, name=name)
            self.session.add(category)
            self.session.commit()
        return category

    def ensure_dataset(
        self,
        category_slug: str,
        dataset_slug: str,
        dataset_name: str,
        description: str,
        year: int | None,
    ) -> Dataset:
        """Fetch or create a dataset under the given category."""
        category_name = dict(DEFAULT_OPEN_DATA_CATEGORIES).get(
            category_slug, category_slug,
        )
        category = self.ensure_category(category_slug, category_name)
        dataset = self.session.scalar(
            select(Dataset).where(Dataset.slug == dataset_slug),
        )
        if dataset:
            return dataset

        dataset = Dataset(
            category=category,
            slug=dataset_slug,
            name=dataset_name,
            description=description,
            year=year,
        )
        self.session.add(dataset)
        self.session.commit()
        return dataset

    def upsert_columns(self, dataset: Dataset, columns: list[dict[str, Any]]) -> None:
        """Insert column metadata if missing."""
        existing = {col.name: col for col in dataset.columns}
        for column in columns:
            if column["name"] in existing:
                col = existing[column["name"]]
                col.data_type = column["data_type"]
                col.description = column.get("description")
                col.is_index = column.get("is_index", False)
            else:
                self.session.add(
                    DatasetColumn(
                        dataset_id=dataset.id,
                        name=column["name"],
                        data_type=column.get("data_type", "text"),
                        description=column.get("description"),
                        is_index=column.get("is_index", False),
                    ),
                )
        self.session.commit()

    def add_record(
        self, dataset: Dataset, row_json: dict[str, Any], index_cols: dict[str, Any],
    ) -> None:
        """Insert a record if it does not already exist (idempotent)."""
        row_hash = hashlib.sha256(
            json.dumps(row_json, sort_keys=True, ensure_ascii=False).encode("utf-8"),
        ).hexdigest()
        record = DatasetRecord(
            dataset_id=dataset.id,
            row_json=row_json,
            index_cols=index_cols,
            row_hash=row_hash,
        )
        self.session.add(record)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

    def add_file(
        self, dataset: Dataset, path: str, file_type: str = "csv",
    ) -> DatasetFile:
        """Record an imported file."""
        file_entry = DatasetFile(dataset_id=dataset.id, path=path, file_type=file_type)
        self.session.add(file_entry)
        self.session.commit()
        return file_entry

    def import_csv(
        self,
        category_slug: str,
        dataset_slug: str,
        csv_path: Path,
        dataset_name: str,
        description: str,
        year: int | None,
        index_columns: list[str] | None = None,
    ) -> Dataset:
        """Load a CSV file and store dataset metadata and records."""
        dataset = self.ensure_dataset(
            category_slug, dataset_slug, dataset_name, description, year,
        )
        raw_rows = self._read_csv_rows(csv_path)
        inferred_columns = infer_columns(raw_rows, index_columns)
        self.upsert_columns(dataset, inferred_columns)

        for row in raw_rows:
            self.add_record(
                dataset,
                row_json=row,
                index_cols=extract_index_cols(row, inferred_columns),
            )

        self.add_file(dataset, str(csv_path))
        return dataset

    def _read_csv_rows(self, csv_path: Path) -> list[dict[str, object]]:
        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows: list[dict[str, object]] = []
            for row in reader:
                parsed_row = {key: parse_value(value) for key, value in row.items()}
                rows.append(parsed_row)
            return rows

    def get_dataset_metadata(self, dataset_id: int) -> dict[str, Any]:
        """Return metadata (slug/name/description/year/columns) for a dataset."""
        dataset = self.session.get(Dataset, dataset_id)
        if not dataset:
            msg = f"Dataset {dataset_id} not found"
            raise ValueError(msg)

        columns = [
            {
                "name": col.name,
                "data_type": col.data_type,
                "description": col.description,
                "is_index": col.is_index,
            }
            for col in self.session.execute(
                select(DatasetColumn).where(DatasetColumn.dataset_id == dataset_id),
            ).scalars()
        ]
        return {
            "id": dataset.id,
            "slug": dataset.slug,
            "name": dataset.name,
            "description": dataset.description,
            "year": dataset.year,
            "columns": columns,
        }

    def list_datasets(self) -> list[dict[str, Any]]:
        """List datasets with their column metadata."""
        datasets = self.session.execute(select(Dataset)).scalars().all()
        return [self.get_dataset_metadata(dataset.id) for dataset in datasets]

    def get_datasets_metadata(self, datasets: list[Dataset]) -> list[dict[str, Any]]:
        """Return metadata for a list of dataset entities."""
        return [self.get_dataset_metadata(dataset.id) for dataset in datasets]

    def get_records(self, dataset_id: int) -> list[dict[str, Any]]:
        """Fetch all stored records for a dataset as dictionaries."""
        return [
            row_json
            for (row_json,) in self.session.execute(
                select(DatasetRecord.row_json).where(
                    DatasetRecord.dataset_id == dataset_id,
                ),
            )
        ]

    def record_analysis(
        self,
        dataset_id: int,
        question: str,
        query_spec: dict[str, Any],
        result_summary: dict[str, Any],
        provider: str | None,
        model: str | None,
    ) -> AnalysisQuery:
        """Persist an analysis query and return the stored record."""
        analysis = AnalysisQuery(
            dataset_id=dataset_id,
            question=question,
            query_spec=query_spec,
            result_summary=result_summary,
            provider=provider,
            model=model,
        )
        self.session.add(analysis)
        self.session.commit()
        return analysis


def parse_value(value: str | None) -> Any:
    """Convert CSV cell strings to typed Python values."""
    if value is None:
        return None
    stripped = value.strip()
    if stripped == "":
        return None
    if re.fullmatch(r"-?\d+", stripped):
        return int(stripped)
    if re.fullmatch(r"-?\d+\.\d+", stripped):
        return float(stripped)
    return stripped


def infer_columns(
    rows: Iterable[dict[str, object]], index_columns: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Infer column metadata (name/type/is_index) from the first batch of rows."""
    rows_list = list(rows)
    if not rows_list:
        return []

    keys = rows_list[0].keys()
    column_types: dict[str, Counter[str]] = {key: Counter() for key in keys}

    for row in rows_list:
        for key, value in row.items():
            if isinstance(value, (int, float)):
                column_types[key]["number"] += 1
            elif value is None:
                column_types[key]["null"] += 1
            else:
                column_types[key]["text"] += 1

    inferred: list[dict[str, Any]] = []
    for key in keys:
        counts = column_types[key]
        data_type = "text"
        if counts["number"] and counts["text"] == 0:
            data_type = "number"
        is_index = index_columns is not None and key in index_columns
        if index_columns is None:
            is_index = bool(
                re.search(r"year|年度|month|code|コード", key, re.IGNORECASE),
            )
        inferred.append(
            {
                "name": key,
                "data_type": data_type,
                "description": None,
                "is_index": is_index,
            },
        )
    return inferred


def extract_index_cols(
    row: dict[str, object], inferred_columns: list[dict[str, Any]],
) -> dict[str, object]:
    """Extract index column values from a row using inferred metadata."""
    index_values: dict[str, object] = {}
    for column in inferred_columns:
        if column.get("is_index"):
            value = row.get(column["name"])
            if value is not None:
                index_values[column["name"]] = value
    return index_values


def init_database(session: Session) -> None:
    """Create tables and seed categories."""
    bind = session.get_bind()
    init_db(bind)
    repo = DatasetRepository(session)
    repo.seed_categories()
