from __future__ import annotations

import argparse
from typing import Any, TYPE_CHECKING

import pandas as pd

from scripts import convert_excel_to_csv

if TYPE_CHECKING:
    from pathlib import Path


def test_parse_args_defaults(tmp_path: Path) -> None:
    """Verify defaults when only excel path is provided."""
    excel_path = tmp_path / "data.xlsx"
    args = convert_excel_to_csv.parse_args([str(excel_path)])

    assert args.excel_path == excel_path
    assert args.output_csv is None
    assert args.sheet_name is None
    assert args.sheet_index is None


def test_main_reads_specified_sheet_and_writes_csv(
    monkeypatch: Any, tmp_path: Path,
) -> None:
    """Ensure main() reads a chosen sheet and writes a CSV output."""
    excel_path = tmp_path / "input.xlsx"
    output_csv = tmp_path / "out.csv"
    called: dict[str, Any] = {}

    def fake_read_excel(path: Path, sheet_name: str | int) -> pd.DataFrame:
        called["path"] = path
        called["sheet_name"] = sheet_name
        return pd.DataFrame({"col": [1, 2]})

    monkeypatch.setattr(convert_excel_to_csv.pd, "read_excel", fake_read_excel)

    def fake_parse_args() -> argparse.Namespace:
        return argparse.Namespace(
            excel_path=excel_path,
            output_csv=output_csv,
            sheet_name=None,
            sheet_index=2,
        )

    monkeypatch.setattr(convert_excel_to_csv, "parse_args", fake_parse_args)

    convert_excel_to_csv.main()

    assert called == {"path": excel_path, "sheet_name": 2}
    assert output_csv.exists()
    assert "col" in output_csv.read_text(encoding="utf-8")
