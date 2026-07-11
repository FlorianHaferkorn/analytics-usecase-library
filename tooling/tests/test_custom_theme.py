"""Tests for the BC-BRAND-01 custom-theme validator (knock-out).

Covers the classifier against synthetic report dirs and a guard that the committed
dist reports all carry a composed custom theme (never the renderer default).
"""
from __future__ import annotations

import json
from pathlib import Path

from tooling.validation.check_custom_theme import classify_theme, check_report

REPO = Path(__file__).resolve().parents[2]
_DIST = REPO / "products/fabric/powerbi/dist"


def _make_report(tmp_path: Path, theme: dict | None) -> Path:
    rep = tmp_path / "UC-TEST.Report"
    reg = rep / "StaticResources" / "RegisteredResources"
    reg.mkdir(parents=True)
    if theme is not None:
        (reg / "Brand_Test.json").write_text(json.dumps(theme), encoding="utf-8")
    return rep


def test_composed_theme_passes(tmp_path):
    ok, _ = classify_theme(_make_report(tmp_path, {
        "name": "Brand_Test", "dataColors": ["#061840", "#A2A0A1"],
        "good": "#1F6F47", "bad": "#8B1E24",
    }))
    assert ok is True


def test_no_registered_theme_fails(tmp_path):
    rep = tmp_path / "UC-TEST.Report"
    (rep / "StaticResources").mkdir(parents=True)
    ok, reason = classify_theme(rep)
    assert ok is False and "default" in reason


def test_empty_palette_fails(tmp_path):
    ok, reason = classify_theme(_make_report(tmp_path, {"name": "x", "dataColors": [], "good": "#1", "bad": "#2"}))
    assert ok is False


def test_missing_semantic_colours_fails(tmp_path):
    ok, _ = classify_theme(_make_report(tmp_path, {"name": "x", "dataColors": ["#061840"]}))
    assert ok is False


def test_committed_dist_all_custom_themed():
    reports = sorted(_DIST.glob("*.Report"))
    assert reports, "no dist reports found"
    missing = [r.name for r in reports if check_report(r) is False]
    assert missing == [], f"reports on renderer default: {missing}"
