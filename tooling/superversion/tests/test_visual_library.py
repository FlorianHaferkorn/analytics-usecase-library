"""Tests for the Visual-Library Layer-Tool (task I-5.1).

DoD: a standalone smoke (resolve registry → visual spec, without the ALUCA core)
AND an integrated check (the PBIR emitter only emits visuals the registry
sanctions for each visual's information block). "Visual-Typ fehlt → Katalog-Eintrag"
surfaces as a CatalogGap / non-zero resolve.
"""
from __future__ import annotations

import pytest

from tooling.superversion.layer_tools import visual_idioms as vi
from tooling.superversion.layer_tools import visual_library as vl
from tooling.superversion.targets import pbir


# --- Standalone (Invariant I4: runs against the bare registry) -------------- #

def test_library_loads_blocks():
    lib = vl.VisualLibrary.load()
    assert lib.registry_version
    assert {"status_signal", "time_trend", "variance_explanation",
            "entity_ranking", "detail_matrix"} <= set(lib.blocks)


def test_block_describe_and_default():
    lib = vl.VisualLibrary.load()
    b = lib.block("status_signal")
    assert b.primary_layer == "3s"
    assert "KPI_Cards" in b.slot_compatibility
    assert b.default_visual().pbip_type == "cardVisual"
    assert "cardVisual" in b.allowed_pbip_types()
    # status_signal forbids gauge/pie/radar (evidence-based)
    assert {"gaugeVisual", "pieChart"} <= b.forbidden_pbip_types()


def test_resolve_slot_to_block():
    lib = vl.VisualLibrary.load()
    blocks = lib.blocks_for_slot("KPI_Cards")
    assert [b.block_id for b in blocks] == ["status_signal"]


def test_unknown_block_and_slot():
    lib = vl.VisualLibrary.load()
    with pytest.raises(vl.VisualLibraryError):
        lib.block("does_not_exist")
    assert lib.blocks_for_slot("NoSuchSlot") == []  # catalog gap → empty


def test_catalog_gap_when_block_has_no_visual():
    empty = vl.InformationBlock("x", "", "30s", [], [], allowed_visuals=[], forbidden_visuals=[])
    with pytest.raises(vl.CatalogGap):
        empty.default_visual()


def test_cli_list_and_resolve(capsys):
    assert vl.main(["list"]) == 0
    assert "blocks" in capsys.readouterr().out
    assert vl.main(["resolve", "KPI_Cards"]) == 0
    assert vl.main(["resolve", "NoSuchSlot"]) == 1   # catalog gap → non-zero


# --- Integrated with I-3.3 (PBIR emitter respects the library) -------------- #

def test_pbir_mapping_is_library_sanctioned():
    """Every official PBIR visualType the emitter maps an ALUCA visual_type to
    must be allowed by the registry for that visual's information block."""
    lib = vl.VisualLibrary.load()
    for aluca_type, plan in pbir._PLANS.items():
        block_id = lib.block_for_aluca_visual(aluca_type)
        if block_id is None:
            continue  # chrome/control (e.g. slicer) — no information block
        allowed = lib.block(block_id).allowed_pbip_types()
        assert plan.visual_type in allowed, (
            f"pbir maps {aluca_type} → {plan.visual_type}, not sanctioned by "
            f"block {block_id} (allowed: {sorted(allowed)})"
        )


def test_sanctions_helper():
    lib = vl.VisualLibrary.load()
    assert lib.sanctions("card", "cardVisual")
    assert not lib.sanctions("card", "pieChart")
    assert lib.sanctions("slicer", "anything")  # no block → exempt


# --- Integrated with the idiom library (the tighter, point-wise authority) --- #

def test_pbir_plans_match_governed_idiom_native_type():
    """The registry test above proves the emitted type is in the ALLOWED set. This is
    stronger: for every chart visual_type, the exact PBIR visualType in _PLANS must equal
    the powerbi_native visualType of the governed idiom — so the generator and the idiom
    library can never drift apart (the reconciliation the two 'visual libraries' needed)."""
    for aluca_type, idiom in vi.ALUCA_VISUAL_IDIOM.items():
        assert aluca_type in pbir._PLANS, f"idiom bridge maps {aluca_type} but _PLANS has no such type"
        assert pbir._PLANS[aluca_type].visual_type == vi.native_visual_type(idiom), (
            f"pbir emits {pbir._PLANS[aluca_type].visual_type} for {aluca_type}, but the governed "
            f"idiom '{idiom}' produces {vi.native_visual_type(idiom)}"
        )


def test_every_plan_is_idiom_governed_or_exempt():
    """No chart type may silently escape idiom governance: every _PLANS key is either bridged
    to a governed idiom or explicitly exempt (chrome/container)."""
    for aluca_type in pbir._PLANS:
        assert aluca_type in vi.ALUCA_VISUAL_IDIOM or aluca_type in vi.EXEMPT, (
            f"_PLANS type '{aluca_type}' is neither idiom-governed nor listed EXEMPT in visual_idioms"
        )


