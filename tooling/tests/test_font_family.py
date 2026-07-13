"""Tests for the BC-TYPE-01 (one font family) advisory reporter.

'Segoe UI Light' is the Light weight of 'Segoe UI' (allowed — vary weight); 'DIN' is a
genuinely different family. The reporter is advisory (never gates), and it surfaces the
committed DIN-vs-Segoe-UI drift so the design call (govern vs unify) stays visible.
"""
from __future__ import annotations

from tooling.validation.check_font_family import base_family, theme_families, multi_family_themes


def test_weight_words_normalise_to_base_family():
    assert base_family("Segoe UI Light") == "Segoe UI"
    assert base_family("Segoe UI Semibold") == "Segoe UI"
    assert base_family("Segoe UI") == "Segoe UI"


def test_distinct_family_is_kept():
    assert base_family("DIN") == "DIN"
    assert base_family("Inter Bold") == "Inter"


def test_theme_with_one_family_is_clean(tmp_path):
    import json
    t = tmp_path / "clean.json"
    t.write_text(json.dumps({"textClasses": {
        "title": {"fontFace": "Segoe UI"}, "callout": {"fontFace": "Segoe UI Light"}}}))
    assert theme_families(t) == {"Segoe UI"}   # Light is a weight, not a family


def test_theme_mixing_families_is_flagged(tmp_path):
    import json
    t = tmp_path / "mixed.json"
    t.write_text(json.dumps({"textClasses": {
        "title": {"fontFace": "Segoe UI"}, "callout": {"fontFace": "DIN"}}}))
    assert theme_families(t) == {"DIN", "Segoe UI"}


def test_committed_din_drift_is_surfaced_as_advisory():
    """The known finding: the composed themes use DIN for callouts (ungoverned) — the
    advisory must surface it (this guards the finding stays visible, not that it passes)."""
    offenders = multi_family_themes()
    assert offenders, "expected the committed DIN drift to be reported"
    assert all("DIN" in fams for _rel, fams in offenders)
