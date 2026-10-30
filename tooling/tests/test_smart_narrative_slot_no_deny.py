"""Der Slot `Smart_Narrative` rendert nie das deny-gelistete smartNarrativeVisual.

Quelle der Deny-Liste: core/templates/page_templates/visual_library/index.yaml
(`powerbi_smart_narrative`). Der Slot-Name bleibt als Ablagekonvention (Umbenennung:
58 Dateien + 19 dist-Reports, offen im Ledger); sein Inhalt ist Kontexttext.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from products.fabric.powerbi.tooling.adapters.pbip import (
    _VISUAL_TYPE_MAP,
    _build_visual_json,
)
from tooling.generator_core.ir.specs import (
    Binding,
    PageRole,
    Position,
    VisualSpec,
    VisualType,
)

ROOT = Path(__file__).resolve().parents[2]
PT = ROOT / "core" / "templates" / "page_templates"


def _deny() -> list[str]:
    idx = yaml.safe_load((PT / "visual_library" / "index.yaml").read_text(encoding="utf-8"))
    return list(idx["deny"])


def test_deny_list_carries_smart_narrative() -> None:
    assert "powerbi_smart_narrative" in _deny()


def test_ir_adapter_emits_textbox_for_smart_narrative() -> None:
    vspec = VisualSpec(
        id="Smart_Narrative",
        visual_type=VisualType.SMART_NARRATIVE,
        page_role=PageRole.DETAIL,
        position=Position(0.165, 0.0, 0.55, 0.18),
        binding=Binding(),
    )
    out = _build_visual_json(vspec)
    assert out["visual"]["visualType"] == "textbox"
    assert "smartNarrativeVisual" not in json.dumps(out)


def test_adapter_map_has_no_smart_narrative_visual() -> None:
    assert all("smartNarrativeVisual" not in v for v in _VISUAL_TYPE_MAP.values())


def test_grid_templates_hint_no_smart_narrative_visual() -> None:
    checked = 0
    for p in sorted((PT / "grid_templates").glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        for slot in data.get("slots", []):
            if slot.get("slot_id") == "Smart_Narrative":
                checked += 1
                assert slot.get("visual_type_hint") == "textbox", p.name
    vt = json.loads((PT / "visual_templates" / "smart_narrative.json").read_text(encoding="utf-8"))
    assert vt["visual_type"] == "textbox"
    assert checked >= 1, "kein Smart_Narrative-Slot in grid_templates gelesen"
