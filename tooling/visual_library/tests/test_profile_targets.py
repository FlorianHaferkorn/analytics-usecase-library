"""Profile axis and derived targets (A-31 R2).

A profile is either a NOTATION (house_default, ibcs, print_safe: how an idiom is drawn, per
idiom opt-in) or a STYLE (fluent, editorial, minimal: a Vega-Lite config for every idiom).
`fabric_app` and `html_vegalite` are derived from the `deneb_vegalite` track: one Vega-Lite
source, three runtimes. These tests prove the registry is well-formed, the derived targets
are deterministic and frozen, and every idiom x profile actually rasterizes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import render  # noqa: E402

LIB = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library"
CORPUS = REPO_ROOT / "docs" / "architecture" / "research" / "2026-09-30_visual-stack-r1"


def _implemented() -> list[str]:
    return yaml.safe_load((LIB / "index.yaml").read_text(encoding="utf-8"))["implemented"]


def test_every_profile_declares_a_valid_kind():
    for pid in render.all_profiles():
        d = render.profile_def(pid)
        assert d.get("kind") in ("notation", "style"), f"{pid}: kind must be notation or style"
        if d["kind"] == "style":
            base = d.get("base_notation")
            assert base in render.all_profiles("notation"), f"{pid}: base_notation '{base}' is no notation profile"
            assert d.get("vegalite_config"), f"{pid}: a style profile without vegalite_config does nothing"


def test_style_profiles_cite_the_corpus():
    """Every source of a style profile names an entry id that exists in the R1 corpus
    (or the corpus summary, which is marked experimental)."""
    ids = set()
    for f in ("product", "editorial", "fabric", "ibcs_v2"):
        ids |= {e["id"] for e in yaml.safe_load((CORPUS / f"{f}.yaml").read_text(encoding="utf-8"))}
    for pid in render.all_profiles("style"):
        d = render.profile_def(pid)
        for src in d.get("source") or []:
            ref = str(src).split(" ")[0]
            if d.get("status") == "experimental" and "summary" in src:
                continue
            assert ref in ids, f"{pid}: source '{ref}' is not an entry of the R1 corpus"


def test_capabilities_are_known_vegavisual_flags():
    for pid in render.all_profiles():
        caps = render.profile_def(pid).get("vegavisual_capabilities") or {}
        unknown = set(caps) - set(render.VEGAVISUAL_CAPABILITIES)
        assert not unknown, f"{pid}: unknown flags {sorted(unknown)}"
        assert all(isinstance(v, bool) for v in caps.values()), f"{pid}: capability values must be booleans"


def test_profiles_carry_no_brand_colours_in_style():
    """Brand colours are Klasse C (SHARED_SUBSTANCE §2.3) and come from the brand tokens —
    a style profile must not set a categorical range."""
    for pid in render.all_profiles("style"):
        cfg = render.profile_def(pid).get("vegalite_config") or {}
        assert "range" not in cfg, f"{pid}: a style profile sets range colours; those belong to the brand"


def test_style_config_is_the_baseline_overlaid():
    base = render.vegalite_config(render.default_profile())
    for pid in render.all_profiles("style"):
        cfg = render.vegalite_config(pid)
        own = render.profile_def(pid)["vegalite_config"]
        for k, v in own.items():
            if isinstance(v, dict):
                for kk, vv in v.items():
                    assert cfg[k][kk] == vv, f"{pid}: {k}.{kk} not taken from the profile"
            else:
                assert cfg[k] == v
        for k in base:
            assert k in cfg, f"{pid}: lost baseline key '{k}'"


#: Keys only full Vega knows at the top level; Vega-Lite has none of them there. `@microsoft/fabric-visuals`
#: 4.0.0 accepts Vega-Lite or Flint only (`VisualizationSpec = VegaLiteSpecWithOptionalData | FlintSpec`,
#: dist/index.d.ts:37), so a full-Vega spec would not render in the Fabric App (Meridian D-642).
VEGA_ONLY_TOP_LEVEL = ("signals", "scales", "axes", "legends", "marks", "projections")
VEGA_LITE_SCHEMA = "https://vega.github.io/schema/vega-lite/"


def is_vega_lite(spec: dict) -> bool:
    return str(spec.get("$schema", "")).startswith(VEGA_LITE_SCHEMA) and not any(k in spec for k in VEGA_ONLY_TOP_LEVEL)


def test_every_fabric_app_target_is_vega_lite():
    """D-642: the Fabric App renders Vega-Lite only. Every idiom x notation profile the cockpit can ask for is
    Vega-Lite; an idiom Vega-Lite cannot draw is reported as not mappable, never emitted as full Vega or D3."""
    seen = 0
    for idiom in _implemented():
        for pid in render.target_profiles(idiom):
            if render.profile_def(pid).get("kind", "notation") != "notation":
                continue
            spec = json.loads(render.render_target(idiom, "fabric_app", pid)[0])["spec"]
            assert is_vega_lite(spec), f"{idiom}@{pid}: fabric_app target is not Vega-Lite"
            seen += 1
    assert seen >= 30, f"expected the Vega-Lite set under its notation profiles, got {seen}"


def test_vega_lite_check_rejects_full_vega():
    """Counter-check: a full-Vega spec (signals/marks at the top) and a v5 Vega schema fail the check."""
    assert not is_vega_lite({"$schema": "https://vega.github.io/schema/vega/v5.json", "marks": []})
    assert not is_vega_lite({"$schema": VEGA_LITE_SCHEMA + "v5.json", "signals": [], "mark": "bar"})
    assert is_vega_lite({"$schema": VEGA_LITE_SCHEMA + "v5.json", "mark": "bar"})


def test_fabric_app_targets_match_golden_and_are_idempotent():
    frozen = 0
    for idiom in _implemented():
        for pid in render.target_profiles(idiom):
            if render.profile_def(pid).get("kind", "notation") != "notation":
                continue
            out, _ = render.render_target(idiom, "fabric_app", pid)
            assert out == render.render_target(idiom, "fabric_app", pid)[0], f"{idiom}@{pid}: not idempotent"
            gp = render.target_golden_path(idiom, "fabric_app", pid)
            assert gp.exists(), f"freeze it: render.py write-targets {idiom}"
            assert out == gp.read_text(encoding="utf-8"), f"{idiom}@{pid}: fabric_app drifted from golden"
            doc = json.loads(out)
            assert doc["data_name"] == "dataset" and doc["spec"]["data"] == {"name": "dataset"}
            frozen += 1
    assert frozen >= 30, f"expected the Vega-Lite set under its notation profiles, got {frozen}"


def test_html_target_embeds_the_profile_config():
    for idiom in _implemented():
        for pid in render.target_profiles(idiom):
            spec = json.loads(render.render_target(idiom, "html_vegalite", pid)[0])
            assert spec["config"] == render.vegalite_config(pid), f"{idiom}@{pid}: config not embedded"


def test_every_idiom_rasterizes_under_every_profile():
    """The real gate: the Vega-Lite a Fabric App or an HTML page would receive draws, for
    every idiom x profile (style profiles included)."""
    pytest.importorskip("vl_convert")
    sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library" / "acceptance"))
    import render_acceptance  # noqa: E402
    import vl_convert as vlc  # noqa: E402

    drawn = 0
    for idiom in _implemented():
        for pid in render.target_profiles(idiom):
            spec = json.loads(render.render_target(idiom, "html_vegalite", pid)[0])
            spec = render_acceptance._sized_with_data(spec, render_acceptance._field_covering_sample())
            png = vlc.vegalite_to_png(spec, scale=1)
            assert png[:8] == b"\x89PNG\r\n\x1a\n" and len(png) > 1000, f"{idiom}@{pid}: drew nothing"
            drawn += 1
    assert drawn >= 90, f"expected every idiom x profile to draw, got {drawn}"


def test_dark_background_keeps_salience_and_contrast():
    """A-31 R6: the library's inks are chosen for light cards (#0F2430 measures 1.1:1 on the
    Fabric-App dark card #292929). `background=` maps each colour by salience (contrast.for_dark_ground):
    marks >= 3:1, text >= 4.5:1, gridlines stay quieter than the data, PY stays quieter than AC."""
    import contrast

    dark = "#292929"
    for idiom in ("line", "bar_ranking", "deviation_bar", "waterfall_pvm"):
        for pid in ("house_default", "ibcs", "editorial"):
            if pid not in render.target_profiles(idiom):
                continue
            light = json.loads(render.render_target(idiom, "fabric_app", pid)[0])
            doc = json.loads(render.render_target(idiom, "fabric_app", pid, background=dark)[0])
            assert light != doc, f"{idiom}@{pid}: nothing changed on a dark ground"
            assert '"white"' not in json.dumps(doc), f"{idiom}@{pid}: white hollow fill on a dark ground"
            for node, parent in _hex_literals(doc["spec"]) + _hex_literals(doc["configVegaLite"]):
                if parent == "gridColor" or (parent == "fill" and node == dark):
                    continue
                assert contrast.contrast_ratio(node, dark) >= 3.0, f"{idiom}@{pid}: {parent}={node}"
            for key in ("labelColor", "titleColor"):
                for node, parent in _hex_literals(doc["configVegaLite"]):
                    if parent == key:
                        assert contrast.contrast_ratio(node, dark) >= 4.5, f"{idiom}@{pid}: {key}={node}"


def test_dark_mapping_keeps_the_order_of_emphasis():
    """Measured 30.09.2026: lifting to a floor only made the #E1DFDD grid brighter than the data."""
    import contrast

    dark = "#292929"
    ink, grid = contrast.for_dark_ground("#0F2430", dark), contrast.for_dark_ground("#E1DFDD", dark)
    assert contrast.contrast_ratio(ink, dark) > 2 * contrast.contrast_ratio(grid, dark)
    ac = contrast.for_dark_ground("#404040", dark, min_ratio=3.0)
    py = contrast.for_dark_ground("#A0A0A0", dark, min_ratio=3.0)
    assert contrast.contrast_ratio(ac, dark) > contrast.contrast_ratio(py, dark), "PY louder than AC"
    red = contrast.hex_to_oklch(contrast.for_dark_ground("#A4262C", dark))[2]
    assert abs(red - contrast.hex_to_oklch("#A4262C")[2]) < 3.0


def _hex_literals(node, key=None):
    out = []
    if isinstance(node, dict):
        for k, v in node.items():
            out += _hex_literals(v, k)
    elif isinstance(node, list):
        for v in node:
            out += _hex_literals(v, key)
    elif isinstance(node, str) and len(node) == 7 and node.startswith("#"):
        out.append((node, key))
    return out
