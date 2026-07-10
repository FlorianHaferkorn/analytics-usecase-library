#!/usr/bin/env python3
"""
check_mixed_scale.py — Boutique rubric BC-CHART-01 structural validator (knock-out)

Enforces "no mixed scale on one axis" (Boutique-Craft-Rubric BC-CHART-01) at the intent
layer: a 30-second chart exhibit that binds measures of ≥2 different unit types (e.g. %
and €) to a single axis is a knock-out. This is the R1.4 founding bug turned into a
permanent regression guard — and the second structural rubric rule wired into the gate
(after BC-NARR-01 / check_exhibit_message.py).

Scope: renderer-agnostic. Units are resolved from the governed KPI catalog
(core/kpi_catalog/kpis/<kpi_id>.yaml → unit_format). Measures not in the catalog
(display-only names) are ignored — the rule flags only clearly-different governed units.

Usage:
    python tooling/validation/check_mixed_scale.py            # all use cases
    python tooling/validation/check_mixed_scale.py COM-002     # single use case
    python tooling/validation/check_mixed_scale.py --exit-zero # warn mode (CI)

Exit codes:
    0 — no exhibit mixes units on one axis (or --exit-zero)
    1 — a chart exhibit binds ≥2 different unit types to one axis (BC-CHART-01 knock-out)
"""
from __future__ import annotations

import argparse
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    if __name__ == "__main__":
        print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    raise

REPO = Path(__file__).resolve().parents[2]
_KPI_DIR = REPO / "core/kpi_catalog/kpis"

# Chart exhibits share one value axis; cards show a single value, tables allow mixed
# columns by design — neither can "mix scale on an axis".
_CARD_TYPES = {"kpi_card", "kpi_card_hero", "kpi_card_compact", "status_tile"}
_TABLE_TYPES = {"recommendation_table", "table_with_databars"}


def unit_class(unit_format: Optional[str]) -> Optional[str]:
    """Coarse unit class from a KPI's unit_format string. None = unknown/ignore.

    Pure function — unit-tested in tooling/tests/test_mixed_scale.py.
    """
    s = (unit_format or "").strip().strip("'\" ").lower()
    if not s:
        return None
    if "%" in s or "pct" in s or "percent" in s or "ppt" in s:
        return "PCT"
    if "eur" in s or "usd" in s or "gbp" in s or "€" in s or "$" in s or "currency" in s:
        return "CUR"
    if "day" in s:
        return "DAYS"
    if "hour" in s or "minute" in s:
        return "TIME"
    if "index" in s or "score" in s or "turns" in s or "ratio" in s:
        return "INDEX"
    if "count" in s or "unit" in s or "item" in s or "defect" in s or "#" in s:
        return "COUNT"
    return None


@lru_cache(maxsize=None)
def _kpi_unit_class(kpi_id: str) -> Optional[str]:
    f = _KPI_DIR / f"{kpi_id}.yaml"
    if not f.exists():
        return None
    try:
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return None
    uf = (
        (data.get("business", {}) or {}).get("unit_format")
        or data.get("unit_format")
        or (data.get("technical", {}) or {}).get("unit_format")
    )
    return unit_class(uf if isinstance(uf, str) else None)


def _measures(exhibit: dict[str, Any]) -> list[str]:
    kids = exhibit.get("kpi_ids")
    if not isinstance(kids, list):
        kid = exhibit.get("kpi_id")
        kids = [kid] if kid else []
    return [k for k in kids if isinstance(k, str) and k.strip()]


def classify_exhibit(exhibit: dict[str, Any]) -> tuple[bool, str]:
    """Return (is_mixed, reason). is_mixed True → BC-CHART-01 violation."""
    vt = exhibit.get("visual_type") or ""
    if vt in _CARD_TYPES or vt in _TABLE_TYPES:
        return False, "card/table — not a shared axis"
    measures = _measures(exhibit)
    if len(measures) < 2:
        return False, "single measure"
    classes = {c for c in (_kpi_unit_class(m) for m in measures) if c is not None}
    if len(classes) >= 2:
        return True, f"mixes units {sorted(classes)} on one axis (BC-CHART-01)"
    return False, f"one unit class ({sorted(classes) or 'unknown'})"


def check_bracket(path: Path) -> tuple[int, int, list[str]]:
    """Return (ok, violations, messages) for one bracket."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    ux = data.get("ux_layout_rules", {}) or {}
    ok = violations = 0
    lines: list[str] = []
    for page_key in ("page_1_summary", "page_2_execution"):
        page = ux.get(page_key, {}) or {}
        for ex in page.get("component_30s", []) or []:
            if not isinstance(ex, dict):
                continue
            mixed, reason = classify_exhibit(ex)
            slot = ex.get("slot_id") or ex.get("visual_type") or "?"
            if mixed:
                violations += 1
                lines.append(f"    ✗ {slot}: {reason}")
            else:
                ok += 1
    return ok, violations, lines


def main() -> int:
    parser = argparse.ArgumentParser(description="BC-CHART-01 mixed-scale validator")
    parser.add_argument("use_case_id", nargs="?", help="Validate a single use case by ID substring")
    parser.add_argument("--exit-zero", action="store_true", help="Always exit 0 (CI warn mode)")
    args = parser.parse_args()

    brackets = sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml"))
    if args.use_case_id:
        brackets = [b for b in brackets if args.use_case_id.lower() in str(b).lower()]
        if not brackets:
            print(f"No UseCase_Bracket.yaml found matching '{args.use_case_id}'", file=sys.stderr)
            return 1

    total_ok = total_viol = 0
    for b in brackets:
        ok, viol, lines = check_bracket(b)
        total_ok += ok
        total_viol += viol
        if lines:
            print(f"{b.relative_to(REPO)}")
            print("\n".join(lines))

    print(f"\nBC-CHART-01: {total_ok} single-scale exhibit(s), {total_viol} mixed-scale violation(s).")
    if args.exit_zero:
        return 0
    return 1 if total_viol else 0


if __name__ == "__main__":
    raise SystemExit(main())
