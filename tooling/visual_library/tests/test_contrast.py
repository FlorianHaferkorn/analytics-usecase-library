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

import pytest
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


# --- ensure_contrast (hue-kept OKLCH lightness step) --------------------------
def _hue_drift(a: str, b: str) -> float:
    ha, hb = C.hex_to_oklch(a)[2], C.hex_to_oklch(b)[2]
    d = abs(ha - hb) % 360
    return min(d, 360 - d)


def test_ensure_contrast_lifts_brand_accent_on_white_and_keeps_hue():
    assert C.contrast_ratio("#2ECDE7", "#FFFFFF") < 3.0          # the Design-Lab finding
    out = C.ensure_contrast("#2ECDE7", "#FFFFFF")
    assert out != "#2ECDE7" and out == out.upper() and len(out) == 7
    assert C.contrast_ratio(out, "#FFFFFF") >= 3.0
    assert C.hex_to_oklch(out)[0] < C.hex_to_oklch("#2ECDE7")[0], "must darken on a light ground"
    assert _hue_drift("#2ECDE7", out) <= 3.0
    assert C.contrast_ratio(out, "#FFFFFF") < 3.3, "small steps: first pass, no big overshoot"
    assert C.ensure_contrast("#2ECDE7", "#FFFFFF") == out         # deterministic


def test_ensure_contrast_passes_compliant_colour_through():
    assert C.ensure_contrast("#0072B2", "#FFFFFF") == "#0072B2"
    assert C.ensure_contrast("#0072b2", "#FFFFFF", 4.5) == "#0072B2"


def test_ensure_contrast_lightens_on_dark_ground():
    navy = "#1F3864"
    assert C.contrast_ratio(navy, "#1B1A19") < 3.0
    out = C.ensure_contrast(navy, "#1B1A19")
    assert C.contrast_ratio(out, "#1B1A19") >= 3.0
    assert C.hex_to_oklch(out)[0] > C.hex_to_oklch(navy)[0], "must lighten on a dark ground"
    assert _hue_drift(navy, out) <= 3.0


def test_ensure_contrast_unreachable_raises():
    with pytest.raises(ValueError):
        C.ensure_contrast("#1F3864", "#1B1A19", 18.0)             # white on #1B1A19 is 17.38:1
    with pytest.raises(ValueError):
        C.ensure_contrast("#808080", "#FFFFFF", 22.0)


def test_oklch_round_trip_is_identity_on_governed_palette():
    for c in C.OKABE_ITO + C.TOL_BRIGHT:
        assert C.oklch_to_hex(*C.hex_to_oklch(c)) == c


# --- reserved semantic colours -------------------------------------------------
def _semantic() -> dict:
    return yaml.safe_load(TOKENS.read_text(encoding="utf-8"))["semantic"]


def test_reserved_conflicts_flags_bad_colour_and_near_copy():
    bad = _semantic()["negative"]
    assert bad == "#A4262C"
    found = C.reserved_conflicts(["#0072B2", "#A4262C", "#A5282D"], {"bad": bad})
    assert {f["color"] for f in found} == {"#A4262C", "#A5282D"}
    for f in found:
        assert set(f) == {"color", "reserved", "role", "delta_e", "vision"}
        assert f["role"] == "bad" and f["reserved"] == bad and f["delta_e"] < 10.0


def test_reserved_conflicts_spares_okabe_blue():
    assert C.reserved_conflicts(["#0072B2"], {"bad": "#A4262C"}) == []


def test_reserved_conflicts_sees_cvd_only_collisions():
    """Okabe-Ito vermillion vs ALUCA positive green: far apart for normal vision, one colour
    for a protanope (measured 0.79 ΔE00) — a normal-vision-only check would miss it."""
    found = C.reserved_conflicts(["#D55E00"], {"positive": _semantic()["positive"]}, visions=C.ALL_VISIONS)
    assert C.delta_e("#D55E00", _semantic()["positive"]) > 50
    assert found and found[0]["vision"] == "protan"
    # default = normal vision only (status never travels without icon + label)
    assert C.reserved_conflicts(["#D55E00"], {"positive": _semantic()["positive"]}) == []


# --- palette_gate ---------------------------------------------------------------
def test_palette_gate_okabe_five_on_white_passes():
    g = C.palette_gate(C.OKABE_ITO[:5], "#FFFFFF", {"bad": _semantic()["negative"]})
    assert g["ok"], g["failures"]
    assert g["needs_label_or_outline"] == []


def test_palette_gate_on_dark_ground_reports_label_needs():
    g = C.palette_gate(C.OKABE_ITO[:5], "#1B1A19", {"bad": _semantic()["negative"]})
    assert g["ok"], "low non-text contrast is a warning, not a failure"
    assert g["needs_label_or_outline"] == ["#000000"]
    assert all(w["check"] == "needs_label_or_outline" for w in g["warnings"])


def test_palette_gate_fails_on_reserved_conflict_and_cvd_collapse():
    g = C.palette_gate(["#0072B2", "#A5282D"], "#FFFFFF", {"bad": "#A4262C"})
    assert not g["ok"] and g["failures"][0]["check"] == "reserved_conflict"
    g2 = C.palette_gate(["#107C10", "#D55E00"], "#FFFFFF", {})    # protan ΔE 0.79
    assert not g2["ok"] and g2["failures"][0]["check"] == "cvd_separation"


def test_thresholds_decide_unrounded():
    """BO-036 (Freelancing, 01.10.2026): a colour just under 3:1 (#62A462 on white, 2.9975) rounded to 3.00 and passed;
    the Meridian theme gate measures unrounded and failed. Decisions now use the exact ratio."""
    assert C.contrast_ratio("#62A462", "#FFFFFF") == 3.0
    assert C.contrast_ratio_exact("#62A462", "#FFFFFF") < 3.0
    assert not C.solid_safe_on_white("#62A462")
    darker = C.ensure_contrast("#62A462", "#FFFFFF", 3.0)
    assert darker != "#62A462" and C.contrast_ratio_exact(darker, "#FFFFFF") >= 3.0
