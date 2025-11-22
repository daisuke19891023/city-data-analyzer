"""SQLAlchemy ORM models for the city data backend."""

from __future__ import annotations

from datetime import datetime

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
        DateTime, default=datetime.utcnow, nullable=False,
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
    row_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    index_cols: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    row_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False,
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
    query_spec: Mapped[dict] = mapped_column(JSON, nullable=False)
    result_summary: Mapped[dict] = mapped_column(JSON, nullable=False)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False,
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
        DateTime, default=datetime.utcnow, nullable=False,
    )

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="files")
