"""Load spreadsheet files (CSV or XLSX) into a normalized pandas DataFrame.

Handles:
- CSV and XLSX inputs
- Multi-sheet XLSX (user picks the sheet)
- Leading empty rows and columns (auto-stripped)
- Merged cells in XLSX (detected and reported as warnings)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


@dataclass
class LoadResult:
    """Container for a loaded spreadsheet plus any warnings raised during load."""

    df: pd.DataFrame
    source: str
    sheet: str | None = None
    warnings: list[str] = field(default_factory=list)


def _strip_empty_edges(df: pd.DataFrame) -> pd.DataFrame:
    """Remove fully-empty leading/trailing rows and columns."""
    df = df.dropna(how="all", axis=0).dropna(how="all", axis=1)
    df = df.reset_index(drop=True)
    return df


def _detect_merged_cells(path: Path, sheet: str | None) -> list[str]:
    """Return a list of warning strings for any merged cell ranges found."""
    try:
        from openpyxl import load_workbook
    except ImportError:
        return []

    wb = load_workbook(path, read_only=False, data_only=True)
    ws = wb[sheet] if sheet else wb.active
    warnings = []
    for merged_range in ws.merged_cells.ranges:
        warnings.append(f"Merged cells detected at {merged_range} in sheet '{ws.title}'")
    wb.close()
    return warnings


def list_sheets(path: str | Path) -> list[str]:
    """Return all sheet names in an XLSX file (empty list for CSV)."""
    path = Path(path)
    if path.suffix.lower() not in {".xlsx", ".xlsm"}:
        return []
    return pd.ExcelFile(path).sheet_names


def load_spreadsheet(
    path: str | Path,
    sheet: str | None = None,
    header_row: int | None = None,
) -> LoadResult:
    """Load a spreadsheet into a normalized DataFrame.

    Args:
        path: Path to a CSV or XLSX file.
        sheet: Sheet name for XLSX files. Defaults to the first sheet.
        header_row: Explicit header row index (0-based). If None, pandas auto-detects.

    Returns:
        LoadResult with the DataFrame, source info, and any warnings.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()
    warnings: list[str] = []

    if suffix == ".csv":
        df = pd.read_csv(path, header=header_row if header_row is not None else 0)
        sheet_used = None
    elif suffix in {".xlsx", ".xlsm"}:
        sheets = list_sheets(path)
        if not sheets:
            raise ValueError(f"No sheets found in {path}")
        sheet_used = sheet or sheets[0]
        if sheet_used not in sheets:
            raise ValueError(
                f"Sheet '{sheet_used}' not found in {path}. Available: {sheets}"
            )
        df = pd.read_excel(
            path,
            sheet_name=sheet_used,
            header=header_row if header_row is not None else 0,
        )
        warnings.extend(_detect_merged_cells(path, sheet_used))
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Use .csv or .xlsx.")

    df = _strip_empty_edges(df)

    return LoadResult(
        df=df,
        source=str(path),
        sheet=sheet_used,
        warnings=warnings,
    )
