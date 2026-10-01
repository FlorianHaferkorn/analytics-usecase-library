"""Zone vocabulary -> purpose (A-31 R5): page-template zones name WHAT they answer, not the chart.

`index.yaml` `zone_vocabulary` maps Meridian's zone tasks (`task_taxonomy`) and ALUCA's manifest
information blocks onto the purposes; the chart then comes from `resolve.choose`. These tests
prove the mapping is complete for both vocabularies, points only at known purposes, agrees with
the registry's idiom bridges, and that bracket slots stay inside what their block allows.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import resolve  # noqa: E402

PT = REPO_ROOT / "core" / "templates" / "page_templates"

# Munzner (2014) task set as used by Meridian's template.schema.json `task_taxonomy`. Meridian's
# own test compares its schema enum against the mirrored index.yaml, so drift shows on both sides.
MUNZNER_TASKS = {"summarize", "compare", "compare_to_target", "trend", "rank", "find_extremum",
                 "distribute", "correlate", "locate", "lookup", "decide", "audit", "comprehension"}

# Bracket slots whose visual_type is not an allowed visual of the slot's information block
# (measured 30.09.2026: 9 of 70 slots). A ratchet, not an exemption: a new mismatch fails, and a
# fixed one must leave this set. Fixing them is use-case content work (slot or chart), not R5.
KNOWN_SLOT_MISMATCHES = {
    ("COM-003_Customer_Value", "T1_Portfolio", "Main_3", "horizontal_bar_chart"),
    ("FIN-001_Cash_Liquidity_Performance", "T1_Trend", "Main_2", "waterfall_chart"),
    ("FIN-001_Cash_Liquidity_Performance", "T1_Trend", "Main_3", "waterfall_chart"),
    ("SCM-001_Inventory_Performance", "T1_Portfolio", "Main_2", "exception_table"),
    ("SCM-001_Inventory_Performance", "T1_Portfolio", "Main_3", "line_chart"),
    ("SCM-002_Supply_Reliability_OTIF", "T3_ProcessControl", "Main_2", "exception_table"),
    ("SCM-003_Forecast_vs_Actual", "T2_Comparative", "Main_2", "exception_table"),
    ("XD-002_Resource_Utilization", "T1_Portfolio", "Main_2", "exception_table"),
    ("COM-IND-R001_Basket_Category_CrossSell", "T1_Portfolio", "Main_3", "horizontal_bar_chart"),
}


def _vocab(kind: str) -> dict:
    return resolve._index()["zone_vocabulary"][kind]


def _registry_blocks() -> list[dict]:
    return yaml.safe_load((PT / "visual_registry.yaml").read_text(encoding="utf-8"))["information_blocks"]


def _manifest_slots() -> dict[str, dict[str, "str | None"]]:
    m = yaml.safe_load((PT / "template_manifest.yaml").read_text(encoding="utf-8"))
    out: dict[str, dict[str, "str | None"]] = {}
    for fam in m["page_families"]:
        for var in fam["variants"]:
            for s in (var.get("overview_slots") or []) + (var.get("detail_slots") or []):
                out.setdefault(var["variant_id"], {}).setdefault(s["slot_id"], s.get("information_block"))
    return out


def test_task_vocabulary_is_the_munzner_set():
    assert set(_vocab("tasks")) == MUNZNER_TASKS


def test_every_information_block_is_mapped():
    blocks = {b["block_id"] for b in _registry_blocks()}
    assert set(_vocab("information_blocks")) == blocks
    used = {b for slots in _manifest_slots().values() for b in slots.values() if b}
    assert used <= blocks, f"manifest names blocks the registry lacks: {sorted(used - blocks)}"


def test_mapped_purposes_exist_and_no_chart_zones_give_a_reason():
    purposes = set(resolve._index()["purposes"])
    for kind in resolve.ZONE_KINDS:
        for key, val in _vocab(kind).items():
            if isinstance(val, dict):
                assert set(val) == {"none"} and str(val["none"]).strip(), f"{kind}.{key}: no-chart without reason"
                assert resolve.zone_purposes(kind, key) == []
            else:
                assert val and set(val) <= purposes, f"{kind}.{key}: unknown purpose {set(val) - purposes}"


def test_registry_idiom_bridges_answer_their_block_purposes():
    """A block's bridged idiom must be a candidate of one of the block's purposes — otherwise the
    registry would place a chart that answers a different question than the zone asks."""
    idx = resolve._index()
    for block in _registry_blocks():
        cands: set[str] = set()
        for p in resolve.zone_purposes("information_blocks", block["block_id"]):
            pur = idx["purposes"][p]
            cands |= {str(c).split("@")[0] for c in [pur["best"]] + list(pur["candidates"])}
        for vis in block.get("allowed_visuals") or []:
            if vis.get("idiom"):
                assert vis["idiom"] in cands, f"{block['block_id']}.{vis['visual_id']} -> {vis['idiom']}"


def test_bracket_slots_stay_inside_their_block():
    allowed = {b["block_id"]: {v["visual_id"] for v in b.get("allowed_visuals") or []} for b in _registry_blocks()}
    slots = _manifest_slots()
    found = set()
    for path in sorted((REPO_ROOT / "core" / "usecases").rglob("UseCase_Bracket.yaml")):
        layout = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("ux_layout_rules") or {}
        for page in layout.values():
            if not isinstance(page, dict) or not page.get("template_variant"):
                continue
            var = page["template_variant"]
            items = [("KPI_Cards", page.get("component_3s"))] + [
                (s.get("slot_id"), s) for key in ("component_30s", "component_300s")
                for s in page.get(key) or [] if isinstance(s, dict)]
            for sid, slot in items:
                if not isinstance(slot, dict) or not slot.get("visual_type"):
                    continue
                block = slots.get(var, {}).get(sid)
                assert block, f"{path.parent.name}: slot {var}.{sid} has no information block in the manifest"
                if slot["visual_type"] not in allowed[block]:
                    found.add((path.parent.name, var, sid, slot["visual_type"]))
    assert found - KNOWN_SLOT_MISMATCHES == set(), "new slot/visual mismatches"
    assert KNOWN_SLOT_MISMATCHES - found == set(), "fixed mismatches must leave KNOWN_SLOT_MISMATCHES"


def test_choose_for_zone_walks_the_purposes_in_order():
    got = resolve.choose_for_zone("tasks", "trend", {"value", "time"}, "ibcs")
    assert got["purpose"] == "time_comparison" and got["idiom"] == "line"
    got = resolve.choose_for_zone("tasks", "comprehension", {"step", "variance"}, "ibcs")
    assert got["purpose"] == "contribution_to_change" and got["idiom"] == "waterfall_pvm"
    got = resolve.choose_for_zone("information_blocks", "variance_explanation", {"variance"}, "house_default")
    assert got["purpose"] == "deviation_from_target", "falls through to the second purpose"
    assert resolve.choose_for_zone("tasks", "decide", {"value"}, "ibcs") is None
    with pytest.raises(KeyError):
        resolve.zone_purposes("tasks", "no_such_task")
    with pytest.raises(KeyError):
        resolve.zone_purposes("zones", "trend")
