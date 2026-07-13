#!/usr/bin/env python3
"""
check_font_family.py — Boutique rubric BC-TYPE-01 ADVISORY reporter

BC-TYPE-01: "one font family across the report; vary only weight and size" (Craft-Core
§5.2). Governance declares a single family (core/templates/page_templates/tokens/
typography.yaml → font_family.preferred = "Segoe UI"; BrandSpec secondary = null). This
reporter reads the committed themes' textClasses (+ any visual font overrides), normalises
each font face to its BASE family (stripping weight words — "Segoe UI Light" is the Light
*weight* of "Segoe UI", which the rule explicitly allows), and lists any theme that mixes
≥2 base families.

It is ADVISORY, not a gate: resolving a genuine second family (e.g. a display font for
callout numerals) is a *design* decision — either govern it (add to the brand stack) or
unify it — not something a validator should force. So this never exits 1 and is not wired
into the Boutique-Scorecard (BC-TYPE-01 stays not_scored) until the design call is made.

Usage:
    python tooling/validation/check_font_family.py     # advisory list (always exit 0)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_DIST = REPO / "products/fabric/powerbi/dist"

# Weight / style words that are NOT a different family — the rule permits varying weight.
_WEIGHT_WORDS = {
    "thin", "hairline", "extralight", "ultralight", "light", "semilight", "regular",
    "normal", "book", "medium", "semibold", "demibold", "bold", "extrabold", "ultrabold",
    "black", "heavy", "italic", "oblique",
}


def base_family(font_face: str) -> str:
    """Normalise a font face to its base family (strip trailing weight/style words)."""
    tokens = [t for t in re.split(r"[\s,]+", (font_face or "").strip()) if t]
    while len(tokens) > 1 and tokens[-1].lower() in _WEIGHT_WORDS:
        tokens.pop()
    return " ".join(tokens)


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


def multi_family_themes() -> list[tuple[str, list[str]]]:
    """Return [(theme_rel_path, sorted base families), ...] for themes mixing ≥2 families."""
    out: list[tuple[str, list[str]]] = []
    for tj in sorted(_DIST.glob("*.Report/StaticResources/RegisteredResources/*.json")):
        fams = theme_families(tj)
        if len(fams) > 1:
            rel = f"{tj.parent.parent.parent.name}/{tj.name}"
            out.append((rel, sorted(fams)))
    return out


def main() -> int:
    offenders = multi_family_themes()
    print("BC-TYPE-01 (ADVISORY — one font family; weight/size may vary):")
    for rel, fams in offenders:
        print(f"    · {rel}: {len(fams)} base families {fams} — vary only weight/size")
    n = len({r.split('/')[0] for r, _ in offenders})
    print(f"\n{len(offenders)} theme file(s) across {n} report(s) mix ≥2 base families. "
          f"Advisory only — resolve by governing the second family or unifying it (design call).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
