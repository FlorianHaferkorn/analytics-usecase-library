#!/usr/bin/env bash
# OSS Stack validation gate — independent from Stage 1 (core) and Fabric gate
# Run from repo root: bash products/open_source_stack/tooling/run_oss_checks.sh

set -euo pipefail

ROOT="${1:-.}"
echo "Running OSS stack checks..."

echo "[1/4] Validating OSS artifacts..."
python "$ROOT/products/open_source_stack/tooling/validate_oss.py" --root "$ROOT"

echo "[2/4] Running OSS tooling tests..."
cd "$ROOT/products/open_source_stack/tooling"
python -m pytest tests/ -v
cd "$ROOT"

echo "[3/4] Running page generator tests..."
cd "$ROOT/products/open_source_stack/tooling/page_generator"
python -m pytest tests/ -v
cd "$ROOT"

echo "[4/4] Running metric generator tests..."
cd "$ROOT/products/open_source_stack/tooling"
python -m pytest metric_generator/tests/ -v
cd "$ROOT"

echo ""
echo "All OSS checks passed."
