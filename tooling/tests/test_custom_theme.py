"""Tests for the BC-BRAND-01 custom-theme validator (knock-out).

Covers the classifier against synthetic report dirs and a guard that the committed
dist reports all carry a composed custom theme (never the renderer default).
"""
from __future__ import annotations

import json
from pathlib import Path

from tooling.validation.check_custom_theme import (
    classify_theme, check_report, active_theme, check_consistency,
)

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


# ── BC-BRAND-02: cross-report theme consistency ──────────────────────────────

def _make_active(tmp_path: Path, name: str, theme_name: str) -> Path:
    rep = tmp_path / f"{name}.Report"
    (rep / "definition").mkdir(parents=True)
    (rep / "definition" / "report.json").write_text(
        json.dumps({"themeCollection": {"customTheme": {"name": theme_name}}}), encoding="utf-8")
    return rep


def test_active_theme_reads_report_json(tmp_path):
    rep = _make_active(tmp_path, "UC-A", "Brand_Navy")
    assert active_theme(rep) == "Brand_Navy"


def test_active_theme_ignores_pbir_legacy_root_report_json(tmp_path):
    """I-21 W5.8: PBIR only. A root report.json (PBIR-Legacy) is no longer read."""
    rep = tmp_path / "UC-L.Report"
    rep.mkdir()
    (rep / "report.json").write_text(
        json.dumps({"themeCollection": {"customTheme": {"name": "Legacy_Theme"}}}), encoding="utf-8")
    assert active_theme(rep) is None


def test_consistency_passes_when_all_share_one_theme(tmp_path):
    _make_active(tmp_path, "UC-A", "Brand_Navy")
    _make_active(tmp_path, "UC-B", "Brand_Navy")
    themes, ok = check_consistency(tmp_path)
    assert ok is True and set(themes.values()) == {"Brand_Navy"}


def test_consistency_flags_drift(tmp_path):
    _make_active(tmp_path, "UC-A", "Brand_Navy")
    _make_active(tmp_path, "UC-B", "Brand_Rose")   # a second firm-look → drift
    _themes, ok = check_consistency(tmp_path)
    assert ok is False


def test_committed_dist_is_brand_consistent():
    """BC-BRAND-02: the committed report set applies one active theme (looks like one firm)."""
    _themes, ok = check_consistency(_DIST)
    assert ok is True, f"active-theme drift across reports: {sorted(set(_themes.values()))}"
