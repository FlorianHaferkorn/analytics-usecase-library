"""Selection logic question -> purpose -> idiom, and binding real columns (A-31 R4).

`data_slots` declares which role each column param of the Vega-Lite track plays; `render.bind`
fills them from {role: column}; `resolve.choose` picks the governed idiom for a purpose among
those the data can fill. These tests prove the declarations are complete, binding reaches every
column of every profile, and the choice is deterministic and stays inside the purpose's list.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import render  # noqa: E402
import resolve  # noqa: E402

_COLUMN_PARAM = re.compile(r'"field"\s*:\s*"\{\{(\w+)\}\}"|datum\[\'\{\{(\w+)\}\}\'\]')


def _vega_idioms() -> list[str]:
    impl = yaml.safe_load((render.LIB / "index.yaml").read_text(encoding="utf-8"))["implemented"]
    return [i for i in impl if "deneb_vegalite" in render.tools(i)]


def _column_params(idiom: str) -> set[str]:
    entry = render.load_entry(idiom)
    out: set[str] = set()
    for prof in render.profiles(idiom):
        real = render._realization(entry, "deneb_vegalite", prof)
        if real and real.get("applicable", True):
            out |= {a or b for a, b in _COLUMN_PARAM.findall(real["template"])}
    return out


def test_every_vega_idiom_declares_its_data_slots():
    for idiom in _vega_idioms():
        slots = render.data_slots(idiom)
        assert slots, f"{idiom}: deneb_vegalite track without data_slots"
        for param, slot in slots.items():
            assert slot.get("role") in render.SLOT_ROLES, f"{idiom}.{param}: unknown role {slot.get('role')}"
        missing = _column_params(idiom) - set(slots)
        assert not missing, f"{idiom}: column params without a declared slot {sorted(missing)}"


def _derived(spec) -> set[str]:
    """Fields a spec computes itself (transform `as`, window/aggregate outputs)."""
    out: set[str] = set()
    def walk(n):
        if isinstance(n, dict):
            if isinstance(n.get("as"), str):
                out.add(n["as"])
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
    walk(spec.get("transform", []))
    for layer in spec.get("layer", []):
        out |= _derived(layer)
    return out


def _referenced(spec) -> set[str]:
    text = json.dumps(spec)
    return set(re.findall(r'"field": "([^"]+)"', text)) | set(re.findall(r"datum\[\'([^']+)\'\]", text)) \
        | set(re.findall(r"datum\.([A-Za-z_]\w*)", text))


def test_binding_reaches_every_column_under_every_profile():
    """After binding, every column the spec reads is either a bound column or one the spec
    derives itself — a hard-coded sample column would break on real data."""
    for idiom in _vega_idioms():
        columns = {s["role"]: f"col_{s['role']}" for s in render.data_slots(idiom).values()}
        for pid in render.target_profiles(idiom):
            spec = json.loads(render.render_target(idiom, "html_vegalite", pid, bindings=columns)[0])
            stray = _referenced(spec) - set(columns.values()) - _derived(spec)
            assert not stray, f"{idiom}@{pid}: reads columns that binding cannot reach {sorted(stray)}"


def test_missing_required_role_is_an_error():
    with pytest.raises(KeyError):
        render.bind("column_time", {"value": "Orders"})


def test_bound_spec_draws_with_real_column_names():
    vlc = pytest.importorskip("vl_convert")
    cols = {"value": "OTIF %", "time": "Monat", "plan": "Plan %"}
    rows = [{"OTIF %": v, "Monat": f"2026-0{i + 1}", "Plan %": 95} for i, v in enumerate([91.2, 90.4, 88.1])]
    for pid in ("house_default", "ibcs", "editorial"):
        spec = json.loads(render.render_target("line", "html_vegalite", pid, bindings=cols)[0])
        spec["data"] = {"values": rows}
        spec["width"], spec["height"] = 320, 200
        png = vlc.vegalite_to_png(spec, scale=1)
        assert len(png) > 1000, f"line@{pid} drew nothing with bound columns"


def test_polarity_param_flips_the_ibcs_rating():
    spec = json.loads(render.render_target("deviation_bar", "fabric_app", "ibcs",
                                           bindings={"variance": "Δ Kosten"}, params={"polarity": -1})[0])["spec"]
    calc = next(t["calculate"] for t in spec["transform"] if t.get("as") == "rating")
    assert "* -1" in calc and "Δ Kosten" in calc


def test_choose_stays_in_the_purpose_and_is_deterministic():
    idx = resolve._index()
    all_roles = set(render.SLOT_ROLES)
    for purpose, pur in idx["purposes"].items():
        allowed = {str(c).split("@")[0] for c in [pur.get("best")] + list(pur.get("candidates") or []) if c}
        for pid in ("house_default", "ibcs", "fluent"):
            got = resolve.choose(purpose, all_roles, pid)
            assert got == resolve.choose(purpose, all_roles, pid)
            if got:
                assert got["idiom"] in allowed, f"{purpose}@{pid}: chose {got['idiom']} outside the list"


def test_choose_respects_available_roles():
    assert resolve.choose("time_comparison", {"value", "time"}, "ibcs")["idiom"] == "line"
    assert resolve.choose("deviation_from_target", {"variance"}, "ibcs")["idiom"] == "deviation_bar"
    assert resolve.choose("contribution_to_change", {"step", "variance"}, "ibcs")["idiom"] == "waterfall_pvm"
    assert resolve.choose("time_comparison", set(), "house_default") is None
    with pytest.raises(KeyError):
        resolve.choose("no_such_purpose", {"value"})


def test_choose_never_collapses_a_dimension():
    """A list of causes (category + value) must not become a single bullet: every dimension
    role in the data has to be consumed by the chosen idiom, or the purpose has no answer."""
    assert resolve.choose("deviation_from_target", {"category", "value"}, "house_default") is None
    assert resolve.choose("deviation_from_target", {"value"}, "house_default")["idiom"] == "bullet"
    got = resolve.choose("compare_categories", {"category", "value"}, "ibcs")
    assert got and "category" in {s["role"] for s in render.data_slots(got["idiom"]).values()}


def test_column_names_vega_would_misread_are_refused():
    """A dot in a column name is a nested-field access in Vega-Lite: the bar silently vanishes
    (measured 30.09.2026, R3). bind() refuses such names instead of drawing nothing."""
    with pytest.raises(ValueError):
        render.bind("deviation_bar", {"variance": "Marge vs. PL"})
    assert render.bind("deviation_bar", {"variance": "Marge vs PL"}) == {"field": "Marge vs PL"}
