from pathlib import Path

import pytest

from src.loader import load_spreadsheet

FIX = Path(__file__).parent / "fixtures"


def test_load_csv_basic():
    result = load_spreadsheet(FIX / "file_a.csv")
    assert result.df.shape == (4, 4)
    assert list(result.df.columns) == ["ID", "Name", "Amount", "Currency"]
    assert result.sheet is None
    assert result.warnings == []


def test_load_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_spreadsheet(FIX / "does_not_exist.csv")


def test_unsupported_extension_raises(tmp_path):
    bad = tmp_path / "data.txt"
    bad.write_text("hello")
    with pytest.raises(ValueError):
        load_spreadsheet(bad)
