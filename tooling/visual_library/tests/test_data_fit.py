"""Tests for the data-fit + why-not layer: the anti-pattern catalog (_anti_patterns.yaml)
and the per-idiom data_fit contracts, plus resolve.check_fit / resolve.anti_patterns.

Governance guarantees:
- every anti_pattern tag any idiom uses is DEFINED once in the catalog (no opaque slugs);
- every data_fit bound references a real param, sane min<=max, and an existing on_violation;
- check_fit deterministically flags over/under-cardinality and type breaches, and names the
  governed anti_pattern that explains each (the agent-legible 'why not').
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import render  # noqa: E402
import resolve  # noqa: E402

LIB = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library"
_ALLOWED_TYPES = {"category", "quantitative", "temporal", "date"}


def _idiom_files() -> "list[str]":
    return [f for f in sorted(glob.glob(str(LIB / "*.yaml")))
            if not Path(f).name.startswith("_") and Path(f).name != "index.yaml"]


def _used_anti_patterns() -> set:
    used = set()
    for f in _idiom_files():
        d = yaml.safe_load(Path(f).read_text(encoding="utf-8"))
        if isinstance(d, dict):
            used.update(d.get("anti_patterns") or [])
    return used


def test_every_anti_pattern_is_catalogued_and_nothing_orphaned():
    cat = resolve.load_anti_patterns()
    used = _used_anti_patterns()
    missing = used - set(cat)
    assert not missing, f"anti_patterns used by an idiom but not defined in _anti_patterns.yaml: {sorted(missing)}"
    orphaned = set(cat) - used
    assert not orphaned, f"catalog defines unused anti_patterns (remove or reference them): {sorted(orphaned)}"


def test_catalog_entries_have_message_and_fix():
    for ap_id, d in resolve.load_anti_patterns().items():
        assert isinstance(d, dict), f"{ap_id}: not a mapping"
        assert d.get("message"), f"{ap_id}: missing message"
        assert d.get("fix"), f"{ap_id}: missing fix"
        fit = d.get("fit")
        if fit is not None:
            assert fit.get("role") and fit.get("rel"), f"{ap_id}: fit hint needs role + rel"


def test_data_fit_blocks_are_structurally_valid():
    cat = set(resolve.load_anti_patterns())
    seen = 0
    for iid in resolve._implemented():
        e = render.load_entry(iid)
        df = e.get("data_fit")
        if not df:
            continue
        seen += 1
        params = set((e.get("params") or {}).keys())
        for key, spec in df.items():
            assert key in params, f"{iid}: data_fit key '{key}' is not a declared param"
            assert isinstance(spec, dict), f"{iid}.{key}: spec must be a mapping"
            if "min" in spec and "max" in spec:
                assert spec["min"] <= spec["max"], f"{iid}.{key}: min>max"
            if spec.get("type"):
                assert spec["type"] in _ALLOWED_TYPES, f"{iid}.{key}: unknown type {spec['type']}"
            ov = spec.get("on_violation")
            if ov:
                assert ov in cat, f"{iid}.{key}: on_violation '{ov}' not in the anti-pattern catalog"
            # a real 'too many' ceiling (max > 1) must be explainable — carry an on_violation
            # reason; a single-measure requirement (max == 1) does not.
            if spec.get("max", 1) > 1 and not ov:
                raise AssertionError(f"{iid}.{key}: cardinality ceiling without an on_violation reason")
    assert seen >= 16, f"expected the cardinality-sensitive idioms to carry data_fit, got {seen}"


def test_known_cardinality_idioms_declare_data_fit():
    for iid in ("donut", "stacked_100", "small_multiples", "waterfall_pvm", "lollipop", "boxplot"):
        assert render.load_entry(iid).get("data_fit"), f"{iid}: expected a data_fit contract"


def test_check_fit_passes_within_bounds():
    r = resolve.check_fit("donut", {"category": 3, "value": 1})
    assert r["fit"] is True and r["violations"] == []
    assert set(r["checked"]) == {"category", "value"}


def test_check_fit_flags_max_with_the_governing_anti_pattern():
    r = resolve.check_fit("donut", {"category": 7})
    assert r["fit"] is False
    v = r["violations"][0]
    assert v["param"] == "category" and v["check"] == "max" and v["bound"] == 3 and v["actual"] == 7
    assert v["rule"] == "pie_or_donut_gt_4"
    assert v["message"] and v["fix"]  # resolved from the catalog
    assert "value" in r["unchecked"]  # not supplied -> unchecked, not failed


def test_donut_max_three_parts_ibcs_ex21():
    # IBCS 2.0 EX 2.1 (S. 136): not more than two or three values per pie; Gegenprobe 3 vs 4
    assert resolve.check_fit("donut", {"category": 3})["fit"] is True
    r = resolve.check_fit("donut", {"category": 4})
    assert r["fit"] is False and r["violations"][0]["rule"] == "pie_or_donut_gt_4"
    assert "<=3 parts" in resolve.DENY_VISUALTYPES["pieChart"]["use"]


def test_check_fit_flags_min_and_type():
    rmin = resolve.check_fit("donut", {"category": 1})
    assert rmin["fit"] is False and rmin["violations"][0]["check"] == "min"
    rtype = resolve.check_fit("histogram", {"measure": {"n": 1, "type": "category"}})
    assert rtype["fit"] is False and rtype["violations"][0]["check"] == "type"
    # date and temporal are interchangeable for a fit check
    assert resolve._norm_type("date") == resolve._norm_type("temporal") == "temporal"


def test_check_fit_ignores_unknown_params():
    r = resolve.check_fit("donut", {"not_a_param": 999})
    assert r["fit"] is True and "not_a_param" not in r["checked"]


def test_anti_patterns_resolve_to_catalog_entries():
    aps = resolve.anti_patterns("donut")
    ids = {a["id"] for a in aps}
    assert "pie_or_donut_gt_4" in ids
    for a in aps:
        assert a["message"] and a["fix"], f"{a['id']}: unresolved message/fix"


def test_idiom_card_carries_data_fit_and_resolved_anti_patterns():
    card = resolve._idiom_card("donut")
    assert card["data_fit"]["category"]["max"] == 3  # IBCS 2.0 EX 2.1, S. 136
    assert any(a["id"] == "pie_or_donut_gt_4" and a["message"] for a in card["anti_patterns"])
