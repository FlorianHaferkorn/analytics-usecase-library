"""Golden + determinism tests for the ALUCA Visual Library.

Guarantees the target: the same request yields the same result every time.
- byte-for-byte: each idiom x tool renders exactly its frozen golden.
- idempotent: rendering twice returns identical bytes.
- valid + fully filled: JSON tools parse; no unfilled {{...}} placeholders remain.
- schema: every idiom carries the required keys; index `implemented` files exist.
- render-valid: every Deneb/Vega-Lite golden COMPILES as Vega-Lite (not just parses).
- render-real: every Deneb golden RASTERIZES to a non-trivial PNG via vl-convert (a true render,
  not a compile — caught the lollipop x/x2 bug). Skips where vl-convert is absent.
- structural: native fragments carry visualType + projections; SVG-DAX emits a balanced
  <svg> data URI; Recharts JSX has a known, closed chart root (full render stays runtime-gated).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import render  # noqa: E402

LIB = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library"


def _index() -> dict:
    return yaml.safe_load((LIB / "index.yaml").read_text(encoding="utf-8"))


def _implemented() -> "list[str]":
    return _index().get("implemented", [])


def test_index_implemented_entries_exist_and_have_required_keys():
    schema = yaml.safe_load((LIB / "_schema.yaml").read_text(encoding="utf-8"))
    for idiom in _implemented():
        entry = render.load_entry(idiom)  # raises if a required key is missing
        assert entry["id"] == idiom
        for key in schema["required_keys"]:
            assert key in entry, f"{idiom} missing {key}"
        # every governed tool track is ADDRESSED: either a runnable template,
        # or an explicit applicable:false with a reason + a recommended fallback.
        for tool in schema["tools"]:
            r = entry["realizations"].get(tool)
            assert r is not None, f"{idiom} does not address tool {tool}"
            if r.get("applicable", True):
                assert "template" in r and "ext" in r, f"{idiom}.{tool} applicable but no template/ext"
            else:
                assert r.get("reason") and r.get("use"), f"{idiom}.{tool} n/a needs reason + use"


def test_every_realization_matches_its_golden_byte_for_byte():
    for idiom in _implemented():
        for tool in render.tools(idiom):
            out, ext = render.render(idiom, tool)
            gp = render.golden_path(idiom, tool, ext)
            assert gp.exists(), f"missing golden {gp.name} (run: render.py write {idiom})"
            assert out == gp.read_text(encoding="utf-8"), f"{idiom}.{tool} drifted from its golden"


def test_render_is_idempotent():
    for idiom in _implemented():
        for tool in render.tools(idiom):
            assert render.render(idiom, tool)[0] == render.render(idiom, tool)[0]


def test_no_unfilled_placeholders_and_json_is_valid():
    for idiom in _implemented():
        for tool in render.tools(idiom):
            out, ext = render.render(idiom, tool)
            assert "{{" not in out and "}}" not in out, f"{idiom}.{tool} has an unfilled placeholder"
            if ext == "json":
                json.loads(out)  # raises on invalid JSON


def test_declared_profiles_are_registered_and_addressed():
    """Every notation profile an idiom opts into must exist in _notation_profiles.yaml,
    and any per-tool override must be a runnable template OR an applicable:false+reason."""
    reg = yaml.safe_load((LIB / "_notation_profiles.yaml").read_text(encoding="utf-8"))["profiles"]
    for idiom in _implemented():
        entry = render.load_entry(idiom)
        for pid, pdef in (entry.get("profiles") or {}).items():
            assert pid in reg, f"{idiom} declares unregistered profile '{pid}'"
            for tool, r in (pdef.get("realizations") or {}).items():
                if r.get("applicable", True):
                    assert "template" in r and "ext" in r, f"{idiom}@{pid}.{tool} applicable but no template/ext"
                else:
                    assert r.get("reason") and r.get("use"), f"{idiom}@{pid}.{tool} n/a needs reason + use"


def test_non_default_profiles_render_match_golden_and_are_valid():
    """The determinism guarantee extends to every idiom x tool x profile: byte-for-byte
    against a frozen golden, idempotent, fully filled, and valid JSON where applicable."""
    dp = render.default_profile()
    for idiom in _implemented():
        for profile in render.profiles(idiom):
            if profile == dp:
                continue  # baseline is covered by the tests above
            for tool in render.tools(idiom, profile):
                out, ext = render.render(idiom, tool, profile)
                assert "{{" not in out and "}}" not in out, f"{idiom}@{profile}.{tool} unfilled placeholder"
                gp = render.golden_path(idiom, tool, ext, profile)
                assert gp.exists(), f"missing golden {gp.name} (run: render.py write {idiom})"
                assert out == gp.read_text(encoding="utf-8"), f"{idiom}@{profile}.{tool} drifted from its golden"
                assert render.render(idiom, tool, profile)[0] == out, f"{idiom}@{profile}.{tool} not idempotent"
                if ext == "json":
                    json.loads(out)


def test_house_default_profile_output_is_the_base_realization():
    """house_default must be byte-identical to the plain 2-arg render (no accidental drift
    from introducing the axis) — the baseline goldens keep their unsuffixed filenames."""
    for idiom in _implemented():
        for tool in render.tools(idiom):
            assert render.render(idiom, tool)[0] == render.render(idiom, tool, render.default_profile())[0]


def test_docs_render_matches_golden_and_idempotent():
    """The generated Part D + HTML are pure functions of the library (SoT closes the loop)."""
    import render_docs  # noqa: E402  (tooling/visual_library already on sys.path)
    md = render_docs.render_part_d()
    assert md == render_docs.render_part_d(), "Part D render is not idempotent"
    golden = REPO_ROOT / "tooling" / "visual_library" / "tests" / "golden_docs" / "Part_D.md"
    assert golden.exists(), "freeze it: render_docs.py md > tests/golden_docs/Part_D.md"
    assert md == golden.read_text(encoding="utf-8"), "Part D drifted from the library — regenerate the docs"
    assert render_docs.render_artifact_html() == render_docs.render_artifact_html(), "HTML render not idempotent"


def test_deneb_goldens_compile_as_valid_vega_lite():
    """Render-validation, not just determinism: every Deneb/Vega-Lite golden must
    COMPILE as a valid Vega-Lite spec (catches structurally-wrong specs that still
    parse as JSON and pass the byte-for-byte test). Skips cleanly where altair is
    not installed (e.g. a minimal CI image)."""
    alt = pytest.importorskip("altair")
    specs = sorted((LIB / "golden").glob("*.deneb_vegalite*.json"))
    assert specs, "no deneb_vegalite goldens found"
    for gp in specs:
        spec = json.loads(gp.read_text(encoding="utf-8"))
        try:
            alt.Chart.from_dict(spec, validate=True).to_dict(validate=True)
        except Exception as e:  # noqa: BLE001 - surface which spec + first error line
            raise AssertionError(
                f"{gp.name} is not a valid Vega-Lite spec: {str(e).splitlines()[0]}"
            ) from None


def test_native_goldens_have_pbir_structure():
    """Structural contract for Power BI native fragments (a full Desktop load stays
    Desktop-gated): each carries a non-empty visualType and a query.queryState with
    at least one projection."""
    for gp in sorted((LIB / "golden").glob("*.powerbi_native*.json")):
        d = json.loads(gp.read_text(encoding="utf-8"))
        assert d.get("visualType"), f"{gp.name}: missing visualType"
        qs = d.get("query", {}).get("queryState", {})
        proj = sum(len(b.get("projections", [])) for b in qs.values() if isinstance(b, dict))
        assert proj >= 1, f"{gp.name}: query.queryState has no projections"


def test_svg_dax_goldens_emit_wellformed_svg():
    """SVG-DAX measures must build a data-URI SVG with a balanced <svg>..</svg> and
    even-quoted DAX strings (DAX-engine evaluation stays Desktop-gated)."""
    for gp in sorted((LIB / "golden").glob("*.powerbi_svg_dax*.dax")):
        t = gp.read_text(encoding="utf-8")
        assert "data:image/svg+xml" in t, f"{gp.name}: no SVG data URI"
        assert t.count("<svg") == t.count("</svg>") >= 1, f"{gp.name}: unbalanced <svg>..</svg>"
        assert t.count('"') % 2 == 0, f"{gp.name}: odd number of DAX double-quotes (unterminated string)"


_RECHARTS_ROOTS = {"AreaChart", "BarChart", "ComposedChart", "LineChart",
                   "PieChart", "Sankey", "ScatterChart"}


def test_recharts_goldens_are_structurally_closed():
    """Recharts JSX goldens: a known chart root, properly closed, with balanced braces
    and parens (a full React render stays runtime-gated)."""
    for gp in sorted((LIB / "golden").glob("*.web_recharts*.jsx")):
        t = gp.read_text(encoding="utf-8").strip()
        m = re.match(r"<([A-Za-z]+)", t)
        assert m, f"{gp.name}: does not start with a JSX element"
        root = m.group(1)
        assert root in _RECHARTS_ROOTS, f"{gp.name}: unknown Recharts root <{root}> (extend _RECHARTS_ROOTS if intended)"
        closed = f"</{root}>" in t or t.endswith("/>")  # container or self-closing (e.g. <Sankey .../>)
        assert closed, f"{gp.name}: root <{root}> is not closed"
        assert t.count("{") == t.count("}"), f"{gp.name}: unbalanced braces"
        assert t.count("(") == t.count(")"), f"{gp.name}: unbalanced parens"


def test_deneb_goldens_rasterize_to_png():
    """The strongest Deneb gate: every golden must actually RASTERIZE to a non-trivial PNG via
    vl-convert — a real render, not just a schema-valid compile. This is what caught the lollipop
    x/x2 bug that `to_dict(validate=True)` passed. Skips where vl-convert isn't installed."""
    pytest.importorskip("vl_convert")
    sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library" / "acceptance"))
    import render_acceptance  # noqa: E402

    dp = render.default_profile()
    rendered = 0
    for idiom in _implemented():
        for profile in render.profiles(idiom):
            if "deneb_vegalite" not in render.tools(idiom, profile):
                continue
            png = render_acceptance.render_deneb_png(idiom, None if profile == dp else profile)
            tag = idiom if profile == dp else f"{idiom}@{profile}"
            assert png[:8] == b"\x89PNG\r\n\x1a\n", f"{tag}: not a PNG"
            assert len(png) > 1000, f"{tag}: PNG is trivially empty ({len(png)} bytes) — spec drew nothing"
            rendered += 1
    assert rendered >= 20, f"expected the full Deneb set to render, got {rendered}"


