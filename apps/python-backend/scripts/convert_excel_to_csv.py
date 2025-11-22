"""CLI utility to convert an Excel sheet into a CSV file for ingestion."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

import pandas as pd

logger = logging.getLogger(__name__)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Return parsed CLI arguments for Excel to CSV conversion.

    Parameters
    ----------
    argv:
        Optional arguments to parse. When omitted, defaults to ``sys.argv``.

    """
    parser = argparse.ArgumentParser(
        description=(
            "Convert an Excel worksheet into a CSV file."
            " Use this to prepare open data for load_csv.py."
        ),
    )
    parser.add_argument("excel_path", type=Path, help="Path to the Excel file")
    parser.add_argument(
        "output_csv",
        type=Path,
        nargs="?",
        help="Optional output CSV path (defaults to <excel_path>.csv)",
    )
    parser.add_argument(
        "--sheet",
        dest="sheet_name",
        help="Worksheet name to read (defaults to the first sheet)",
    )
    parser.add_argument(
        "--sheet-index",
        dest="sheet_index",
        type=int,
        help="Zero-based worksheet index when the name is unknown",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main() -> None:
    """Convert the requested sheet to CSV and report the result."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")
    args = parse_args()

    if args.sheet_name is not None:
        sheet_to_read: str | int = args.sheet_name
    elif args.sheet_index is not None:
        sheet_to_read = args.sheet_index
    else:
        sheet_to_read = 0

    output_csv = args.output_csv or args.excel_path.with_suffix(".csv")

    dataframe = pd.read_excel(args.excel_path, sheet_name=sheet_to_read)
    dataframe.to_csv(output_csv, index=False)

    logger.info(
        "Saved %s rows from sheet %s to %s",
        len(dataframe),
        sheet_to_read,
        output_csv,
    )


if __name__ == "__main__":
    main()
