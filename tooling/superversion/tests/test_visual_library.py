"""Tests for the Visual-Library Layer-Tool (task I-5.1).

DoD: a standalone smoke (resolve registry → visual spec, without the ALUCA core)
AND an integrated check (the PBIR emitter only emits visuals the registry
sanctions for each visual's information block). "Visual-Typ fehlt → Katalog-Eintrag"
surfaces as a CatalogGap / non-zero resolve.
"""
from __future__ import annotations

import pytest

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