def test_svg_dax_goldens_rasterize_to_png():
    """The svg_dax ARTEFACT is the SVG string the measure emits; every svg_dax golden must
    rasterize that SVG (representative values) to a real PNG via vl-convert. The DAX-computed
    values stay engine-gated (dax_udf/validate/acceptance.dax); this proves the emitted SVG
    renders. Skips where vl-convert isn't installed."""
    pytest.importorskip("vl_convert")
    sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library" / "acceptance"))
    import render_acceptance  # noqa: E402

    dp = render.default_profile()
    rendered = 0
    for idiom in _implemented():
        for profile in render.profiles(idiom):
            if "powerbi_svg_dax" not in render.tools(idiom, profile):
                continue
            png = render_acceptance.render_svg_dax_png(idiom, None if profile == dp else profile)
            tag = idiom if profile == dp else f"{idiom}@{profile}"
            assert png[:8] == b"\x89PNG\r\n\x1a\n", f"{tag}: emitted SVG did not rasterize"
            assert len(png) > 200, f"{tag}: PNG trivially empty ({len(png)} bytes)"
            rendered += 1
    assert rendered >= 9, f"expected every svg_dax golden to rasterize, got {rendered}"


def test_acceptance_materialize_writes_one_artifact_per_tool(tmp_path):
    """The acceptance generator must produce a runnable artifact for every tool track."""
    pytest.importorskip("vl_convert")
    sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library" / "acceptance"))
    import render_acceptance  # noqa: E402

    manifest = render_acceptance.materialize(tmp_path)
    for tool in ("deneb_vegalite", "powerbi_native", "powerbi_svg_dax", "web_recharts"):
        assert tool in manifest["artifacts"], f"materialize skipped {tool}"
    assert manifest["artifacts"]["deneb_vegalite"]["rendered_png"] >= 20
    assert (tmp_path / manifest["artifacts"]["powerbi_native"]["file"]).exists()
    assert (tmp_path / manifest["artifacts"]["web_recharts"]["file"]).exists()


