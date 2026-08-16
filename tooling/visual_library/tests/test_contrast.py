"""Tests for contrast.py — the colour-safety checker — and the governed CVD-safe categorical palette.

Guarantees:
- WCAG contrast ratio + CIEDE2000 are correct (the latter checked against Sharma's reference data);
- the governed `categorical_cvd_safe` palette is CVD-distinguishable (worst-case min ΔE well above a
  just-noticeable difference) and measurably safer than the current brand.data_colors;
- the color_semantics.yaml block stays in lockstep with contrast.py (no silent drift);
- series_palette flags the outline-on-white colours and mandates a pattern channel past the cap.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import contrast as C  # noqa: E402

TOKENS = REPO_ROOT / "core" / "templates" / "page_templates" / "tokens" / "color_semantics.yaml"
BRAND_DATA_COLORS = ["#0078D4", "#50E6FF", "#8661C5", "#F7630C",
                     "#008575", "#E3008C", "#EF6950", "#FFB900"]


# --- WCAG -------------------------------------------------------------------
def test_contrast_ratio_known_values():
    assert C.contrast_ratio("#000000", "#FFFFFF") == 21.0
    assert C.contrast_ratio("#FFFFFF", "#FFFFFF") == 1.0
    assert C.contrast_ratio("#FFFFFF", "#000000") == 21.0  # symmetric


def test_relative_luminance_bounds():
    assert C.relative_luminance("#000000") == 0.0
    assert abs(C.relative_luminance("#FFFFFF") - 1.0) < 1e-9


# --- CIEDE2000 (Sharma et al. 2005 reference pair) --------------------------
def test_ciede2000_matches_reference():
    # Sharma et al. 2005 reference pairs (catch hue-rotation / RT-term bugs)
    d = C.delta_e_ciede2000((50.0, 2.6772, -79.7751), (50.0, 0.0, -82.7485))
    assert abs(d - 2.0425) < 0.01, f"CIEDE2000 off: {d}"
    d2 = C.delta_e_ciede2000((50.0, 3.1571, -77.2803), (50.0, 0.0, -82.7485))
    assert abs(d2 - 2.8615) < 0.01, f"CIEDE2000 off: {d2}"
    d3 = C.delta_e_ciede2000((60.2574, -34.0099, 36.2677), (60.4626, -34.1751, 39.4387))
    assert abs(d3 - 1.2644) < 0.01, f"CIEDE2000 off: {d3}"


def test_delta_e_identity_and_symmetry():
    assert C.delta_e("#0072B2", "#0072B2") == 0.0
    assert C.delta_e("#0072B2", "#D55E00") == C.delta_e("#D55E00", "#0072B2")


# --- CVD simulation ---------------------------------------------------------
def test_simulate_cvd_returns_hex_and_is_deterministic():
    for k in C.CVD_KINDS:
        h = C.simulate_cvd("#009E73", k)
        assert h.startswith("#") and len(h) == 7
        assert C.simulate_cvd("#009E73", k) == h  # deterministic
    # a neutral grey stays neutral-ish under any CVD (R≈G≈B)
    r, g, b = C.hex_to_rgb(C.simulate_cvd("#808080", "deutan"))
    assert max(r, g, b) - min(r, g, b) < 12


# --- the governed palette is CVD-safe AND better than the status quo --------
def test_okabe_ito_is_cvd_distinguishable():
    worst = C.palette_report(C.OKABE_ITO)["worst_cvd_delta_e"]
    assert worst >= 10.0, f"Okabe-Ito worst-case CVD min ΔE fell to {worst}"


def test_brand_data_colors_is_measurably_worse():
    brand_worst = C.palette_report(BRAND_DATA_COLORS)["worst_cvd_delta_e"]
    okabe_worst = C.palette_report(C.OKABE_ITO)["worst_cvd_delta_e"]
    assert brand_worst < 5.0, f"brand palette unexpectedly CVD-safe ({brand_worst}) — re-check"
    assert okabe_worst > brand_worst + 5, "the governed palette must be clearly safer than the status quo"


# --- lockstep: YAML block == contrast.py ------------------------------------
def test_color_semantics_palette_in_lockstep_with_contrast():
    block = yaml.safe_load(TOKENS.read_text(encoding="utf-8"))["categorical_cvd_safe"]
    hexes = [c["hex"] for c in block["colors"]]
    assert hexes == C.OKABE_ITO, "categorical_cvd_safe order drifted from contrast.OKABE_ITO"
    assert block["series_cap"] == C.SERIES_CAP
    for c in block["colors"]:
        cr = C.contrast_ratio(c["hex"], "#FFFFFF")
        assert abs(c["contrast_on_white"] - cr) < 0.01, f"{c['hex']}: stale contrast_on_white"
        assert c["solid_safe_on_white"] == (cr >= 3.0), f"{c['hex']}: stale solid_safe_on_white flag"


# --- series_palette behaviour ----------------------------------------------
def test_series_palette_no_fallback_within_cap():
    r = C.series_palette(4)
    assert r["colors"] == C.OKABE_ITO[:4]
    assert r["pattern_fallback"] is False
    assert r["outline_needed_on_white"] == []  # first four are all ≥3:1 on white


def test_series_palette_flags_outline_colours():
    r = C.series_palette(8)
    # the three light Okabe-Ito hues need an outline on white
    assert set(r["outline_needed_on_white"]) == {"#E69F00", "#56B4E9", "#F0E442"}
    assert r["pattern_fallback"] is False


def test_series_palette_mandates_pattern_beyond_cap():
    r = C.series_palette(11)
    assert r["pattern_fallback"] is True
    assert len(r["colors"]) == C.SERIES_CAP  # capped, not fabricated
    assert "pattern" in r["note"]


def test_solid_safe_on_white():
    assert C.solid_safe_on_white("#0072B2") is True
    assert C.solid_safe_on_white("#F0E442") is False  # light yellow, 1.32:1
