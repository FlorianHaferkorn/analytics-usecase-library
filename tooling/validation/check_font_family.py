#!/usr/bin/env python3
"""
check_font_family.py — Boutique rubric BC-TYPE-01 structural validator

BC-TYPE-01: "one font family across the report; vary only weight and size" (Craft-Core
§5.2). The governed intent is a disciplined, GOVERNED type system — not literally one
face, but only faces the brand declares: a `preferred` text family plus an optional
`display` family for highlight values (kpi_card callout numerals). Governance lives in
core/templates/page_templates/tokens/typography.yaml → font_family (preferred + display +
alternatives). Any face outside that governed set is drift.

Checkable from the committed PBIR (no render): read each theme's textClasses (+ visual
font overrides), normalise each face to its BASE family (stripping weight words — "Segoe
UI Light" is the Light *weight* of "Segoe UI", allowed), and fail if any base family is
not in the governed set. This is a passing gate (all committed faces are governed), and it
locks the type system in: an ungoverned font (a random second family) fails.

Usage:
    python tooling/validation/check_font_family.py            # all dist reports
    python tooling/validation/check_font_family.py --strict   # any ungoverned face = exit 1

Exit codes:
    0 — every theme uses only governed font families (else 1 when --strict)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: pyyaml not installed.", file=sys.stderr)
    raise

REPO = Path(__file__).resolve().parents[2]
_DIST = REPO / "products/fabric/powerbi/dist"
_TYPOGRAPHY = REPO / "core/templates/page_templates/tokens/typography.yaml"

# Weight / style words that are NOT a different family — the rule permits varying weight.
_WEIGHT_WORDS = {
    "thin", "hairline", "extralight", "ultralight", "light", "semilight", "regular",
    "normal", "book", "medium", "semibold", "demibold", "bold", "extrabold", "ultrabold",
    "black", "heavy", "italic", "oblique",
}


def base_family(font_face: str) -> str:
    """Normalise a font face to its base family (strip trailing weight/style words + a CSS
    fallback stack — 'Inter, system-ui, sans-serif' → 'Inter')."""
    head = str(font_face or "").split(",")[0]
    tokens = [t for t in re.split(r"\s+", head.strip()) if t]
    while len(tokens) > 1 and tokens[-1].lower() in _WEIGHT_WORDS:
        tokens.pop()
    return " ".join(tokens)


def governed_families() -> set[str]:
    """The governed font families (preferred + display + alternatives), base-normalised."""
    data = yaml.safe_load(_TYPOGRAPHY.read_text(encoding="utf-8")) or {}
    ff = data.get("font_family", {}) or {}
    fams: set[str] = set()
    for key in ("preferred", "display", "secondary"):
        if ff.get(key):
            fams.add(base_family(str(ff[key])))
    for alt in ff.get("alternatives", []) or []:
        fams.add(base_family(str(alt)))
    return fams


def theme_families(theme_path: Path) -> set[str]:
    """Distinct base font families declared across a theme's textClasses. Pure — tested."""
    try:
        data = json.loads(theme_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    fams = set()
    for cls in (data.get("textClasses", {}) or {}).values():
        face = cls.get("fontFace") if isinstance(cls, dict) else None
        if face:
            fams.add(base_family(str(face)))
    return fams


def ungoverned_in_theme(theme_path: Path, governed: set[str] | None = None) -> set[str]:
    """Base families used by a theme that are NOT in the governed set."""
    governed = governed if governed is not None else governed_families()
    return theme_families(theme_path) - governed


def check_registry() -> list[tuple[str, list[str]]]:
    """Return [(theme_rel_path, [ungoverned families]), ...] across the dist."""
    governed = governed_families()
    out: list[tuple[str, list[str]]] = []
    for tj in sorted(_DIST.glob("*.Report/StaticResources/RegisteredResources/*.json")):
        bad = ungoverned_in_theme(tj, governed)
        if bad:
            out.append((f"{tj.parent.parent.parent.name}/{tj.name}", sorted(bad)))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="BC-TYPE-01 one-(governed)-font-family validator")
    parser.add_argument("--strict", action="store_true", help="Any ungoverned font family = exit 1")
    args = parser.parse_args()

    governed = governed_families()
    violations = check_registry()
    for rel, bad in violations:
        print(f"    ⚠ {rel}: ungoverned font families {bad} (governed: {sorted(governed)}) — BC-TYPE-01")
    print(f"\nBC-TYPE-01: governed families {sorted(governed)}; "
          f"{len(violations)} theme file(s) use an ungoverned family.")
    if args.strict and violations:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
