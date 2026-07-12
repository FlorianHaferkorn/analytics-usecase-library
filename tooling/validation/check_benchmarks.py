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


_MIN_SOURCES = 2  # industry benchmarks need corroboration — a single source is unreliable


def _is_iso(d: str) -> bool:
    return len(d) == 10 and d[4] == "-" and d[7] == "-"


def validate_entry(entry: dict[str, Any], allowed_source_types: set[str]) -> list[str]:
    """Return a list of provenance/grounding violations for one benchmark entry.

    Enforces the Golden Thread, per-source provenance, and ≥2 corroborating sources.
    Pure function — unit-tested in tooling/tests/test_benchmarks.py.
    """
    errs: list[str] = []
    kpi_id = entry.get("kpi_id", "")
    if not kpi_id or not kpi_exists(kpi_id):
        errs.append(f"kpi_id '{kpi_id}' does not resolve to a governed KPI (Golden Thread)")

    bclass = entry.get("benchmark_class")
    if bclass not in ("normative", "empirical"):
        errs.append(f"benchmark_class '{bclass}' not in ('normative','empirical')")

    sources = entry.get("sources")
    sources = sources if isinstance(sources, list) else []
    if len(sources) < _MIN_SOURCES:
        errs.append(f"only {len(sources)} source(s) — need ≥{_MIN_SOURCES} corroborating references")
    if not any(isinstance(s, dict) and s.get("tier") in ("primary", "large_sample") for s in sources):
        errs.append("no authoritative source (needs ≥1 tier primary/large_sample, not only secondary)")
    for i, s in enumerate(sources):
        if not isinstance(s, dict):
            errs.append(f"source[{i}] is not an object")
            continue
        if s.get("source_type") not in allowed_source_types:
            errs.append(f"source[{i}] source_type '{s.get('source_type')}' not in benchmark_sources.yaml")
        if s.get("tier") not in ("primary", "large_sample", "secondary"):
            errs.append(f"source[{i}] tier '{s.get('tier')}' invalid")
        if len(str(s.get("citation", "")).strip()) < 12:
            errs.append(f"source[{i}] citation missing/too short (no bare assertions)")
        if not _is_iso(str(s.get("as_of", ""))):
            errs.append(f"source[{i}] as_of '{s.get('as_of')}' is not an ISO date")

    # Empirical benchmarks must be peer-relative — a cross-industry average misleads.
    segments = entry.get("segments") or []
    if bclass == "empirical":
        if len(segments) < 2:
            errs.append("empirical benchmark needs ≥2 industry segments (cross-industry average alone misleads)")
        for i, seg in enumerate(segments):
            if not isinstance(seg, dict) or len(str(seg.get("industry", "")).strip()) < 2:
                errs.append(f"segment[{i}] missing industry label")
            if not isinstance(seg.get("value"), (int, float)) or isinstance(seg.get("value"), bool):
                errs.append(f"segment[{i}] value is not numeric")

    unit = entry.get("unit", "")
    val = entry.get("value")
    lo, hi = _UNIT_RANGES.get(unit, (None, None))
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        if lo is not None and val < lo:
            errs.append(f"value {val} below sane minimum {lo} for unit '{unit}'")
        if hi is not None and val > hi:
            errs.append(f"value {val} above sane maximum {hi} for unit '{unit}'")

    rng = entry.get("range")
    if isinstance(rng, dict):
        if rng.get("low") is not None and rng.get("high") is not None and rng["low"] > rng["high"]:
            errs.append(f"range low {rng['low']} > high {rng['high']}")
    return errs


def _load_allowed_source_types() -> set[str]:
    data = yaml.safe_load(_SOURCES.read_text(encoding="utf-8")) or {}
    return set((data.get("source_types") or {}).keys())


def _benchmarked_kpi_ids() -> set[str]:
    data = yaml.safe_load(_REGISTRY.read_text(encoding="utf-8")) or {}
    return {e.get("kpi_id") for e in data.get("benchmarks", []) or [] if e.get("kpi_id")}


def check_bracket_links() -> list[tuple[str, str]]:
    """Reverse Golden Thread: a hero card opting into the benchmark axis
    (`component_3s.benchmark: true`) must have a governed benchmark for its KPI.

    Returns [(bracket_id, violation), ...]. Ties the grounding layer to the report
    model — a report can't claim a benchmark axis the registry can't back.
    """
    benchmarked = _benchmarked_kpi_ids()
    out: list[tuple[str, str]] = []
    for path in sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        card = ((data.get("ux_layout_rules", {}) or {})
                .get("page_1_summary", {}) or {}).get("component_3s") or {}
        if isinstance(card, dict) and card.get("benchmark") is True:
            kpi_id = card.get("kpi_id", "")
            if kpi_id not in benchmarked:
                out.append((data.get("id", path.parent.name),
                            f"hero card opts into benchmark axis but no benchmark "
                            f"for '{kpi_id}' in benchmarks.yaml"))
    return out


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

    link_violations = check_bracket_links()
    for bid, err in link_violations:
        print(f"    ⚠ {bid}: {err}")
    print(f"Benchmark axis links: {len(link_violations)} broken.")

    if args.strict and (violations or link_violations):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
