"""Format a DiffResult into a human-readable report (markdown or console text)."""

from __future__ import annotations

from .comparator import DiffResult


def _fmt_shape(shape: tuple[int, int]) -> str:
    return f"{shape[0]} rows x {shape[1]} columns"


def render_markdown(
    result: DiffResult,
    source_a: str,
    source_b: str,
    loader_warnings: list[str] | None = None,
) -> str:
    """Render a DiffResult as a markdown report."""
    lines: list[str] = []
    lines.append("# Spreadsheet Diff Report")
    lines.append("")
    lines.append(f"- **File A:** `{source_a}`")
    lines.append(f"- **File B:** `{source_b}`")
    if result.key_column:
        lines.append(f"- **Key column:** `{result.key_column}`")
    lines.append("")

    status = "MATCH" if result.is_match else "DIFFERENCES FOUND"
    lines.append(f"## Result: {status}")
    lines.append("")

    # Shape
    lines.append("## Shape")
    lines.append(f"- File A: {_fmt_shape(result.shape_a)}")
    lines.append(f"- File B: {_fmt_shape(result.shape_b)}")
    if result.shape_a != result.shape_b:
        which = "A" if result.shape_a[0] > result.shape_b[0] else "B"
        lines.append(f"- Row counts differ; File {which} has more rows.")
    lines.append("")

    # Headers
    lines.append("## Headers")
    if result.headers_match:
        lines.append("- Headers match (same names, same order).")
    else:
        lines.append("- Headers do NOT match.")
        if result.header_only_in_a:
            lines.append(f"- Only in A: {result.header_only_in_a}")
        if result.header_only_in_b:
            lines.append(f"- Only in B: {result.header_only_in_b}")
    lines.append("")

    # Row membership (key-based)
    if result.key_column:
        lines.append("## Row Membership")
        lines.append(f"- Rows only in A: {len(result.rows_only_in_a)}")
        lines.append(f"- Rows only in B: {len(result.rows_only_in_b)}")
        if result.rows_only_in_a:
            lines.append("")
            lines.append("### First rows only in A")
            for row in result.rows_only_in_a[:5]:
                lines.append(f"- {row}")
        if result.rows_only_in_b:
            lines.append("")
            lines.append("### First rows only in B")
            for row in result.rows_only_in_b[:5]:
                lines.append(f"- {row}")
        lines.append("")

    # Cell differences
    lines.append("## Cell Differences")
    value_diffs = [d for d in result.cell_diffs if d.kind == "value"]
    type_diffs = [d for d in result.cell_diffs if d.kind == "type"]
    lines.append(f"- Value mismatches: {len(value_diffs)}")
    lines.append(f"- Type mismatches: {len(type_diffs)}")

    if value_diffs:
        lines.append("")
        lines.append("### Value mismatches (first 20)")
        lines.append("| Row | Column | File A | File B |")
        lines.append("|---|---|---|---|")
        for d in value_diffs[:20]:
            lines.append(f"| {d.row} | {d.column} | {d.value_a!r} | {d.value_b!r} |")

    if type_diffs:
        lines.append("")
        lines.append("### Type mismatches (first 20)")
        lines.append("| Row | Column | File A (type) | File B (type) |")
        lines.append("|---|---|---|---|")
        for d in type_diffs[:20]:
            lines.append(
                f"| {d.row} | {d.column} | "
                f"{d.value_a!r} ({type(d.value_a).__name__}) | "
                f"{d.value_b!r} ({type(d.value_b).__name__}) |"
            )

    # Warnings
    all_warnings = list(loader_warnings or []) + list(result.warnings)
    if all_warnings:
        lines.append("")
        lines.append("## Warnings")
        for w in all_warnings:
            lines.append(f"- {w}")

    lines.append("")
    return "\n".join(lines)


def render_console(
    result: DiffResult,
    source_a: str,
    source_b: str,
    loader_warnings: list[str] | None = None,
) -> str:
    """A compact console-friendly summary."""
    status = "MATCH" if result.is_match else "DIFFERENCES FOUND"
    lines = [
        f"Spreadsheet Diff: {status}",
        f"  A: {source_a}  {_fmt_shape(result.shape_a)}",
        f"  B: {source_b}  {_fmt_shape(result.shape_b)}",
        f"  Headers match: {result.headers_match}",
    ]
    if result.key_column:
        lines.append(
            f"  Rows only in A: {len(result.rows_only_in_a)}  "
            f"only in B: {len(result.rows_only_in_b)}"
        )
    value_diffs = sum(1 for d in result.cell_diffs if d.kind == "value")
    type_diffs = sum(1 for d in result.cell_diffs if d.kind == "type")
    lines.append(f"  Value mismatches: {value_diffs}")
    lines.append(f"  Type mismatches:  {type_diffs}")
    for w in (loader_warnings or []) + list(result.warnings):
        lines.append(f"  ! {w}")
    return "\n".join(lines)
