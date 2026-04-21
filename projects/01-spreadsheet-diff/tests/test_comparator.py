from pathlib import Path

import pandas as pd
import pytest

from src.comparator import compare
from src.loader import load_spreadsheet

FIX = Path(__file__).parent / "fixtures"


def test_identical_files_match():
    a = load_spreadsheet(FIX / "file_a_match.csv").df
    b = load_spreadsheet(FIX / "file_b_match.csv").df
    result = compare(a, b)
    assert result.is_match
    assert result.headers_match
    assert result.cell_diffs == []


def test_positional_comparison_detects_differences():
    a = load_spreadsheet(FIX / "file_a.csv").df
    b = load_spreadsheet(FIX / "file_b.csv").df
    result = compare(a, b)
    assert not result.is_match
    assert result.cell_diffs, "Expected cell diffs from out-of-order rows"


def test_key_column_ignores_row_order():
    a = load_spreadsheet(FIX / "file_a.csv").df
    b = load_spreadsheet(FIX / "file_b.csv").df
    result = compare(a, b, key_column="ID")

    # ID 4 only in A, ID 5 only in B
    assert len(result.rows_only_in_a) == 1
    assert len(result.rows_only_in_b) == 1
    assert result.rows_only_in_a[0]["ID"] == 4
    assert result.rows_only_in_b[0]["ID"] == 5

    # ID 1 Amount differs (100 vs 150), ID 3 Currency differs (GBP vs USD)
    value_diffs = [d for d in result.cell_diffs if d.kind == "value"]
    diff_cols = {(d.column, d.value_a, d.value_b) for d in value_diffs}
    assert ("Amount", 100, 150) in diff_cols
    assert ("Currency", "GBP", "USD") in diff_cols


def test_nan_cells_treated_as_equal():
    """NaN == NaN must not be flagged as a difference.

    pandas default comparison treats NaN as not-equal-to-NaN, which would
    produce false positives on every empty cell. This regression test locks
    in the correct behaviour: matching NaN cells are ignored.
    """
    a = load_spreadsheet(FIX / "file_nan_a.csv").df
    b = load_spreadsheet(FIX / "file_nan_b.csv").df
    result = compare(a, b, key_column="ID")
    assert result.is_match, f"Expected match but got diffs: {result.cell_diffs}"


def test_key_column_missing_raises():
    a = load_spreadsheet(FIX / "file_a.csv").df
    b = load_spreadsheet(FIX / "file_b.csv").df
    with pytest.raises(ValueError, match="Key column"):
        compare(a, b, key_column="NonExistent")


def test_normalize_types_removes_diffs():
    """Strings that represent the same number should not diff when normalised.

    Without normalisation, '100' != 100 (value diff). With normalisation both
    columns are coerced to numeric so the comparison finds no differences.
    """
    a = pd.DataFrame({"ID": [1, 2], "Amount": ["100", "200"]})
    b = pd.DataFrame({"ID": [1, 2], "Amount": [100, 200]})

    result_raw = compare(a, b)
    assert result_raw.cell_diffs, "Expected diffs before normalisation"

    result_norm = compare(a, b, normalize_types=True)
    assert result_norm.is_match, f"Expected match after normalisation, got: {result_norm.cell_diffs}"