def test_idiom_bridge_agrees_with_registry():
    """The two authorities are consistent: the idiom-governed visualType is also in the
    registry's allowed set for that visual_type's block."""
    lib = vl.VisualLibrary.load()
    for aluca_type, idiom in vi.ALUCA_VISUAL_IDIOM.items():
        block_id = lib.block_for_aluca_visual(aluca_type)
        if block_id is None:
            continue
        assert vi.native_visual_type(idiom) in lib.block(block_id).allowed_pbip_types()


def test_native_visual_type_rejects_non_native_idiom():
    with pytest.raises(vi.IdiomBridgeError):
        vi.native_visual_type("lollipop")  # lollipop has no powerbi_native realization


def test_idiom_native_types_are_derived_from_the_whole_library():
    """Coverage is index.yaml-derived, not hand-listed: every native-capable idiom appears."""
    nt = vi.idiom_native_types()
    assert nt["bar_ranking"] == "clusteredBarChart"
    assert nt["column_time"] == "clusteredColumnChart"
    assert nt["donut"] == "donutChart" and nt["scatter"] == "scatterChart"
    assert len(nt) >= 17  # 17 native-capable idioms today


def test_native_idioms_are_reachable_via_plans_or_explicitly_tracked():
    """Every native-capable idiom is either emittable via _PLANS today, or in the tracked
    PLANS_UNREACHABLE set (needs catalog-validated PBIR roles). No silent third case."""
    emitted_types = {p.visual_type for p in pbir._PLANS.values()}
    reachable, gap = set(), set()
    for iid, vt in vi.idiom_native_types().items():
        (reachable if vt in emitted_types else gap).add(iid)
    assert gap == set(vi.PLANS_UNREACHABLE), (
        f"reachability drifted — unreachable now {sorted(gap)}, tracked {sorted(vi.PLANS_UNREACHABLE)}; "
        "add catalog-validated _PLANS roles then update PLANS_UNREACHABLE"
    )
    assert {"line", "bar_ranking", "column_time", "waterfall_pvm", "matrix_evidence"} <= reachable


def test_min_slot_and_purpose_helpers():
    """The generator seam can consult the grid floor and resolve a purpose to its best idiom."""
    cols, rows = vi.min_slot("bar_ranking")
    assert cols >= 2 and rows >= 2
    assert vi.best_idiom_for_purpose("compare_categories") == "bar_ranking"
    with pytest.raises(KeyError):
        vi.best_idiom_for_purpose("nope")


def test_pbir_plans_emit_the_governed_golden_roles():
    """Stronger than the visualType check: every bridged chart's _PLANS roles (primary + dim roles
    + optional secondary measure axis) equal the DATA-ROLE projections of the governed native
    golden — so the generator emits exactly the governed reference's role shape and cannot drift.
    Non-projection queryState keys (e.g. sortDefinition) are chrome, not data roles, and excluded."""
    import json
    from pathlib import Path
    golden_dir = Path(__file__).resolve().parents[3] / "core/templates/page_templates/visual_library/golden"
    for aluca_type, idiom in vi.ALUCA_VISUAL_IDIOM.items():
        d = json.loads((golden_dir / f"{idiom}.powerbi_native.json").read_text(encoding="utf-8"))
        golden_roles = {k for k, v in d["query"]["queryState"].items()
                        if isinstance(v, dict) and v.get("projections")}
        plan = pbir._PLANS[aluca_type]
        plan_roles = {plan.primary_role, *plan.dim_roles}
        if plan.secondary_role:
            plan_roles.add(plan.secondary_role)
        assert plan_roles == golden_roles, (
            f"{aluca_type}→{idiom}: _PLANS roles {sorted(plan_roles)} != "
            f"golden data roles {sorted(golden_roles)}"
        )


def test_visual_type_for_purpose_resolves_best_native_idiom():
    """analytical_purpose seam: a purpose resolves to its best idiom's emittable visual_type, or
    None (→ card) when the best idiom is non-native (svg-dax/table/card)."""
    cases = {
        "time_comparison": "line_chart", "compare_categories": "bar_chart",
        "part_to_whole": "donut", "correlation": "scatter",
        "contribution_to_change": "waterfall", "driver_breakdown": "decomposition_tree",
    }
    for purpose, vt in cases.items():
        got = vi.visual_type_for_purpose(purpose)
        assert got == vt, f"{purpose} -> {got}, expected {vt}"
        assert got in pbir._PLANS, f"{purpose} resolved to non-emittable {got}"
    assert vi.visual_type_for_purpose("value_verdict") is None   # best = kpi_card_spark (non-native)
    assert vi.visual_type_for_purpose("does_not_exist") is None
