#!/usr/bin/env python3
"""
check_custom_theme.py — Boutique rubric BC-BRAND-01 structural validator (knock-out)

Enforces "a composed custom theme — never the renderer default" (Boutique-Craft-Rubric
BC-BRAND-01, Craft-Core §5.6). Every generated report must register a real custom
theme with a composed palette + semantic colours, not fall back to the Power BI
default. Checkable from the committed PBIR (no render needed): each `.Report` must
carry a `StaticResources/RegisteredResources/*.json` theme whose `dataColors` are
non-empty and that defines the semantic good/neutral/bad slots.

BC-BRAND-01 is a knock-out (weight 6). This validator lets the Boutique-Scorecard
score it structurally (raising coverage) instead of leaving it to the LLM judge.

Usage:
    python tooling/validation/check_custom_theme.py            # all dist reports
    python tooling/validation/check_custom_theme.py --strict   # any default/missing = exit 1

Exit codes:
    0 — every report has a composed custom theme (else 1 when --strict)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[2]
_DIST = REPO / "products/fabric/powerbi/dist"


def classify_theme(report_dir: Path) -> tuple[bool, str]:
    """Return (has_custom_theme, reason) for one .Report directory.

    Pure-ish (filesystem read only) — unit-tested via a tmp fixture in
    tooling/tests/test_custom_theme.py.
    """
    reg = report_dir / "StaticResources" / "RegisteredResources"
    themes = sorted(reg.glob("*.json")) if reg.is_dir() else []
    if not themes:
        return False, "no RegisteredResources theme (renderer default)"
    for t in themes:
        try:
            data = json.loads(t.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        data_colors = data.get("dataColors") or []
        has_semantic = all(k in data for k in ("good", "bad"))
        if data_colors and has_semantic:
            return True, f"custom theme '{data.get('name', t.stem)}' ({len(data_colors)} data colours)"
    return False, "registered theme has no composed palette / semantic colours"


def check_report(report_dir: Path) -> Optional[bool]:
    """True (custom) / False (default-or-incomplete). None if not a report dir."""
    if not report_dir.is_dir() or not report_dir.name.endswith(".Report"):
        return None
    return classify_theme(report_dir)[0]


def active_theme(report_dir: Path) -> Optional[str]:
    """The report's ACTIVE custom theme name (definition/report.json themeCollection.customTheme.name).

    Distinct from classify_theme, which only asks whether *a* composed theme is registered;
    a report can register several resources but applies exactly one. Filesystem read only.
    PBIR only: a PBIR-Legacy root `report.json` is not read (PBIR is GA and the default,
    Learn power-bi/developer/projects/projects-report, read 2026-10-01; I-21 W5.8).
    """
    rj = report_dir / "definition" / "report.json"
    if not rj.is_file():
        return None
    try:
        data = json.loads(rj.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    ct = (data.get("themeCollection", {}) or {}).get("customTheme", {}) or {}
    name = ct.get("name")
    return str(name) if name else None


def check_consistency(dist: Path = _DIST) -> tuple[dict[str, str], bool]:
    """BC-BRAND-02: every report applies ONE and the same active custom theme, so the set
    looks like one firm. Returns ({report: active_theme}, is_consistent). Pure-ish."""
    reports = sorted(dist.glob("*.Report")) if dist.is_dir() else []
    themes = {r.name: t for r in reports if (t := active_theme(r))}
    return themes, len(set(themes.values())) <= 1


def main() -> int:
    parser = argparse.ArgumentParser(description="BC-BRAND-01/02 custom-theme validator")
    parser.add_argument("--strict", action="store_true", help="Missing/default theme (or drift) = exit 1")
    parser.add_argument("--consistency", action="store_true",
                        help="BC-BRAND-02: all reports must share one active theme")
    args = parser.parse_args()

    if args.consistency:
        themes, ok = check_consistency()
        distinct = sorted(set(themes.values()))
        print(f"\nBC-BRAND-02: {len(themes)} reports, {len(distinct)} distinct active theme(s).")
        if not ok:
            from collections import Counter  # noqa: PLC0415
            common = Counter(themes.values()).most_common(1)[0][0]
            for rep, t in sorted(themes.items()):
                if t != common:
                    print(f"    ⚠ {rep}: active theme '{t}' ≠ set '{common}' — BC-BRAND-02 drift")
        return 1 if (args.strict and not ok) else 0

    reports = sorted(_DIST.glob("*.Report")) if _DIST.is_dir() else []
    custom = missing = 0
    for r in reports:
        ok, reason = classify_theme(r)
        if ok:
            custom += 1
        else:
            missing += 1
            print(f"    ⚠ {r.name}: {reason} — BC-BRAND-01")

    total = custom + missing
    print(f"\nBC-BRAND-01: {custom}/{total} reports carry a composed custom theme, {missing} default.")
    if args.strict and missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