def test_deneb_renders_across_all_scenarios():
    """'Proven in variable scenarios': every Deneb realization must rasterize under EVERY data
    scenario (positive, negatives, single/many categories, extremes), not just one sample."""
    pytest.importorskip("vl_convert")
    sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library" / "acceptance"))
    import render_acceptance  # noqa: E402

    dp = render.default_profile()
    checked = 0
    for idiom in _implemented():
        for profile in render.profiles(idiom):
            if "deneb_vegalite" not in render.tools(idiom, profile):
                continue
            results = render_acceptance.render_deneb_scenarios(idiom, None if profile == dp else profile)
            assert set(results) == set(render_acceptance.SCENARIOS), f"{idiom}@{profile}: scenario set mismatch"
            failed = [s for s, ok in results.items() if not ok]
            tag = idiom if profile == dp else f"{idiom}@{profile}"
            assert not failed, f"{tag}: did not render under scenarios {failed}"
            checked += 1
    assert checked >= 20, f"expected the full Deneb set across scenarios, got {checked}"


def test_frozen_validation_matrix_is_current():
    """The committed validation_matrix.json (read by the doc generator) must match a fresh
    re-derivation — so the artifact's 'proven vs gated' claims can never quietly go stale."""
    pytest.importorskip("vl_convert")
    sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library" / "acceptance"))
    import render_acceptance  # noqa: E402

    assert render_acceptance.compute_validation_matrix() == render_acceptance.load_matrix(), (
        "validation_matrix.json is stale — re-freeze with `render_acceptance.py matrix`"
    )
