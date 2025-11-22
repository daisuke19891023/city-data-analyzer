"""SQLAlchemy ORM models for the city data backend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from clean_interfaces.database import Base


class OpenDataCategory(Base):
    """Open data categories (pre-seeded for Kawasaki city datasets)."""

    __tablename__ = "open_data_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    datasets: Mapped[list[Dataset]] = relationship("Dataset", back_populates="category")


class Dataset(Base):
    """Dataset metadata for each CSV import."""

    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("open_data_categories.id"), nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False,
    )

    category: Mapped[OpenDataCategory] = relationship(
        "OpenDataCategory", back_populates="datasets",
    )
    columns: Mapped[list[DatasetColumn]] = relationship(
        "DatasetColumn", back_populates="dataset", cascade="all, delete-orphan",
    )
    records: Mapped[list[DatasetRecord]] = relationship(
        "DatasetRecord", back_populates="dataset", cascade="all, delete-orphan",
    )
    analyses: Mapped[list[AnalysisQuery]] = relationship(
        "AnalysisQuery", back_populates="dataset", cascade="all, delete-orphan",
    )
    files: Mapped[list[DatasetFile]] = relationship(
        "DatasetFile", back_populates="dataset", cascade="all, delete-orphan",
    )


class DatasetColumn(Base):
    """Column metadata for each dataset."""

    __tablename__ = "dataset_columns"
    __table_args__ = (
        UniqueConstraint("dataset_id", "name", name="uq_dataset_column_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[str] = mapped_column(String(50), nullable=False, default="text")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_index: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="columns")


class DatasetRecord(Base):
    """Stored dataset rows (JSON payload + extracted index columns)."""

    __tablename__ = "dataset_records"
    __table_args__ = (
        UniqueConstraint("dataset_id", "row_hash", name="uq_dataset_row_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id"), nullable=False, index=True,
    )
    row_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    index_cols: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict,
    )
    row_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False,
    )

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="records")


class AnalysisQuery(Base):
    """History of interactive analysis requests."""

    __tablename__ = "analysis_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id"), nullable=False, index=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    query_spec: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    result_summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False,
    )

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="analyses")


class DatasetFile(Base):
    """Optional file metadata for imported datasets."""

    __tablename__ = "dataset_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id"), nullable=False, index=True,
    )
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False, default="csv")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False,
    )

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="files")


class Experiment(Base):
    """Experiment representing a batch exploration goal."""

    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    goal_description: Mapped[str] = mapped_column(Text, nullable=False)
    dataset_ids: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False,
    )

    jobs: Mapped[list[ExperimentJob]] = relationship(
        "ExperimentJob", back_populates="experiment", cascade="all, delete-orphan",
    )
    insights: Mapped[list[InsightCandidate]] = relationship(
        "InsightCandidate", back_populates="experiment", cascade="all, delete-orphan",
    )


class ExperimentJob(Base):
    """Job planned under an experiment."""

    __tablename__ = "experiment_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id"), nullable=False, index=True,
    )
    dataset_id: Mapped[int] = mapped_column(Integer, nullable=False)
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    query_spec: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    experiment: Mapped[Experiment] = relationship("Experiment", back_populates="jobs")
    insights: Mapped[list[InsightCandidate]] = relationship(
        "InsightCandidate", back_populates="job", cascade="all, delete-orphan",
    )


class InsightCandidate(Base):
    """Insight candidate generated from experiment jobs."""

    __tablename__ = "insight_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id"), nullable=False, index=True,
    )
    job_id: Mapped[int | None] = mapped_column(ForeignKey("experiment_jobs.id"))
    dataset_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    adopted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    feedback_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False,
    )

    experiment: Mapped[Experiment] = relationship(
        "Experiment", back_populates="insights",
    )
    job: Mapped[ExperimentJob | None] = relationship(
        "ExperimentJob", back_populates="insights",
    )
    feedback: Mapped[list[InsightFeedback]] = relationship(
        "InsightFeedback", back_populates="candidate", cascade="all, delete-orphan",
    )


class InsightFeedback(Base):
    """Feedback log for an insight candidate."""

    __tablename__ = "insight_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("insight_candidates.id"), nullable=False, index=True,
    )
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False,
    )

    candidate: Mapped[InsightCandidate] = relationship(
        "InsightCandidate", back_populates="feedback",
    )
