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
    "horizontal_bar_chart": "bar_ranking",
    "horizontal_bar_categorical": "bar_ranking",
    "variance_bar": "bar_ranking",
    "column_chart": "column_time",
    "column_time": "column_time",
    "waterfall": "waterfall_pvm",
    "waterfall_chart": "waterfall_pvm",
    # roles now wired in pbir._PLANS (derived from each idiom's governed native golden)
    "donut": "donut",
    "bar_stacked": "bar_stacked",
    "area_stacked": "area_stacked",
    "stacked_100": "stacked_100",
    "decomposition_tree": "decomposition_tree",
    "scatter": "scatter",
    # 09.09.2026: die native KPI-Karte ist erreichbar, aber nur unter EIGENEM Typ. `kpi_card`
    # bleibt `cardVisual` — Begruendung und Zahlen stehen bei `_PLANS` in targets/pbir.py.
    "kpi_card_native": "kpi_card_spark",
}

# visual_types the emitter handles that are structural/chrome, not a charted idiom.
EXEMPT: frozenset[str] = frozenset({
    "card", "kpi_card", "kpi_card_with_delta", "slicer", "table", "matrix",
    "exception_table",
})

# Native-capable idioms whose visualType is NOT yet in pbir._PLANS. Every other native idiom's
# PBIR roles ARE wired into _PLANS, DERIVED FROM its governed native golden (not guessed) and
# bound to it by test_visual_library.test_pbir_plans_emit_the_governed_golden_roles. Native output
# remains Desktop-gated for the whole track (no headless PBIR renderer) — that is inherent, not a gap.
# The reachability test asserts this stays the exact tracked set.
#
# `kpi_card_spark` stand hier vom 08. bis zum 09.09.2026 und ist jetzt erreichbar — aber ueber
# einen EIGENEN visual_type `kpi_card_native`, nicht durch Umhaengen von `kpi_card`.
#
# Der Unterschied ist gemessen und nicht vorsichtshalber gewaehlt. Das `kpi`-Visual zeichnet Ist
# gegen Ziel; ohne Measure auf der Rolle `Goal` ist es die schlechtere Karte. Gezaehlt am
# 09.09.2026 ueber alle Brackets: 21 KPI-Karten (12 `vs_target`, 8 `vs_plan`, 1 `vs_py`).
# Gegengeprueft an allen 230 Measure-Namen aller TMDL-Modelle des Repos: fuer **0 von 21**
# existiert eine Ziel-Measure. Es gibt genau eine Plan-Measure ueberhaupt (`Plan Sales Amount`),
# und keine der 21 KPIs zeigt auf sie. Ein pauschaler Umzug haette 21 Karten mit leerer
# Ziel-Rolle erzeugt.
#
# Deshalb: die Spur ist gebaut und erreichbar, das Umschalten ist eine Bracket-Entscheidung je
# Karte, und sie setzt eine existierende Ziel-Measure voraus. Der Emitter prueft das und faellt
# sonst mit vermerkter Luecke auf `cardVisual` zurueck (`_goal_gap` in targets/pbir.py).
PLANS_UNREACHABLE: frozenset[str] = frozenset()

# Emittierbar, aber nur auf ausdrueckliche Nennung — nicht ueber den Zweck-Resolver.
#
# `kpi_card_spark` steht hier, weil das `kpi`-Visual eine Ziel-Measure verlangt, die im
# Bestand fuer keine der 21 KPI-Karten existiert (gezaehlt 09.09.2026, Begruendung bei
# `_PLANS` in targets/pbir.py). Ein Bracket bekommt die native Karte, indem es
# `visual_type: kpi_card_native` schreibt — und traegt damit die Verantwortung, eine
# Ziel-Measure zu liefern.
#
# Der Grund, warum diese Liste ueberhaupt existiert, ist ein Befund und keine Vorsicht:
# als das Idiom emittierbar wurde, aenderte `visual_type_for_purpose` ohne eigene
# Aenderung sein Ergebnis — `value_verdict` loeste ploetzlich auf `kpi_card_native` auf,
# und damit haette jedes Bracket, das einen ZWECK statt eines visual_type nennt, die
# native Karte bekommen. Genau der pauschale Umzug, gegen den die Zahlen stehen.
# Gefunden hat das nicht ein Gedanke, sondern ein bestehender Test.
#
# Die Lehre darueber hinaus: einen Typ erreichbar zu machen, macht ihn ueber JEDEN Umweg
# erreichbar, der auf Erreichbarkeit prueft. Wer eine Spur oeffnet, zaehlt ihre Eingaenge.
OPT_IN_ONLY: frozenset[str] = frozenset({"kpi_card_spark"})


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
    if idiom in OPT_IN_ONLY:
        return None                      # Zweck-Umweg liefert ihn nicht; der Fallback traegt
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


def canonical_params(idiom: str) -> dict:
    """Frozen connector-neutral parameters of a governed visual idiom.

    These parameters are the library's reusable binding contract (for example
    the single supporting measure required by a native PVM waterfall), not
    report-specific sample data.
    """
    entry = yaml.safe_load((_LIB / f"{idiom}.yaml").read_text(encoding="utf-8")) or {}
    return dict(entry.get("canonical_params") or {})


def sanctioned_visual_type(visual_type: str) -> "str | None":
    """The exact PBIR visualType the idiom library governs for an ALUCA visual_type,
    or None for an exempt (chrome/container) type."""
    if visual_type in EXEMPT:
        return None
    idiom = ALUCA_VISUAL_IDIOM.get(visual_type)
    return native_visual_type(idiom) if idiom else None


def category_axis_type(visual_type: str) -> "str | None":
    """The governed ``params.category.type`` of the idiom behind an ALUCA ``visual_type``
    (``"date"`` for the line idioms, ``"category"`` for rankings), or None when the visual_type
    maps to no charted idiom or the idiom declares no category axis.

    Read by the contract binding (``tooling/superversion/contract_binding.py``): only a
    ``date`` axis can be filled from the data contract without a business choice — the
    contract names exactly one date column per date dimension, whereas *which* category a
    ranking groups by is the bracket's decision and stays a HITL placeholder."""
    idiom = ALUCA_VISUAL_IDIOM.get((visual_type or "").strip().lower())
    if not idiom:
        return None
    entry = yaml.safe_load((_LIB / f"{idiom}.yaml").read_text(encoding="utf-8")) or {}
    category = (entry.get("params") or {}).get("category")
    if not isinstance(category, dict):
        return None
    return category.get("type")
