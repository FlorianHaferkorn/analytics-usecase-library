"""The BrandSpec → Power BI theme derivation must carry its own fonts (W6.10, Fluent 2).

A custom theme layers on top of the report's base theme; whatever it leaves out comes from
the base theme (Learn, power-bi/create-reports/desktop-report-themes, checked 29.09.2026).
Since August 2026 new reports start on the Fluent 2 base theme, which brings its own fonts
and font sizes (Learn, power-bi/create-reports/power-bi-reports-visual-defaults). A derived
brand theme without `textClasses` therefore shows Fluent 2 fonts in a new report and the
base theme fonts (CY25SU10; since D-587, 30.09.2026: CY26SU10) in a generated one — the brand font never reaches either.

Measured on 29.09.2026 before the fix: `spec_to_pbi_theme` wrote no `textClasses`, put the
font into a card named `fontFamily` (`visualStyles.*.*.fontFamily[{"value": …}]`, not a
Power BI card) and wrapped every per-visual font in a `{"value": {...}}` object, although
theme cards are `[{"<propertyName>": <propertyValue>}]` (Learn,
power-bi/create-reports/report-themes-create-custom).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from core.brand.derivations.loader import load_brand_spec  # noqa: E402
from core.brand.derivations.pbi_theme import spec_to_pbi_theme  # noqa: E402

_SPECS = [
    _REPO / "core" / "brand" / "samples" / "generic_brand.yaml",
    _REPO / "showcases" / "aurora_group" / "brand" / "brand_spec.yaml",
]
_PRIMARY_TEXT_CLASSES = ("callout", "title", "header", "label")
_PROFILES = ("powerbi_design_base", "powerbi_production")


def _themes():
    for spec_path in _SPECS:
        spec = load_brand_spec(spec_path)
        for profile in _PROFILES:
            yield pytest.param(spec, spec_to_pbi_theme(spec, canvas_profile=profile),
                               id=f"{spec_path.parent.name}-{profile}")


@pytest.mark.parametrize(("spec", "theme"), list(_themes()))
def test_primary_text_classes_are_set_from_the_brand(spec, theme):
    tc = theme.get("textClasses") or {}
    missing = [c for c in _PRIMARY_TEXT_CLASSES
               if not all(k in (tc.get(c) or {}) for k in ("fontFace", "fontSize", "color"))]
    assert not missing, f"text classes left to the base theme: {missing}"
    font = spec["typography"]["font_family"]["primary"]
    assert {tc[c]["fontFace"] for c in _PRIMARY_TEXT_CLASSES} == {font}
    assert {tc[c]["color"] for c in _PRIMARY_TEXT_CLASSES} == {theme["foreground"]}


@pytest.mark.parametrize(("spec", "theme"), list(_themes()))
def test_text_class_sizes_respect_the_powerbi_minimums(spec, theme):
    pbi_min = spec["typography"]["tool_minimums"]["powerbi"]
    tc = theme["textClasses"]
    assert tc["label"]["fontSize"] >= pbi_min["label_pt"]
    assert tc["title"]["fontSize"] >= pbi_min["body_pt"]
    assert tc["header"]["fontSize"] >= pbi_min["body_pt"]
    assert tc["callout"]["fontSize"] >= pbi_min["kpi_pt"]


@pytest.mark.parametrize(("spec", "theme"), list(_themes()))
def test_visual_style_cards_have_the_theme_file_shape(spec, theme):
    """`visualStyles.<visual>.<preset>.<card>` is a list of flat property dicts."""
    bad: list[str] = []
    for visual, presets in theme["visualStyles"].items():
        for preset, cards in presets.items():
            for card, entries in cards.items():
                where = f"{visual}.{preset}.{card}"
                if card in ("fontFamily", "fontSize"):
                    bad.append(f"{where}: property used as card name")
                if not isinstance(entries, list) or not all(isinstance(e, dict) for e in entries):
                    bad.append(f"{where}: not a list of property dicts")
                    continue
                for e in entries:
                    if isinstance(e.get("value"), dict):
                        bad.append(f"{where}: properties wrapped in a 'value' object")
    assert not bad, bad
