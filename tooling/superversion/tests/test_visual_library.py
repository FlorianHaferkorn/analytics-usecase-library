"""Tests for the Visual-Library Layer-Tool (task I-5.1).

DoD: a standalone smoke (resolve registry → visual spec, without the ALUCA core)
AND an integrated check (the PBIR emitter only emits visuals the registry
sanctions for each visual's information block). "Visual-Typ fehlt → Katalog-Eintrag"
surfaces as a CatalogGap / non-zero resolve.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

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


def test_third_party_visual_is_rejected_at_load():
    """Doktrin: keine Fremd-Visuals. Erzwungen beim LADEN, nicht nur im Review.

    Bis 01.08.2026 fuehrte `visual_registry.yaml` zwei Eintraege mit
    `pbip_type: custom` — einer davon namentlich `"Enlighten Bullet Chart"`. Das
    Dataclass hatte dafuer ein reguläres Feld `custom_visual_name`, also war der
    Verstoss nicht nur moeglich, sondern vorgesehen.

    Fremd-Visuals kosten Lizenz, brauchen eine Org-Freigabe im Tenant, machen das
    Deliverable tool-abhaengig (Scope-Grenze: der Kunde installiert nichts) und
    aendern Export-/Print-/Mobile-Verhalten. Die Eskalation ist stattdessen
    `render_mode: svg_measure`, danach ein anderes Ziel-Tool.

    Dieser Test prueft den Waechter, nicht die Registry — eine gruene Registry
    beweist nicht, dass der Waechter feuert.
    """
    import textwrap

    import pytest

    from tooling.superversion.layer_tools.visual_library import (
        ThirdPartyVisualError, VisualLibrary)

    for verstoss in ('        custom_visual_name: "Some Marketplace Visual"\n', ""):
        yaml_text = textwrap.dedent("""\
            registry_version: "1.0.0"
            information_blocks:
              - block_id: probe
                purpose: "p"
                primary_layer: "3s"
                slot_compatibility: ["KPI_Cards"]
                page_types: ["T1"]
                allowed_visuals:
                  - visual_id: something
                    pbip_type: custom
            """) + verstoss
        path = Path(tempfile.mkdtemp()) / "visual_registry.yaml"
        path.write_text(yaml_text, encoding="utf-8")
        with pytest.raises(ThirdPartyVisualError) as exc:
            VisualLibrary.load(path)
        assert "probe" in str(exc.value) and "something" in str(exc.value)


def test_committed_registry_declares_no_third_party_visual():
    """Die eingecheckte Registry selbst ist frei von Fremd-Visuals."""
    from tooling.superversion.layer_tools.visual_library import VisualLibrary

    lib = VisualLibrary.load()
    for block in lib.blocks.values():
        for v in block.allowed_visuals:
            assert v.pbip_type != "custom", f"{block.block_id}/{v.visual_id}"
            assert v.render_mode in ("native", "svg_measure"), \
                f"{block.block_id}/{v.visual_id}: unbekannter render_mode '{v.render_mode}'"
