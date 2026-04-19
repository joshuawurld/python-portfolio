#!/usr/bin/env bash
# Runs the tool against the two sample CSVs and writes a markdown report.
set -euo pipefail
cd "$(dirname "$0")/.."
python -m src.cli \
    tests/fixtures/file_a.csv \
    tests/fixtures/file_b.csv \
    --key ID \
    --out examples/example_report.md
