from pathlib import Path

from src.loader import list_sheets, load_spreadsheet

FIX = Path(__file__).parent / "fixtures"


def test_merged_cells_produce_warning():
    result = load_spreadsheet(FIX / "file_merged.xlsx")
    assert any("Merged" in w for w in result.warnings), (
        f"Expected a merged-cell warning, got: {result.warnings}"
    )


def test_multisheet_defaults_to_first_sheet():
    result = load_spreadsheet(FIX / "file_multisheet.xlsx")
    assert result.sheet == "Sheet1"
    assert result.df.shape == (2, 3)


def test_multisheet_select_by_name():
    result = load_spreadsheet(FIX / "file_multisheet.xlsx", sheet="Sheet2")
    assert result.sheet == "Sheet2"
    assert result.df.iloc[0]["Value"] == 999


def test_list_sheets():
    sheets = list_sheets(FIX / "file_multisheet.xlsx")
    assert sheets == ["Sheet1", "Sheet2"]


def test_bad_sheet_name_raises():
    import pytest
    with pytest.raises(ValueError, match="not found"):
        load_spreadsheet(FIX / "file_multisheet.xlsx", sheet="DoesNotExist")
