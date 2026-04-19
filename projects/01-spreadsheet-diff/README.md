# Project 01 — Spreadsheet Diff

A small, modular Python tool for comparing two spreadsheets (CSV or XLSX) and producing a clear diff report.

## The Problem

A common QA workflow in data teams: two people independently transform a raw data extract into a required format, then check each other's work before the data is released.

In practice, that "check" usually ends up as a manually-built Excel template with hand-written `IF(A1=B1, TRUE, FALSE)` formulas and conditional formatting to highlight mismatches in red — recreated from scratch every time, for every new report. It's slow, easy to get wrong, hard to audit, and nobody wants to maintain it.

This tool replaces that ad-hoc template with a single repeatable command that produces a consistent, readable diff report — so the QA check itself stops being a source of error.

## What It Does

Given two spreadsheets, it reports on:

- **Shape** — row and column counts, and which file is longer/wider
- **Headers** — whether column names and order match; which columns are unique to each file
- **Rows** — when a key column is provided, which rows only exist in one file (order-independent)
- **Cell-by-cell values** — exact locations and values of any differences
- **Type mismatches** — flagged separately (e.g. `"100"` vs `100`, strings vs dates)
- **Warnings** — merged cells and other structural oddities

## Assumptions & Scope

**In scope:**
- CSV vs CSV, or XLSX vs XLSX (symmetric inputs)
- XLSX with multiple sheets — user specifies the sheet
- Leading empty rows and columns are auto-stripped
- Rows in different orders, matched by a user-supplied key column
- Merged cells detected and reported as warnings

**Out of scope (may come later):**
- Auto-reformatting files to match
- Comparing files of different types (CSV vs XLSX)
- Comparing formulas (only rendered values are compared)
- GUI or web interface

## Architecture

```
projects/01-spreadsheet-diff/
├── src/
│   ├── loader.py       # Reads CSV/XLSX into a normalized DataFrame
│   ├── comparator.py   # Runs shape/header/row/cell checks
│   ├── reporter.py     # Renders results as markdown or console output
│   └── cli.py          # Command-line entry point
├── tests/
│   ├── fixtures/       # Sample CSVs for matching / mismatching cases
│   ├── test_loader.py
│   └── test_comparator.py
├── examples/
│   └── run_example.sh  # End-to-end demo on the sample fixtures
└── requirements.txt
```

Each module does one thing; any one of them can be swapped out (e.g. a new HTML reporter, or a new loader for another format) without touching the others.

## Install

```bash
pip install -r requirements.txt
```

## Usage

From inside `projects/01-spreadsheet-diff/`:

```bash
# Quick console summary
python -m src.cli tests/fixtures/file_a.csv tests/fixtures/file_b.csv --key ID

# Write a full markdown report
python -m src.cli tests/fixtures/file_a.csv tests/fixtures/file_b.csv --key ID --out report.md

# List sheet names in an XLSX before choosing one
python -m src.cli path/to/file.xlsx path/to/file.xlsx --list-sheets
```

### Options

| Flag | Description |
|------|-------------|
| `--sheet` | Sheet name for XLSX inputs (defaults to the first sheet) |
| `--key` | Column name used for order-independent row matching |
| `--header-row` | 0-based index of the header row |
| `--out` | Path to write a markdown report |
| `--list-sheets` | List sheet names in `file_a` and exit |

The CLI exits with status `0` if the files match and `1` if any differences are found — so it can be dropped into a QA pipeline or CI job.

## Testing

The tool ships with a small but meaningful test suite in `tests/`:

- `test_loader.py` — covers CSV loading, missing files, and unsupported file types
- `test_comparator.py` — covers identical files, positional comparison, and key-based order-independent comparison

Sample fixtures in `tests/fixtures/` include both a matching pair and a deliberately mismatching pair, so the comparator is exercised against real differences (a changed value, a changed currency, rows only in one file).

Run the suite with:

```bash
pip install pytest
pytest
```

Every change to the loader or comparator should keep these tests green.

## Why This Design

- **Modular** — `loader → comparator → reporter → cli` is a pipeline; each stage has a single responsibility.
- **Typed dataclasses** (`LoadResult`, `DiffResult`, `CellDiff`) make the interfaces between stages explicit and easy to test.
- **Pure-function comparator** — no I/O, so it's trivial to unit test.
- **Exit codes for automation** — the tool is useful both for a human reading the markdown and for a script in CI.
