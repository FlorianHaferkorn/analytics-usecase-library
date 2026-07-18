#!/usr/bin/env python3
"""check_visual_format.py — is every governed visual formattable to boutique craft?

Classic BI craft (axes, number format, deviation-vs-target, semantic colour) is only as good as the
metadata behind it. This gate resolves each 3s hero + 30s exhibit through
``visual_format_policy.format_spec`` and reports where the governed inputs are missing, so a report
can't silently ship an unformatted or verdict-less visual:

  • the KPI has no ``unit_format`` → the number format falls back to a generic default;
  • a **vs_target / vs_plan** KPI has **no benchmark** in benchmarks.yaml → no deviation and no
    semantic colour are possible (colour would have nothing to judge against);
  • a 3-second hero has no ``status_logic`` → good/bad direction is undefined.

Advisory by default (like the chart-fit check): it surfaces craft gaps for the designer, and grows
into a hard gate per domain as the benchmark/format coverage is filled. `--strict` fails on findings.

Usage:
    python tooling/validation/check_visual_format.py            # advisory report
    python tooling/validation/check_visual_format.py --strict   # any gap = exit 1
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: pyyaml not installed.", file=sys.stderr)
    sys.exit(1)

REPO = Path(__file__).resolve().parents[2]


def _policy():
    # base → base import (tool-neutral policy lives in tooling/reporting; the base never depends on
    # the PBI product folder).
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from tooling.reporting import format_policy
    return format_policy


def _kpi_units() -> dict[str, str]:
    out: dict[str, str] = {}
    for f in (REPO / "core/kpi_catalog/kpis").glob("*.yaml"):
        if f.stem == "_index":
            continue
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        kid = d.get("kpi_id", f.stem)
        out[kid] = ((d.get("business") or {}).get("unit_format") or "").strip()
    return out


def check_bracket(bracket: dict[str, Any], units: dict[str, str], pol) -> list[str]:
    ucid = bracket.get("id", "?")
    ux = bracket.get("ux_layout_rules", {}) or {}
    out: list[str] = []
    p1 = ux.get("page_1_summary", {}) or {}

    hero = p1.get("component_3s") or {}
    if isinstance(hero, dict) and hero.get("kpi_id"):
        kid = hero["kpi_id"]
        if not (hero.get("status_logic") or "").strip():
            out.append(f"{ucid}: 3s hero `{kid}` has no status_logic — good/bad direction undefined")
        ts = pol.target_source(kid, hero.get("comparison"))
        if ts["kind"] == "none":
            out.append(f"{ucid}: 3s hero `{kid}` has no target (no benchmark, not vs-plan) → no verdict "
                       f"possible; define an org target")
        elif ts["kind"] == "plan":
            out.append(f"{ucid}: 3s hero `{kid}` steers vs plan (no industry benchmark) → deviation/"
                       f"semantic colour compute once the plan-target measure exists [informational]")
        if not units.get(kid):
            out.append(f"{ucid}: 3s hero `{kid}` has no unit_format → generic number format")

    for i, c in enumerate(p1.get("component_30s") or [], 1):
        kid = c.get("kpi_id")
        if not kid:
            continue
        if not units.get(kid):
            out.append(f"{ucid}/30s#{i} `{kid}`: no unit_format → generic number format")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Govern visual formatting / semantic-colour readiness")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    pol = _policy()
    units = _kpi_units()

    total = 0
    for b in sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml")):
        for p in check_bracket(yaml.safe_load(b.read_text(encoding="utf-8")) or {}, units, pol):
            print(f"  ℹ {p}")
            total += 1
    n = len(list(REPO.glob("core/usecases/**/UseCase_Bracket.yaml")))
    print(f"\ncheck_visual_format: {n} use cases · {total} formatting-readiness advisory(ies).")
    if args.strict and total:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
