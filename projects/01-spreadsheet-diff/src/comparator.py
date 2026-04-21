"""Compare two loaded DataFrames and produce a structured diff result.

Checks performed:
- Shape (row/column counts)
- Headers (names + order)
- Row membership (when a key column is provided)
- Cell-by-cell value differences
- Type mismatches (flagged separately from value differences)
- Optional type normalisation (coerce string numbers to numeric before comparing)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class CellDiff:
    row: int
    column: str
    value_a: object
    value_b: object
    kind: str  # "value" or "type"


@dataclass
class DiffResult:
    shape_a: tuple[int, int]
    shape_b: tuple[int, int]
    headers_match: bool
    headers_a: list[str]
    headers_b: list[str]
    header_only_in_a: list[str] = field(default_factory=list)
    header_only_in_b: list[str] = field(default_factory=list)
    rows_only_in_a: list[dict] = field(default_factory=list)
    rows_only_in_b: list[dict] = field(default_factory=list)
    cell_diffs: list[CellDiff] = field(default_factory=list)
    key_column: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def is_match(self) -> bool:
        return (
            self.shape_a == self.shape_b
            and self.headers_match
            and not self.rows_only_in_a
            and not self.rows_only_in_b
            and not self.cell_diffs
        )


def _compare_headers(a: pd.DataFrame, b: pd.DataFrame) -> tuple[bool, list[str], list[str]]:
    headers_a = list(a.columns)
    headers_b = list(b.columns)
    match = headers_a == headers_b
    only_in_a = [h for h in headers_a if h not in headers_b]
    only_in_b = [h for h in headers_b if h not in headers_a]
    return match, only_in_a, only_in_b


def _cell_equal(v_a, v_b) -> bool:
    """Treat NaN == NaN as equal (pandas default is not)."""
    if pd.isna(v_a) and pd.isna(v_b):
        return True
    return v_a == v_b


def _types_equal(v_a, v_b) -> bool:
    if pd.isna(v_a) or pd.isna(v_b):
        return True
    return type(v_a) is type(v_b)


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce columns to numeric where all non-null values look like numbers."""
    df = df.copy()
    for col in df.columns:
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().sum() == df[col].notna().sum():
            df[col] = converted
    return df


def _compare_aligned(
    a: pd.DataFrame, b: pd.DataFrame, shared_cols: list[str]
) -> list[CellDiff]:
    """Row-by-row, column-by-column comparison on aligned DataFrames."""
    diffs: list[CellDiff] = []
    n = min(len(a), len(b))
    for i in range(n):
        for col in shared_cols:
            v_a = a.iloc[i][col]
            v_b = b.iloc[i][col]
            if not _cell_equal(v_a, v_b):
                diffs.append(CellDiff(i, col, v_a, v_b, "value"))
            elif not _types_equal(v_a, v_b):
                diffs.append(CellDiff(i, col, v_a, v_b, "type"))
    return diffs


def _split_by_key(
    a: pd.DataFrame, b: pd.DataFrame, key: str
) -> tuple[list[dict], list[dict], pd.DataFrame, pd.DataFrame]:
    """Return (rows_only_in_a, rows_only_in_b, aligned_a, aligned_b) using a key column."""
    keys_a = set(a[key])
    keys_b = set(b[key])
    only_a_keys = keys_a - keys_b
    only_b_keys = keys_b - keys_a
    shared_keys = keys_a & keys_b

    rows_only_in_a = a[a[key].isin(only_a_keys)].to_dict(orient="records")
    rows_only_in_b = b[b[key].isin(only_b_keys)].to_dict(orient="records")

    aligned_a = (
        a[a[key].isin(shared_keys)].sort_values(key).reset_index(drop=True)
    )
    aligned_b = (
        b[b[key].isin(shared_keys)].sort_values(key).reset_index(drop=True)
    )
    return rows_only_in_a, rows_only_in_b, aligned_a, aligned_b


def compare(
    a: pd.DataFrame,
    b: pd.DataFrame,
    key_column: str | None = None,
    normalize_types: bool = False,
) -> DiffResult:
    """Compare two DataFrames and return a structured DiffResult.

    Args:
        a: First DataFrame ("File A").
        b: Second DataFrame ("File B").
        key_column: If provided, rows are matched by this column so that
            order-independent comparison is possible. If None, rows are
            compared positionally.
        normalize_types: If True, columns that look like numbers are coerced
            to numeric before comparison, so '100' and 100 are treated equal.
    """
    warnings: list[str] = []
    if normalize_types:
        a = _normalize(a)
        b = _normalize(b)
    headers_match, only_in_a, only_in_b = _compare_headers(a, b)
    shared_cols = [c for c in a.columns if c in b.columns]

    rows_only_in_a: list[dict] = []
    rows_only_in_b: list[dict] = []

    if key_column:
        if key_column not in a.columns or key_column not in b.columns:
            raise ValueError(
                f"Key column '{key_column}' must exist in both files."
            )
        rows_only_in_a, rows_only_in_b, aligned_a, aligned_b = _split_by_key(
            a, b, key_column
        )
        cell_diffs = _compare_aligned(aligned_a, aligned_b, shared_cols)
    else:
        if len(a) != len(b):
            warnings.append(
                "Row counts differ and no key_column given; "
                "cell-by-cell comparison covers only overlapping rows."
            )
        cell_diffs = _compare_aligned(a, b, shared_cols)

    return DiffResult(
        shape_a=a.shape,
        shape_b=b.shape,
        headers_match=headers_match,
        headers_a=list(a.columns),
        headers_b=list(b.columns),
        header_only_in_a=only_in_a,
        header_only_in_b=only_in_b,
        rows_only_in_a=rows_only_in_a,
        rows_only_in_b=rows_only_in_b,
        cell_diffs=cell_diffs,
        key_column=key_column,
        warnings=warnings,
    )
