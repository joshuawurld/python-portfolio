"""Format a DiffResult into a human-readable report (markdown, HTML, or console text)."""

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


def render_html(
    result: DiffResult,
    source_a: str,
    source_b: str,
    loader_warnings: list[str] | None = None,
) -> str:
    """Render a DiffResult as a self-contained HTML report."""
    status = "MATCH" if result.is_match else "DIFFERENCES FOUND"
    status_colour = "#2e7d32" if result.is_match else "#c62828"
    all_warnings = list(loader_warnings or []) + list(result.warnings)
    value_diffs = [d for d in result.cell_diffs if d.kind == "value"]
    type_diffs = [d for d in result.cell_diffs if d.kind == "type"]

    def _rows(diffs, extra_col=False):
        rows = []
        for d in diffs[:50]:
            type_info = (
                f" <small>({type(d.value_a).__name__} vs {type(d.value_b).__name__})</small>"
                if extra_col else ""
            )
            rows.append(
                f"<tr><td>{d.row}</td><td>{d.column}</td>"
                f"<td class='val-a'>{d.value_a!r}</td>"
                f"<td class='val-b'>{d.value_b!r}{type_info}</td></tr>"
            )
        return "\n".join(rows)

    value_table = (
        f"<h3>Value mismatches (first 50)</h3>"
        f"<table><thead><tr><th>Row</th><th>Column</th>"
        f"<th>File A</th><th>File B</th></tr></thead>"
        f"<tbody>{_rows(value_diffs)}</tbody></table>"
        if value_diffs else ""
    )
    type_table = (
        f"<h3>Type mismatches (first 50)</h3>"
        f"<table><thead><tr><th>Row</th><th>Column</th>"
        f"<th>File A</th><th>File B</th></tr></thead>"
        f"<tbody>{_rows(type_diffs, extra_col=True)}</tbody></table>"
        if type_diffs else ""
    )
    warnings_html = (
        "<h2>Warnings</h2><ul>" + "".join(f"<li>{w}</li>" for w in all_warnings) + "</ul>"
        if all_warnings else ""
    )
    header_issues = ""
    if not result.headers_match:
        header_issues = (
            f"<p>Only in A: {result.header_only_in_a}</p>"
            f"<p>Only in B: {result.header_only_in_b}</p>"
        )
    row_membership = ""
    if result.key_column:
        row_membership = (
            f"<h2>Row Membership</h2>"
            f"<p>Rows only in A: <strong>{len(result.rows_only_in_a)}</strong> &nbsp;"
            f"Rows only in B: <strong>{len(result.rows_only_in_b)}</strong></p>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Spreadsheet Diff Report</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; color: #212121; }}
  h1 {{ border-bottom: 2px solid #eee; padding-bottom: .5rem; }}
  .status {{ font-size: 1.4rem; font-weight: bold; color: {status_colour}; margin: 1rem 0; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
  th {{ background: #f5f5f5; text-align: left; padding: .4rem .6rem; border: 1px solid #ddd; }}
  td {{ padding: .35rem .6rem; border: 1px solid #eee; font-size: .9rem; }}
  .val-a {{ background: #fff8e1; }}
  .val-b {{ background: #fce4ec; }}
  .meta {{ color: #555; font-size: .9rem; }}
  ul {{ padding-left: 1.5rem; }}
  li {{ margin: .3rem 0; color: #b71c1c; }}
</style>
</head>
<body>
<h1>Spreadsheet Diff Report</h1>
<p class="meta"><strong>File A:</strong> {source_a}</p>
<p class="meta"><strong>File B:</strong> {source_b}</p>
{"<p class='meta'><strong>Key column:</strong> " + result.key_column + "</p>" if result.key_column else ""}
<div class="status">{status}</div>

<h2>Shape</h2>
<p>File A: {_fmt_shape(result.shape_a)}<br>File B: {_fmt_shape(result.shape_b)}</p>

<h2>Headers</h2>
<p>{"Headers match." if result.headers_match else "Headers do NOT match."}</p>
{header_issues}

{row_membership}

<h2>Cell Differences</h2>
<p>Value mismatches: <strong>{len(value_diffs)}</strong> &nbsp;
Type mismatches: <strong>{len(type_diffs)}</strong></p>
{value_table}
{type_table}
{warnings_html}
</body>
</html>
"""


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
