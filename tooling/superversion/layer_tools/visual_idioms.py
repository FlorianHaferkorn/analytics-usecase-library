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

Coverage: `idiom_native_types()` is DERIVED from `index.yaml.implemented` (not hand-listed),
so the governance/audit surface always covers the whole library. `ALUCA_VISUAL_IDIOM` (the
bracket-alias → idiom map) is intentionally narrower: it only lists visual_types the live
emitter's `_PLANS` actually supports today. The gap between the two is tracked, not silent
(see `PLANS_UNREACHABLE` + the reachability test) — new native visualTypes need their PBIR
roles from `powerbi-report-author catalog describe <type>` before they enter `_PLANS`, and are
NOT guessed here.

Pure data access (Invariant I2): reads the committed golden JSON + index.yaml, no engine.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[3]
_LIB = _REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library"
_GOLDEN = _LIB / "golden"

# ALUCA bracket visual_type → the governed idiom whose powerbi_native realization defines the
# emitted PBIR visualType. Only visual_types the emitter's _PLANS supports today (role-validated).
# `column_chart`/`column_time` → clusteredColumnChart is role-identical to `bar_chart` (orientation
# only), so it is safe to add without a fresh catalog lookup.
ALUCA_VISUAL_IDIOM: dict[str, str] = {
    "line_chart": "line",
    "trend_line": "line",
    "bar_chart": "bar_ranking",
    "bar_chart_horizontal": "bar_ranking",
    "column_chart": "column_time",
    "column_time": "column_time",
    "waterfall": "waterfall_pvm",
    # roles now wired in pbir._PLANS (derived from each idiom's governed native golden)
    "donut": "donut",
    "bar_stacked": "bar_stacked",
    "area_stacked": "area_stacked",
    "stacked_100": "stacked_100",
    "decomposition_tree": "decomposition_tree",
    "scatter": "scatter",
}

# visual_types the emitter handles that are structural/chrome, not a charted idiom.
EXEMPT: frozenset[str] = frozenset({"card", "kpi_card", "slicer", "table", "matrix"})

# Native-capable idioms whose visualType is NOT yet in pbir._PLANS. Every other native idiom's
# PBIR roles ARE wired into _PLANS, DERIVED FROM its governed native golden (not guessed) and
# bound to it by test_visual_library.test_pbir_plans_emit_the_governed_golden_roles. Native output
# remains Desktop-gated for the whole track (no headless PBIR renderer) — that is inherent, not a gap.
# The reachability test asserts this stays the exact tracked set.
#
# `kpi_card_spark` steht hier seit 08.09.2026, und zwar als Entscheidung und nicht als Rest:
# das Idiom emittiert seit ADR-0021 nativ ein `kpi`-Visual, aber der ALUCA-Typ `kpi_card` faehrt
# in _PLANS heute ein `cardVisual` (Rolle Data). Ein Umhaengen waere kein Bibliotheks-Detail — es
# aendert JEDE KPI-Karte in jedem erzeugten Report, und `kpi` verlangt zusaetzlich eine
# Ziel-Measure auf der Rolle `Goal`, die ein Bracket heute nicht liefern muss. Beides gehoert
# Flo und nicht einem Seiteneffekt. Bis dahin bleibt die native Spur in der Bibliothek
# vorhanden und aus dem Generator unerreichbar — benannt statt still.
PLANS_UNREACHABLE: frozenset[str] = frozenset({"kpi_card_spark"})


class IdiomBridgeError(ValueError):
    """A mapped idiom has no powerbi_native golden to read the visualType from."""


def _index() -> dict:
    return yaml.safe_load((_LIB / "index.yaml").read_text(encoding="utf-8"))


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


def idiom_native_types() -> dict[str, str]:
    """Every native-capable implemented idiom → its PBIR visualType, derived from the goldens
    (the whole-library coverage the resolver/audit uses, independent of _PLANS)."""
    out: dict[str, str] = {}
    for iid in _index().get("implemented", []):
        gp = _GOLDEN / f"{iid}.powerbi_native.json"
        if gp.exists():
            vt = json.loads(gp.read_text(encoding="utf-8")).get("visualType")
            if vt:
                out[iid] = vt
    return out


def best_idiom_for_purpose(purpose: str) -> str:
    """The governed best idiom for an analytical purpose (index.yaml chooser) — the seam a
    bracket should use (`analytical_purpose`) instead of hand-picking a PBIR-shaped visual_type."""
    purposes = _index().get("purposes", {})
    if purpose not in purposes:
        raise KeyError(f"unknown purpose '{purpose}'. Known: {sorted(purposes)}")
    return purposes[purpose]["best"].split("@", 1)[0]


def visual_type_for_purpose(purpose: str) -> "str | None":
    """The ALUCA visual_type a bracket's ``analytical_purpose`` resolves to: the purpose's governed
    best idiom mapped back to an EMITTABLE visual_type (present in pbir._PLANS via ALUCA_VISUAL_IDIOM),
    or None when the best idiom is not a native chart (svg-dax/table/card idioms) — then the caller
    falls back to a card. This is the reverse of ALUCA_VISUAL_IDIOM: the seam that lets a bracket ask
    for a PURPOSE instead of hand-picking a PBIR-shaped visual_type. Best-only (no candidate
    substitution) so the resolution is predictable and governance stays legible."""
    purposes = _index().get("purposes", {})
    p = purposes.get(purpose)
    if not p:
        return None
    idiom = p.get("best", "").split("@", 1)[0]
    rev: dict[str, str] = {}
    for vt, idi in ALUCA_VISUAL_IDIOM.items():
        rev.setdefault(idi, vt)  # first (canonical) visual_type key wins
    return rev.get(idiom)


def min_slot(idiom: str) -> "tuple[int, int]":
    """The idiom's governed minimum grid size (cols, rows) — the floor a page-template slot must
    satisfy. Read from the idiom YAML's `min_size` (grid units)."""
    e = yaml.safe_load((_LIB / f"{idiom}.yaml").read_text(encoding="utf-8"))
    ms = e.get("min_size") or {}
    return int(ms.get("cols", 0)), int(ms.get("rows", 0))


def sanctioned_visual_type(visual_type: str) -> "str | None":
    """The exact PBIR visualType the idiom library governs for an ALUCA visual_type,
    or None for an exempt (chrome/container) type."""
    if visual_type in EXEMPT:
        return None
    idiom = ALUCA_VISUAL_IDIOM.get(visual_type)
    return native_visual_type(idiom) if idiom else None
