"""Tests for resolve.py — the Visual Library resolver (purpose selection + visual audit)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import render  # noqa: E402
import resolve  # noqa: E402


def test_every_purpose_resolves_to_an_implemented_best_idiom():
    impl = set(render.load_entry(i)["id"] for i in resolve._implemented())
    idx = resolve._index()
    for pid in idx["purposes"]:
        r = resolve.resolve_purpose(pid)
        assert r["best"]["id"] in impl, f"{pid}: best {r['best']['id']} not implemented"
        assert r["question"] and r["candidates"], f"{pid}: missing question/candidates"
        for card in r["candidates"]:
            assert card["id"] in impl, f"{pid}: candidate {card['id']} not implemented"
            assert card["min_size"], f"{pid}/{card['id']}: no resolved min_size"


def test_resolve_purpose_carries_native_type_and_grid_px():
    r = resolve.resolve_purpose("compare_categories")
    best = r["best"]
    assert best["id"] == "bar_ranking"
    assert best["native_visual_type"] == "clusteredBarChart"
    ms = best["min_size"]
    assert ms["cols"] >= 2 and ms["rows"] >= 2
    assert ms["px_production"][0] > ms["px_design_base"][0]  # scales up to 1920


def test_resolve_purpose_accepts_a_notation_profile():
    r = resolve.resolve_purpose("deviation_from_target", profile="print_safe")
    assert r["profile"] == "print_safe"


def test_unknown_purpose_and_profile_raise():
    import pytest
    with pytest.raises(KeyError):
        resolve.resolve_purpose("does_not_exist")
    with pytest.raises(KeyError):
        resolve.resolve_purpose("compare_categories", profile="nope")


def test_audit_governed_denied_and_ungoverned(tmp_path):
    # governed: a real native golden
    gov = REPO_ROOT / "core/templates/page_templates/visual_library/golden/bar_ranking.powerbi_native.json"
    r = resolve.audit_visual(str(gov))
    assert r["verdict"] == "governed" and "bar_ranking" in r["idioms"]

    # denied: a gauge (PBIR nests visualType under `visual`)
    g = tmp_path / "g.json"
    g.write_text(json.dumps({"visual": {"visualType": "gaugeVisual"}}), encoding="utf-8")
    r = resolve.audit_visual(str(g))
    assert r["verdict"] == "denied" and r["deny_rule"] == "gauge" and "bullet" in r["use_instead"]

    # ungoverned: a type not in the library and not denied
    t = tmp_path / "t.json"
    t.write_text(json.dumps({"visual": {"visualType": "treemap"}}), encoding="utf-8")
    r = resolve.audit_visual(str(t))
    assert r["verdict"] == "ungoverned"


def test_native_type_index_maps_types_to_idioms():
    idx = resolve.native_type_index()
    assert "clusteredBarChart" in idx and "bar_ranking" in idx["clusteredBarChart"]
    assert "waterfallChart" in idx and "lineChart" in idx


def test_idiom_card_surfaces_version_and_status():
    card = resolve._idiom_card("donut")
    assert card["version"] and card["status"] == "active"
    # a purpose resolution carries lifecycle on best + candidates
    r = resolve.resolve_purpose("part_to_whole")
    assert r["best"]["status"] in {"active", "experimental", "deprecated"}
    assert r["best"]["version"]
