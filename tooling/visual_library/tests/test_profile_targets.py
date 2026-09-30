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
