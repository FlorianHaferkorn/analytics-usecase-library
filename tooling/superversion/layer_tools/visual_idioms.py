"""layer_tools.visual_idioms — bridge from the ALUCA visual_type vocabulary to the
evidence-based **idiom** library (`core/templates/page_templates/visual_library/`).

Two governed "visual libraries" exist, at different granularities:

  - `visual_registry.yaml` (via `visual_library.py`) says which pbip_types are ALLOWED
    for an information block — a *set*.
  - the idiom library (idiom YAMLs + frozen goldens) says which SPECIFIC native
    visualType a governed idiom PRODUCES — a *point*.

This module reconciles them for the PBIR emitter: for every chart visual_type the
emitter handles, the exact PBIR visualType in `pbir._PLANS` must equal the
`powerbi_native` visualType of the governed idiom it corresponds to — a tighter
authority than "is in the allowed set". Enforced by
`tests/test_visual_library.py::test_pbir_plans_match_governed_idiom_native_type`.

Pure data access (Invariant I2): reads the committed golden JSON, no engine, no render.
"""
from __future__ import annotations

import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_GOLDEN = _REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library" / "golden"

# ALUCA semantic visual_type → the governed idiom whose powerbi_native realization
# defines the emitted PBIR visualType. Chrome/containers with no analytical idiom
# (card/kpi_card → cardVisual, slicer, table/matrix → tableEx as a container) are
# listed in EXEMPT below rather than mapped to an idiom.
ALUCA_VISUAL_IDIOM: dict[str, str] = {
    "line_chart": "line",
    "trend_line": "line",
    "bar_chart": "bar_ranking",
    "bar_chart_horizontal": "bar_ranking",
    "waterfall": "waterfall_pvm",
}

# visual_types the emitter handles that are structural/chrome, not a charted idiom.
EXEMPT: frozenset[str] = frozenset({"card", "kpi_card", "slicer", "table", "matrix"})


class IdiomBridgeError(ValueError):
    """A mapped idiom has no powerbi_native golden to read the visualType from."""


def native_visual_type(idiom: str) -> str:
    """The PBIR ``visualType`` the governed idiom's frozen powerbi_native realization emits."""
    gp = _GOLDEN / f"{idiom}.powerbi_native.json"
    if not gp.exists():
        raise IdiomBridgeError(
            f"idiom '{idiom}' has no powerbi_native golden at {gp} — it is not native-capable, "
            f"so it cannot govern a PBIR visual_type mapping"
        )
    vt = json.loads(gp.read_text(encoding="utf-8")).get("visualType")
    if not vt:
        raise IdiomBridgeError(f"golden {gp.name} has no visualType")
    return vt


def sanctioned_visual_type(visual_type: str) -> str | None:
    """The exact PBIR visualType the idiom library governs for an ALUCA visual_type,
    or None for an exempt (chrome/container) type."""
    if visual_type in EXEMPT:
        return None
    idiom = ALUCA_VISUAL_IDIOM.get(visual_type)
    return native_visual_type(idiom) if idiom else None
