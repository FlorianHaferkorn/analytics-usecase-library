#!/usr/bin/env python3
"""
check_benchmarks.py — Content-Grounding §6.3 provenance validator (K4)

Enforces that every benchmark ("what good looks like") is *governed and grounded*,
never freely asserted (KONZEPT §6.3, Storytelling_Principles grounding rules):

  1. Golden Thread — kpi_id resolves to a real KPI (core/kpi_catalog/kpis/<id>.yaml).
  2. Provenance — source_type is one of benchmark_sources.yaml, and a concrete
     `source` string + ISO `as_of` date are present.
  3. Unit sanity — value is consistent with the declared unit (e.g. a pct in 0..100).

This is the structural guarantee behind the third comparison axis (vs. benchmark):
a benchmark that can't cite a dated public source simply fails the gate, so no
fabricated industry number can reach a report.

Usage:
    python tooling/validation/check_benchmarks.py            # validate the registry
    python tooling/validation/check_benchmarks.py --strict   # any violation = exit 1

Exit codes:
    0 — no violations (advisory by default; --strict makes violations exit 1)
    1 — --strict and ≥1 violation, or the registry/catalog is unreadable
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    if __name__ == "__main__":
        print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    raise

REPO = Path(__file__).resolve().parents[2]
_REGISTRY = REPO / "core/kpi_catalog/benchmarks.yaml"
_SOURCES = REPO / "core/kpi_catalog/benchmark_sources.yaml"
_KPIS_DIR = REPO / "core/kpi_catalog/kpis"

_UNIT_RANGES = {
    "pct": (0.0, 100.0),
    "ratio": (0.0, 100.0),
    "days": (0.0, None),
    "count": (0.0, None),
}


def kpi_exists(kpi_id: str) -> bool:
    return (_KPIS_DIR / f"{kpi_id}.yaml").is_file()


def validate_entry(entry: dict[str, Any], allowed_source_types: set[str]) -> list[str]:
    """Return a list of provenance/grounding violations for one benchmark entry.

    Pure function — unit-tested in tooling/tests/test_benchmarks.py.
    """
    errs: list[str] = []
    kpi_id = entry.get("kpi_id", "")
    if not kpi_id or not kpi_exists(kpi_id):
        errs.append(f"kpi_id '{kpi_id}' does not resolve to a governed KPI (Golden Thread)")
    st = entry.get("source_type", "")
    if st not in allowed_source_types:
        errs.append(f"source_type '{st}' not in benchmark_sources.yaml")
    if not str(entry.get("source", "")).strip():
        errs.append("source citation missing (no free assertions)")
    as_of = str(entry.get("as_of", ""))
    if not (len(as_of) == 10 and as_of[4] == "-" and as_of[7] == "-"):
        errs.append(f"as_of '{as_of}' is not an ISO date (YYYY-MM-DD)")
    unit = entry.get("unit", "")
    val = entry.get("value")
    lo, hi = _UNIT_RANGES.get(unit, (None, None))
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        if lo is not None and val < lo:
            errs.append(f"value {val} below sane minimum {lo} for unit '{unit}'")
        if hi is not None and val > hi:
            errs.append(f"value {val} above sane maximum {hi} for unit '{unit}'")
    return errs


def _load_allowed_source_types() -> set[str]:
    data = yaml.safe_load(_SOURCES.read_text(encoding="utf-8")) or {}
    return set((data.get("source_types") or {}).keys())


def check_registry() -> list[tuple[str, str]]:
    """Return [(kpi_id, violation), ...] across the registry."""
    allowed = _load_allowed_source_types()
    data = yaml.safe_load(_REGISTRY.read_text(encoding="utf-8")) or {}
    out: list[tuple[str, str]] = []
    for entry in data.get("benchmarks", []) or []:
        for err in validate_entry(entry, allowed):
            out.append((entry.get("kpi_id", "?"), err))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Content-Grounding §6.3 benchmark validator")
    parser.add_argument("--strict", action="store_true", help="Any violation = exit 1")
    args = parser.parse_args()

    if not _REGISTRY.is_file() or not _SOURCES.is_file():
        print("ERROR: benchmark registry or source catalog missing", file=sys.stderr)
        return 1

    violations = check_registry()
    data = yaml.safe_load(_REGISTRY.read_text(encoding="utf-8")) or {}
    total = len(data.get("benchmarks", []) or [])
    for kpi_id, err in violations:
        print(f"    ⚠ {kpi_id}: {err}")
    ok = total - len({k for k, _ in violations})
    print(f"\nContent-Grounding §6.3: {ok}/{total} benchmarks grounded, {len(violations)} violation(s).")
    if args.strict and violations:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
