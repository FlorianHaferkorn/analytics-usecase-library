"""Tests for the BC-TYPE-01 (governed font families) validator.

The governed type system is `preferred` (Segoe UI, text) + `display` (DIN, highlight-value
numerals) + fallbacks. 'Segoe UI Light' is the Light weight of 'Segoe UI' (allowed); DIN is
governed as the display face; an ungoverned family fails the gate.
"""
from __future__ import annotations

from pathlib import Path

from tooling.validation.check_font_family import (
    base_family, theme_families, governed_families, ungoverned_in_theme, check_registry,
)

REPO = Path(__file__).resolve().parents[2]


def test_weight_words_and_css_stack_normalise_to_base_family():
    assert base_family("Segoe UI Light") == "Segoe UI"
    assert base_family("Inter, system-ui, -apple-system, sans-serif") == "Inter"
    assert base_family("DIN") == "DIN"


def test_din_is_a_governed_display_family():
    gov = governed_families()
    assert "Segoe UI" in gov and "DIN" in gov   # text + display faces are both governed


def test_theme_with_governed_faces_is_clean(tmp_path):
    import json
    t = tmp_path / "clean.json"
    t.write_text(json.dumps({"textClasses": {
        "title": {"fontFace": "Segoe UI"}, "callout": {"fontFace": "DIN"},
        "label": {"fontFace": "Segoe UI Light"}}}), encoding="utf-8")
    assert ungoverned_in_theme(t) == set()   # DIN + Segoe UI both governed


def test_ungoverned_family_is_flagged(tmp_path):
    import json
    t = tmp_path / "drift.json"
    t.write_text(json.dumps({"textClasses": {
        "title": {"fontFace": "Segoe UI"}, "callout": {"fontFace": "Comic Sans MS"}}}), encoding="utf-8")
    assert ungoverned_in_theme(t) == {"Comic Sans MS"}


def test_committed_dist_uses_only_governed_families():
    """With DIN governed as the display face, every committed theme is compliant."""
    assert check_registry() == [], f"ungoverned font families committed: {check_registry()}"
