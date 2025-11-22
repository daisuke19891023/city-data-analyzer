"""CLI script to ingest CSV files into the city-data backend."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from clean_interfaces.database import configure_engine, session_scope
from clean_interfaces.services.datasets import DatasetRepository, init_database


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Return parsed CLI arguments for CSV ingestion."""
    parser = argparse.ArgumentParser(
        description="Load a CSV file into the datasets tables.",
    )
    parser.add_argument("category_slug", help="Category slug (e.g., population)")
    parser.add_argument(
        "dataset_slug", help="Dataset slug (e.g., population_by_ward_2023)",
    )
    parser.add_argument("csv_path", type=Path, help="Path to the CSV file")
    parser.add_argument("dataset_name", help="Human-friendly dataset name")
    parser.add_argument("description", help="Dataset description")
    parser.add_argument("--year", type=int, default=None, help="Year for the dataset")
    parser.add_argument(
        "--index", nargs="*", default=None, help="Columns to treat as index columns",
    )
    parser.add_argument(
        "--database-url",
        dest="database_url",
        default=None,
        help="Override DATABASE_URL",
    )
    return parser.parse_args()


def main() -> None:
    """Entrypoint for loading a CSV file into the database."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")
    args = parse_args()
    if args.database_url:
        configure_engine(args.database_url)

    with session_scope() as session:
        init_database(session)
        repo = DatasetRepository(session)
        dataset = repo.import_csv(
            category_slug=args.category_slug,
            dataset_slug=args.dataset_slug,
            csv_path=args.csv_path,
            dataset_name=args.dataset_name,
            description=args.description,
            year=args.year,
            index_columns=args.index,
        )
        row_count = len(repo.get_records(dataset.id))
        logger.info(
            "Imported dataset %s (id=%s) with %s rows",
            dataset.slug,
            dataset.id,
            row_count,
        )


if __name__ == "__main__":
    main()
