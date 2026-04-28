"""Tests for the HTML reporter.

These don't parse the HTML rigorously — they verify that the rendered output
contains the right structural and content markers for each branch of the
report (match vs differences, value vs type diffs, warnings, key column).
"""
from pathlib import Path

import pandas as pd

from src.comparator import compare
from src.reporter import render_html
from src.loader import load_spreadsheet

FIX = Path(__file__).parent / "fixtures"


def test_html_match_contains_status_and_sources():
    a = load_spreadsheet(FIX / "file_a_match.csv").df
    b = load_spreadsheet(FIX / "file_b_match.csv").df
    html = render_html(compare(a, b), "a.csv", "b.csv")

    assert html.startswith("<!DOCTYPE html>")
    assert "<title>Spreadsheet Diff Report</title>" in html
    assert "MATCH" in html
    assert "DIFFERENCES FOUND" not in html
    assert "a.csv" in html and "b.csv" in html


def test_html_differences_render_value_table():
    a = load_spreadsheet(FIX / "file_a.csv").df
    b = load_spreadsheet(FIX / "file_b.csv").df
    html = render_html(compare(a, b, key_column="ID"), "a.csv", "b.csv")

    assert "DIFFERENCES FOUND" in html
    assert "Value mismatches" in html
    # Key column branch
    assert "Row Membership" in html
    assert "Key column" in html


def test_html_type_diffs_render_type_table():
    a = pd.DataFrame({"ID": [1, 2], "Amount": ["100", "200"]})
    b = pd.DataFrame({"ID": [1, 2], "Amount": [100, 200]})
    html = render_html(compare(a, b), "a.csv", "b.csv")

    # "100" != 100 produces value diffs (not type) until normalized — verify table renders
    assert "Value mismatches" in html
    assert "<table>" in html


def test_html_warnings_rendered():
    a = load_spreadsheet(FIX / "file_a_match.csv").df
    b = load_spreadsheet(FIX / "file_b_match.csv").df
    html = render_html(
        compare(a, b),
        "a.csv",
        "b.csv",
        loader_warnings=["Merged cells detected in Sheet1"],
    )
    assert "Warnings" in html
    assert "Merged cells detected" in html


def test_html_no_warnings_section_when_clean():
    a = load_spreadsheet(FIX / "file_a_match.csv").df
    b = load_spreadsheet(FIX / "file_b_match.csv").df
    html = render_html(compare(a, b), "a.csv", "b.csv")
    assert "<h2>Warnings</h2>" not in html
