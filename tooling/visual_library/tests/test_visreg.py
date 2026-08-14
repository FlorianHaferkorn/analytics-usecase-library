"""Tests for visreg.py — perceptual visual-regression over the Deneb render set.

Guarantees:
- signatures are deterministic;
- the committed baseline still matches a fresh vl-convert render of every idiom, within tolerance
  (the regression gate — fails loudly with a rebaseline hint on real drift, or on a new/dropped idiom);
- the gate is NOT a no-op: a materially different image is flagged as drift;
- the pixelmatch-style exact diff behaves at the extremes.

Skips cleanly where vl-convert / Pillow / numpy are absent (as the other render tests do).
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library" / "acceptance"))


def _imports():
    pytest.importorskip("vl_convert")
    pytest.importorskip("PIL")
    pytest.importorskip("numpy")
    import visreg  # noqa: E402
    return visreg


def _solid(color):
    from PIL import Image
    im = Image.new("RGBA", (64, 64), color)
    b = io.BytesIO()
    im.save(b, "PNG")
    return b.getvalue()


def test_signature_is_deterministic():
    visreg = _imports()
    import render_acceptance
    png = render_acceptance.render_deneb_png("bar_ranking")
    assert visreg.signature(png) == visreg.signature(png)


def test_baseline_file_is_present_and_well_formed():
    visreg = _imports()
    base = visreg.load_baseline()
    assert base["tool"] == "deneb_vegalite" and base["signatures"]
    assert base["count"] == len(base["signatures"])
    for tag, sig in base["signatures"].items():
        assert len(sig["dhash"]) == 64            # 256-bit hash as hex
        assert len(bytes.fromhex(sig["color"])) == 8 * 8 * 3


def test_fresh_render_matches_committed_baseline():
    """The gate: re-render every Deneb idiom and compare to the committed signature within tolerance.
    A real pixel drift, or a new/dropped idiom, fails here with a `visreg.py baseline` hint."""
    visreg = _imports()
    r = visreg.check_against_baseline()
    assert r["checked"] >= 20, f"expected the full Deneb set, got {r['checked']}"
    assert not r["new"], f"idioms without a baseline signature — run `visreg.py baseline`: {r['new']}"
    assert not r["dropped"], f"baseline has signatures for idioms no longer rendered: {r['dropped']}"
    assert not r["drifts"], f"visual drift vs baseline (rebaseline if intended): {r['drifts']}"


def test_gate_detects_a_material_change():
    """Not a no-op: the same idiom under a very different data scenario must register as drift."""
    visreg = _imports()
    import render_acceptance
    import render
    import vl_convert as vlc
    spec = json.loads(render.render("bar_ranking", "deneb_vegalite")[0])
    alt = render_acceptance._sized_with_data(spec, render_acceptance.SCENARIOS["many_categories"])
    base_png = render_acceptance.render_deneb_png("bar_ranking")
    alt_png = vlc.vegalite_to_png(json.dumps(alt))
    c = visreg.compare(visreg.signature(base_png), visreg.signature(alt_png))
    assert c["drift"] is True, f"gate missed a material change: {c}"


def test_color_axis_catches_uniform_recolour():
    """A uniform recolour has no structure change (dHash stable) but must be caught by the colour grid."""
    visreg = _imports()
    c = visreg.compare(visreg.signature(_solid((255, 255, 255, 255))),
                       visreg.signature(_solid((0, 0, 0, 255))))
    assert c["drift"] is True and c["color_mae"] > visreg.COLOR_MAX_MAE


def test_pixel_diff_extremes():
    visreg = _imports()
    white, black = _solid((255, 255, 255, 255)), _solid((0, 0, 0, 255))
    assert visreg.pixel_diff(white, white)["diff_fraction"] == 0.0
    assert visreg.pixel_diff(white, black)["diff_fraction"] == 1.0
