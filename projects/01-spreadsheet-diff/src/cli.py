"""Command-line entry point for the spreadsheet diff tool.

Example:
    python -m src.cli file_a.xlsx file_b.xlsx --sheet Sheet1 --key ID --out report.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .comparator import compare
from .loader import list_sheets, load_spreadsheet
from .reporter import render_console, render_markdown


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="spreadsheet-diff",
        description="Compare two spreadsheets and produce a diff report.",
    )
    p.add_argument("file_a", help="First spreadsheet (CSV or XLSX)")
    p.add_argument("file_b", help="Second spreadsheet (CSV or XLSX)")
    p.add_argument(
        "--sheet",
        default=None,
        help="Sheet name for XLSX inputs (defaults to the first sheet).",
    )
    p.add_argument(
        "--key",
        default=None,
        help="Key column for order-independent row matching.",
    )
    p.add_argument(
        "--header-row",
        type=int,
        default=None,
        help="0-based index of the header row (default: 0).",
    )
    p.add_argument(
        "--out",
        default=None,
        help="Write a markdown report to this path (default: console only).",
    )
    p.add_argument(
        "--list-sheets",
        action="store_true",
        help="List sheet names in file_a and exit.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list_sheets:
        sheets = list_sheets(args.file_a)
        if not sheets:
            print("No sheets (CSV or unsupported file).")
        else:
            print("\n".join(sheets))
        return 0

    a = load_spreadsheet(args.file_a, sheet=args.sheet, header_row=args.header_row)
    b = load_spreadsheet(args.file_b, sheet=args.sheet, header_row=args.header_row)

    result = compare(a.df, b.df, key_column=args.key)

    loader_warnings = a.warnings + b.warnings
    print(render_console(result, a.source, b.source, loader_warnings))

    if args.out:
        md = render_markdown(result, a.source, b.source, loader_warnings)
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"\nMarkdown report written to {args.out}")

    return 0 if result.is_match else 1


if __name__ == "__main__":
    sys.exit(main())
