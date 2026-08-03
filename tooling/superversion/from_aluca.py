"""from_aluca — Source-Adapter: ALUCA UseCase-Bracket + KPI-Katalog → kanonisches Modell.

Dies ist der KERN der Superversion (PRODUCT_PLAN.md §0/§6, Phase 0/1): er dockt ALUCAs
Bedeutungs-/Visual-Schicht (Brackets, golden_20, KPI-Definitionen, 3-30-300-Layout) an
Meridians kanonischen Modell-Vertrag (`core.pbi_engine.model.CanonicalModel`) an —
gleichrangig neben `from_pbip` (Brownfield), `from_spec` (Greenfield), Meridian-Derive.

Designprinzipien (PRODUCT_PLAN §2/§5):
- **P2 deterministisch:** reine Transformation, kein LLM, gleicher Input → gleicher Output.
- **P5 standalone:** ALUCA hängt NICHT von Meridian ab. Der Ziel-Vertrag wird hier als
  strukturgleiche Dataclasses gespiegelt (`canonical_contract`). Beim Einhängen in
  Meridian werden stattdessen dessen Originale importiert — Feldnamen sind identisch,
  also ist der Adapter 1:1 portierbar (PRODUCT_PLAN §0: "dock, don't rebuild").
- **Neutraler Core (PRODUCT_PLAN Invariante 1):** Measures tragen `expressions{}` je
  Dialekt; `expression` (DAX) ist nur EIN Dialekt, kein Primat. ALUCA liefert die
  Bedeutung dialekt-neutral; der jeweilige Stack-Adapter rendert.

Mapping (Quelle → Ziel):
  Bracket.orchestration.*_kpi_ids + primary_kpi_ids  → Measures (aufgelöst gegen KPI-Katalog)
  KPI.technical.lineage "fact_x.Col"                 → Table fact_x  +  Measure dialect map
  KPI.kpi_key / business / governance                → Measure name + description + folder
  Bracket.ux_layout_rules.page_1/2 + component_*     → ReportModel (Pages + Visuals)
  Bracket.governance.{owner,steward}_role            → Role-Metadaten (RLS-Platzhalter)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import yaml

from tooling.superversion.canonical_contract import (
    CanonicalModel,
    Measure,
    ReportModel,
    ReportPage,
    Role,
    SemanticModel,
    Table,
    Visual,
)


class AlucaSourceError(ValueError):
    """Bracket/Katalog verletzt den Adapter-Vertrag (fehlende Pflichtfelder o. ä.)."""


# Display-Folder-Marker für Measures ohne governten KPI-Katalog-Eintrag (kein
# strategischer Anker). Das Golden-Thread-Gate (I-3.4) liest diesen Marker.
UNRESOLVED_DISPLAY_FOLDER = "_Unresolved"


# --------------------------------------------------------------------------- #
# Katalog-Zugriff (KPI-ID → Definition)                                       #
# --------------------------------------------------------------------------- #

class KpiCatalog:
    """Lädt KPI-Definitionen aus core/kpi_catalog/kpis/*.yaml (ein File je KPI)."""

    def __init__(self, kpis_dir: Path):
        self._dir = Path(kpis_dir)
        self._cache: dict[str, dict] = {}

    def get(self, kpi_id: str) -> Optional[dict]:
        if kpi_id in self._cache:
            return self._cache[kpi_id]
        f = self._dir / f"{kpi_id}.yaml"
        if not f.exists():
            self._cache[kpi_id] = None
            return None
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        self._cache[kpi_id] = data
        return data


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise AlucaSourceError(msg)


def _split_lineage(lineage_entry: str) -> tuple[str, str]:
    """'fact_sales.Net Sales Amount' → ('fact_sales', 'Net Sales Amount').

    Falls kein Punkt: ('', entry) — Measure ohne klare Quelltabelle (→ _Measures).
    """
    if "." in lineage_entry:
        table, col = lineage_entry.split(".", 1)
        return table.strip(), col.strip()
    return "", lineage_entry.strip()


def _measure_from_kpi(kpi_id: str, kpi: Optional[dict], catalog: "KpiCatalog") -> tuple[Measure, str]:
    """Baut ein Measure aus einer KPI-Definition. Gibt (Measure, source_table) zurück.

    Wenn die KPI im Katalog fehlt (direkte Measure-Namen im Bracket, z. B.
    'Plan Sales Amount'), wird graceful ein Platzhalter-Measure gebaut (wie ALUCAs
    BracketCompiler: fehlende KPI → BLANK()/Warnung statt Crash).
    """
    if not kpi:
        # Direkter Name ohne Katalog-Eintrag: Measure-Name = ID selbst, HITL-Hinweis.
        name = kpi_id
        return (
            Measure(
                name=name,
                expression="",
                expressions={},
                description="HITL: no catalog entry — define measure/dialect.",
                display_folder=UNRESOLVED_DISPLAY_FOLDER,
            ),
            "",
        )
    tech = kpi.get("technical", {}) or {}
    biz = kpi.get("business", {}) or {}
    name = tech.get("measure_name") or kpi.get("kpi_key") or kpi_id
    lineage = tech.get("lineage") or []
    source_table = ""
    if lineage:
        source_table, _ = _split_lineage(lineage[0])
    domain = (kpi.get("domain_tag") or [""])[0]
    # Dialekt-neutral (I1): from_aluca trägt die governte Formel-DSL (I-10.0), NIE
    # fertiges DAX/SQL. `expressions['dsl']` ist ein deterministisch resolvter,
    # stack-neutraler Formel-Ausdruck (JSON) — der Stack-Adapter (targets/tmdl.py)
    # materialisiert daraus den Dialekt (dax_synth.py). Fehlt eine ableitbare Formel
    # (kein `calculation`-Feld oder `op: hitl`), bleibt `expressions` leer bzw. trägt
    # nur `hitl_reason` — NIEMALS stilles BLANK() ohne Grund (Review Befund A1).
    expressions: dict = {}
    resolved, hitl_reason = _resolve_calculation(kpi, catalog)
    if resolved is not None:
        expressions["dsl"] = json.dumps(resolved, sort_keys=True)
    elif hitl_reason:
        expressions["hitl_reason"] = hitl_reason
    measure = Measure(
        name=name,
        expression="",                       # kein DAX-Primat (neutraler Core)
        expressions=expressions,
        description=biz.get("definition", "") or biz.get("purpose", ""),
        format_string=_fmt_from_unit(biz.get("unit_format", "")),
        display_folder=domain,
    )
    return measure, source_table


def _own_lineage_columns(kpi: dict) -> dict[str, str]:
    """column-name (no table prefix) → table, from THIS KPI's own lineage list."""
    out: dict[str, str] = {}
    for entry in (kpi.get("technical", {}) or {}).get("lineage") or []:
        if "." in entry:
            table, col = entry.split(".", 1)
            out[col.strip()] = table.strip()
    return out


def _resolve_calc_ref(ref: dict, own_cols: dict[str, str], lineage: list[str], catalog: "KpiCatalog") -> Optional[dict]:
    """calc_ref (kpi-id, bare column, nested `calc`, or bare numeric `literal`) →
    neutral {"kind": "column"|"measure"|"expr"|"literal", ...}.

    Returns None if the reference cannot be resolved (unknown KPI id, a column
    not present in this KPI's own lineage, or an unresolvable nested `calc`) —
    the caller turns that into an explicit HITL marker, never a silent
    placeholder.
    """
    if "kpi" in ref:
        other = catalog.get(ref["kpi"])
        if not other:
            return None
        other_name = (other.get("technical", {}) or {}).get("measure_name") or other.get("kpi_key")
        if not other_name:
            return None
        return {"kind": "measure", "name": other_name}
    if "column" in ref:
        column = ref["column"]
        table = own_cols.get(column)
        if not table:
            return None
        return {"kind": "column", "table": table, "column": column}
    if "calc" in ref:
        nested, _hitl = _resolve_calc_node(ref["calc"], own_cols, lineage, catalog)
        if nested is None:
            return None
        return {"kind": "expr", **nested}
    if "literal" in ref:
        return {"kind": "literal", "value": ref["literal"]}
    return None


def _resolve_calc_filters(filters: list[dict], own_cols: dict[str, str]) -> list[dict]:
    """Shared `count_filtered`/`avg_filtered` filter-list resolution: each filter's
    `column` must be in this KPI's own lineage; raises KeyError (never a silent
    placeholder) if not."""
    resolved = []
    for f in filters:
        f_table = own_cols.get(f["column"])
        if not f_table:
            raise KeyError(f["column"])
        if "not_blank" in f:
            resolved.append({"table": f_table, "column": f["column"], "not_blank": True})
        else:
            resolved.append({"table": f_table, "column": f["column"], "equals": f["equals"]})
    return resolved


def _resolve_calc_node(
    calc: dict, own_cols: dict[str, str], lineage: list[str], catalog: "KpiCatalog"
) -> tuple[Optional[dict], Optional[str]]:
    """One governed `calculation` node (top-level `technical.calculation` OR a
    nested `{"calc": {...}}` calc_ref) → (resolved neutral formula, failure
    reason fragment). `own_cols`/`lineage` always come from the OWNING KPI —
    nested nodes resolve against the same lineage as their parent, they don't
    carry their own."""
    op = calc.get("op")

    def ref(key: str) -> Optional[dict]:
        return _resolve_calc_ref(calc[key], own_cols, lineage, catalog)

    try:
        if op == "sum":
            column = calc["column"]
            table = own_cols.get(column)
            if not table:
                raise KeyError(column)
            return {"op": "sum", "ref": {"kind": "column", "table": table, "column": column}}, None

        if op == "ratio":
            numerator, denominator = ref("numerator"), ref("denominator")
            if numerator is None or denominator is None:
                raise KeyError("numerator/denominator")
            resolved = {"op": "ratio", "numerator": numerator, "denominator": denominator}
            if calc.get("scale"):
                resolved["scale"] = calc["scale"]
            return resolved, None

        if op in ("delta", "delta_pct"):
            minuend, subtrahend = ref("minuend"), ref("subtrahend")
            if minuend is None or subtrahend is None:
                raise KeyError("minuend/subtrahend")
            return {"op": op, "minuend": minuend, "subtrahend": subtrahend}, None

        if op == "rate":
            column = calc["column"]
            table = own_cols.get(column)
            if not table:
                raise KeyError(column)
            return {"op": "rate", "table": table, "column": column}, None

        if op == "count":
            column = calc.get("column")
            if column:
                table = own_cols.get(column)
                if not table:
                    raise KeyError(column)
                return {"op": "count", "table": table}, None
            if not lineage or "." in lineage[0]:
                raise KeyError("bare-table lineage")
            return {"op": "count", "table": lineage[0]}, None

        if op == "mul":
            terms = [_resolve_calc_ref(t, own_cols, lineage, catalog) for t in calc["terms"]]
            if len(terms) < 2 or any(t is None for t in terms):
                raise KeyError("terms")
            return {"op": "mul", "terms": terms}, None

        if op == "add":
            terms = [_resolve_calc_ref(t, own_cols, lineage, catalog) for t in calc["terms"]]
            if len(terms) < 2 or any(t is None for t in terms):
                raise KeyError("terms")
            return {"op": "add", "terms": terms}, None

        if op == "delta_chain":
            minuend = ref("minuend")
            subtrahends = [_resolve_calc_ref(s, own_cols, lineage, catalog) for s in calc["subtrahends"]]
            if minuend is None or not subtrahends or any(s is None for s in subtrahends):
                raise KeyError("minuend/subtrahends")
            return {"op": "delta_chain", "minuend": minuend, "subtrahends": subtrahends}, None

        if op == "distinctcount":
            column = calc["column"]
            table = own_cols.get(column)
            if not table:
                raise KeyError(column)
            filters = []
            for f in calc.get("filters") or []:
                f_table = own_cols.get(f["column"])
                if not f_table:
                    raise KeyError(f["column"])
                filters.append({"table": f_table, "column": f["column"], "equals": f["equals"]})
            resolved = {"op": "distinctcount", "table": table, "column": column}
            if filters:
                resolved["filters"] = filters
            return resolved, None

        if op == "count_threshold":
            column = calc["column"]
            table = own_cols.get(column)
            if not table:
                raise KeyError(column)
            return {
                "op": "count_threshold", "table": table, "column": column,
                "comparator": calc["comparator"], "value": calc["value"],
            }, None

        if op == "round":
            value = ref("value")
            if value is None:
                raise KeyError("value")
            return {"op": "round", "value": value, "digits": calc["digits"]}, None

        if op == "abs":
            value = ref("value")
            if value is None:
                raise KeyError("value")
            return {"op": "abs", "value": value}, None

        if op in ("sumx_over_key", "avgx_over_key"):
            key_column = calc["key_column"]
            table = own_cols.get(key_column)
            value = ref("value")
            if not table or value is None:
                raise KeyError("key_column/value")
            return {"op": op, "table": table, "key_column": key_column, "value": value}, None

        if op == "pvm_volume_effect":
            qty_col, plan_qty_col, plan_sales_col = calc["quantity"], calc["plan_quantity"], calc["plan_sales"]
            tables = {own_cols.get(qty_col), own_cols.get(plan_qty_col), own_cols.get(plan_sales_col)}
            if None in tables or len(tables) != 1:
                raise KeyError("quantity/plan_quantity/plan_sales")
            return {
                "op": "pvm_volume_effect", "table": tables.pop(),
                "quantity_column": qty_col, "plan_quantity_column": plan_qty_col, "plan_sales_column": plan_sales_col,
            }, None

        if op == "pvm_price_effect":
            net_price_col, qty_col, plan_sales_col, plan_qty_col = (
                calc["net_price"], calc["quantity"], calc["plan_sales"], calc["plan_quantity"],
            )
            tables = {own_cols.get(net_price_col), own_cols.get(qty_col), own_cols.get(plan_sales_col), own_cols.get(plan_qty_col)}
            if None in tables or len(tables) != 1:
                raise KeyError("net_price/quantity/plan_sales/plan_quantity")
            return {
                "op": "pvm_price_effect", "table": tables.pop(),
                "net_price_column": net_price_col, "quantity_column": qty_col,
                "plan_sales_column": plan_sales_col, "plan_quantity_column": plan_qty_col,
            }, None

        if op == "avg":
            column = calc["column"]
            table = own_cols.get(column)
            if not table:
                raise KeyError(column)
            return {"op": "avg", "table": table, "column": column}, None

        if op == "sumx_product":
            col_a, col_b = calc["factor_a"], calc["factor_b"]
            tables = {own_cols.get(col_a), own_cols.get(col_b)}
            if None in tables or len(tables) != 1:
                raise KeyError("factor_a/factor_b")
            return {
                "op": "sumx_product", "table": tables.pop(),
                "factor_a_column": col_a, "factor_b_column": col_b,
            }, None

        if op == "count_filtered":
            column = calc["column"]
            table = own_cols.get(column)
            if not table:
                raise KeyError(column)
            filters = _resolve_calc_filters(calc["filters"], own_cols)
            return {"op": "count_filtered", "table": table, "filters": filters}, None

        if op == "avg_filtered":
            column = calc["column"]
            table = own_cols.get(column)
            if not table:
                raise KeyError(column)
            filters = _resolve_calc_filters(calc["filters"], own_cols)
            return {"op": "avg_filtered", "table": table, "column": column, "filters": filters}, None
    except KeyError as exc:
        return None, f"(op={op!r}) failed to resolve ({exc})"

    return None, f"has unknown op {op!r}"


def _resolve_calculation(kpi: dict, catalog: "KpiCatalog") -> tuple[Optional[dict], Optional[str]]:
    """`technical.calculation` (governed, authored) → (resolved neutral formula,
    HITL reason). Exactly one of the two is non-None (never both None without a
    reason — Cut S-1: "Fehlerfall: KPI ohne ableitbare Formel → expliziter
    HITL-Marker, NIEMALS stilles BLANK()")."""
    calc = (kpi.get("technical", {}) or {}).get("calculation")
    kpi_id = kpi.get("kpi_id", "?")
    if not calc:
        return None, None  # no calculation authored yet — generic "no dialect" HITL downstream
    op = calc.get("op")
    if op == "hitl":
        return None, calc.get("reason") or f"HITL: '{kpi_id}' explicitly marked HITL."

    own_cols = _own_lineage_columns(kpi)
    lineage = (kpi.get("technical", {}) or {}).get("lineage") or []

    resolved, failure = _resolve_calc_node(calc, own_cols, lineage, catalog)
    if resolved is not None:
        return resolved, None
    return None, (
        f"HITL: calculation for '{kpi_id}' {failure} — check technical.lineage / referenced kpi ids."
    )


def _fmt_from_unit(unit: str) -> str:
    u = (unit or "").lower()
    if "eur" in u or "€" in u:
        return r"\€#,0.00;-\€#,0.00"
    if "%" in u or "pct" in u or "percent" in u:
        return "0.0%"
    return ""


def _kpi_ids_from_bracket(bracket: dict) -> list[str]:
    """Sammelt alle referenzierten KPI-IDs (dedupe, Reihenfolge erhalten)."""
    orch = bracket.get("orchestration", {}) or {}
    ids: list[str] = []
    for key in ("strategic_kpi_id",):
        v = orch.get(key)
        if isinstance(v, str):
            ids.append(v)
    for key in ("influencing_kpi_ids", "supporting_kpi_ids"):
        ids.extend(orch.get(key, []) or [])
    ids.extend(bracket.get("primary_kpi_ids", []) or [])
    seen: set[str] = set()
    out: list[str] = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


# --------------------------------------------------------------------------- #
# Report-Mapping (3-30-300 Layout → Pages + Visuals)                          #
# --------------------------------------------------------------------------- #

def _collect_visual_kpi_ids(component: dict, catalog: KpiCatalog) -> list[str]:
    """KPI-IDs, die ein Visual an Measures bindet (dedupe, Reihenfolge erhalten).

    - `kpi_id` / `kpi_ids`: explizite Referenzen — binden as-is (auch ohne
      Katalog-Eintrag: graceful Platzhalter, wie `_measure_from_kpi`).
    - `evidence_columns` (3-30-300 Detail-/Evidence-Grid, `component_300s`): eine
      gemischte Liste aus Dimensions-Feldern (region, channel, …) UND KPI-IDs.
      Nur **katalog-auflösbare** Spalten werden zu Measures; reine Dimensionen
      sind keine Measures. Kein auflösbares Feld → leere Bindung (v0-Karte bleibt).
    """
    out: list[str] = []
    if component.get("kpi_id"):
        out.append(component["kpi_id"])
    out.extend(component.get("kpi_ids", []) or [])
    for col in component.get("evidence_columns", []) or []:
        if isinstance(col, str) and catalog.get(col) is not None:
            out.append(col)
    seen: set[str] = set()
    deduped: list[str] = []
    for i in out:
        if i not in seen:
            seen.add(i)
            deduped.append(i)
    return deduped


# ─────────────────────────────────────────────────────────────────────────────
# Layout-Bindung (Task L8)
#
# Bis zum 02.08.2026 erzeugte dieser Adapter Visuals OHNE Geometrie — jedes `Visual`
# ging mit x=y=width=height=0 heraus. Sichtbar war das in den eingecheckten Golden
# Snapshots (`"width": 0`), aber es fiel nicht auf, weil kein Test danach fragte.
# Der Vertrag (`_canonical_mirror.Visual`) fuehrt die vier Felder seit jeher.
#
# Gebunden wird als **Leser** des governten Systems, nicht als kopierte Tabelle:
# die Slot-Definitionen leben in Logical Units in `generator_core/ir/compiler.py`
# (Task L13), die Rasterparameter in `core/templates/page_templates/tokens/layout_grid.yaml`.
# Eine Aenderung dort wirkt hier ohne Codeaenderung — das ist die eigentliche
# Zusicherung von L8, nicht die Zahlen selbst.
#
# Warum PIXEL und nicht Brueche: PBIR positioniert in Pixeln. Die Aufloesung passiert
# genau einmal, in `layout_grid.to_pixels()`, gegen die Produktionsleinwand.
_SLOT_FUER_KOMPONENTE = {
    "3s": "KPI_Cards",
    "300s": "Detail_Matrix",
}
# Die 30s-Komponenten fuellen der Reihe nach die drei Hauptspalten — dieselbe
# Zuordnung, die der IR-Compiler vornimmt (`Main_{i}`), damit beide Pfade dieselbe
# Seite beschreiben und nicht zwei Wahrheiten ueber dasselbe Layout entstehen.
_MAIN_SLOTS = ("Main_1", "Main_2", "Main_3")

#: Welches Visual ein Pflicht-Moebel ist. Die Werte sind `CHROME_TOKENS` aus der
#: Visual-Library — Seitenmoebel, ausdruecklich KEINE Registry-Visuals: die Registry
#: beschreibt Absichten, und ein Slicer beantwortet keine Frage. Das `visual_type_hint`
#: der Raster-Templates ist bewusst NICHT die Quelle: es fuehrt PBIR-Typnamen
#: (`tableEx`, `cardVisual`) und wuerde die Vokabular-Autoritaet aus ADR-0018 umgehen.
_MOEBEL_VISUAL = {
    "Slicer_Date": "slicer",
    "Slicer_Pane": "slicer",
    "Slicer_Entity": "slicer",
    "Slicer_Region": "slicer",
    "Slicer_Product": "slicer",
    "Smart_Narrative": "smart_narrative",
    "ActionPanel": "action_panel",
}

#: Das Feld, auf das ein Slicer filtert. Leer heisst „vom Modell zu binden" — der
#: Bracket kennt hier keine Spalte, und eine erfundene waere ein dangling reference.
_SLICER_FELD = {"Slicer_Date": "Date[Date]"}


def _slot_geometrie(slot_name: str, variant: str = "", ebene: str = "") -> dict[str, float]:
    """Slot-Name → Pixel-Rechteck aus dem Raster-Template **dieser Variante**.

    Leer, wenn der Slot dort nicht deklariert ist — geraten wird nichts.

    Bis 02.08.2026 las diese Funktion `_OVERVIEW_LU`/`_DETAIL_LU` aus dem IR-Compiler.
    Gemessen war das faktisch `pulse` fuer **alle** Varianten: `executive_kpi` gibt
    `Main_2` 328 px Hoehe, die Tabelle 749 px (Δ 421). `template_variant` wurde also
    deklariert, gegen das Manifest validiert — und von der Geometrie ignoriert.
    Autoritaet sind jetzt die `grid_templates/*.json` (Entscheidung Flo, 02.08.2026).

    Ohne Variante bleibt das benannte Default-Raster — dieselbe Annahme wie vorher,
    aber sichtbar statt in einer Tabelle versteckt.
    """
    from tooling.superversion.layer_tools.layout_grid import load, to_pixels
    from tooling.superversion.layer_tools.page_templates import default_raster, slot_lu

    lu = None
    if variant and ebene:
        lu = slot_lu(variant, ebene, slot_name)
    if lu is None and ebene:
        lu = default_raster(ebene).slots.get(slot_name)
    if lu is None:
        return {}
    return to_pixels(*lu, params=load("production"))


def _visual_fuer_slot(component: dict, slot_name: str, variant: str,
                      ebene: str) -> tuple[str, Optional[dict]]:
    """Welches Visual gehoert in diesen Slot — und widerspricht das Bracket der Variante?

    Das ist die Naht, die bis 02.08.2026 fehlte. `template_manifest.yaml` weist jedem
    Slot einer Variante einen `information_block` zu — `Main_2` ist bei
    T2_DriverBridge `variance_explanation`, bei T3_ProcessControl `exception_list`.
    Das ist die **einzige** Achse, auf der sich die 11 Varianten wirklich unterscheiden
    (6 bzw. 7 distinkte Signaturen bei 2x2 Rastern). Gemessen wurde sie von **niemandem**
    gelesen: 0 Treffer in diesem Modul und im IR-Compiler.

    Genau das hat `PAGE_TYPE_TAXONOMY.md` schon benannt — „the renderer was not
    distinguishing them… an engine gap, not a taxonomy gap". Behoben wurde es nie.

    Drei Faelle, und keiner ueberstimmt still:

    * **Bracket schweigt** → `default_visual` des Blocks. Vorher stand hier ein
      hartes `"card"`, unabhaengig vom Slot — 20 der 66 Deklarationen liefen darauf.
      Eine KPI-Karte an der Stelle einer Ausnahmeliste ist kein Default, sondern ein
      stiller Fallback.
    * **Bracket waehlt aus der erlaubten Menge** → die Wahl gilt. Governance grenzt
      ein, sie entmuendigt nicht.
    * **Bracket waehlt ausserhalb** → die Wahl gilt **trotzdem**, aber der Konflikt
      wird gemeldet. 12 der 66 Deklarationen sind das heute, 7 davon derselbe Fall
      (`exception_list` vs. Balkendiagramm). Bei sieben gleichlautenden Widerspruechen
      ist keineswegs ausgemacht, dass die Brackets falsch liegen — es kann die
      Slot-Zuweisung der Variante sein. Das automatisch zu ueberschreiben hiesse, eine
      offene Frage per Codezeile zu entscheiden.
    """
    from tooling.superversion.layer_tools.page_templates import load as _variante
    from tooling.superversion.layer_tools.visual_library import (
        VisualLibrary, canonical_visual_id,
    )

    deklariert = component.get("visual_type") or ""
    block = None
    if variant and ebene and slot_name:
        try:
            block = next((s.information_block for s in _variante(variant).slots
                          if s.slot_id == slot_name and s.ebene == ebene), None)
        except Exception:      # unbekannte Variante meldet `slot_luecken`, nicht hier
            block = None
    if not block:
        return (deklariert or "card"), None

    lib = VisualLibrary.load()
    spec = lib.block(block)
    erlaubt = {v.visual_id for v in spec.allowed_visuals}
    # `default_visual()` ist eine METHODE, kein Attribut — ein `getattr` darauf liefert
    # das gebundene Objekt und ist wahrheitswertig. Genau daran ist der erste Lauf
    # gescheitert: der Visualtyp war ein `<bound method …>`.
    dv = spec.default_visual()
    default = dv.visual_id if dv else ""

    if not deklariert:
        return (default or "card"), None
    kanon = canonical_visual_id(deklariert) or deklariert
    if kanon in erlaubt:
        return deklariert, None
    return deklariert, {"slot": slot_name, "block": block, "declared": kanon,
                        "allowed": sorted(erlaubt)}


def _page_from_layout(page_key: str, page: dict, catalog: KpiCatalog) -> ReportPage:
    visuals: list[Visual] = []
    idx = 0
    vergeben: set[str] = set()
    block_konflikte: list[dict] = []
    variant = page.get("template_variant") or ""
    ebene = _EBENE_JE_SEITE.get(page_key, "")

    def add(component: dict, slot: str, slot_name: str = ""):
        nonlocal idx
        idx += 1
        # Der Bracket darf seinen Slot selbst benennen (`slot_id`); sonst entscheidet
        # die Komponentenart. Geraten wird nichts: ein unbekannter Slot bekommt keine
        # Geometrie statt einer plausiblen — eine erfundene Position sieht richtig aus
        # und ist es nicht.
        name = slot_name or component.get("slot_id") or _SLOT_FUER_KOMPONENTE.get(slot, "")
        geo = _slot_geometrie(name, variant, ebene) if name else {}
        vtyp, konflikt = _visual_fuer_slot(component, name, variant, ebene)
        if konflikt:
            block_konflikte.append(konflikt)
        kpi_ids = _collect_visual_kpi_ids(component, catalog)
        # bound_measures: aufgelöste measure_names (Katalog) bzw. direkter Name
        bound = []
        for kid in kpi_ids:
            kpi = catalog.get(kid)
            bound.append((kpi.get("technical", {}).get("measure_name") if kpi else None) or kid)
        # Die `visual_id` IST der Slot-Name, wo einer bekannt ist.
        #
        # Vorher: `page_1_summary_3s_1`. Der Slot-Name wurde oben berechnet, fuer die
        # Geometrie benutzt und dann weggeworfen — womit nachgelagert niemand mehr
        # pruefen konnte, ob eine Seite ihre Pflicht-Slots hat. `RequiredSlots`
        # vergleicht Slot-Namen; gegen `page_1_summary_3s_1` konnte die Menge sich nie
        # schneiden, der Wachhund lief also leer (einer von drei Gruenden, gemessen
        # 02.08.2026).
        #
        # Kollisionen sind hier KEIN Schoenheitsfehler: die `visual_id` wird in
        # `pbir.py` zum Verzeichnisnamen (`.../visuals/<visual_id>/visual.json`).
        # Zwei gleiche Namen = ein Visual ueberschreibt das andere, still. Deshalb
        # faellt ein bereits vergebener Name auf das indizierte Schema zurueck,
        # statt zu ueberschreiben.
        vid = name if name and name not in vergeben else f"{page_key}_{slot}_{idx}"
        vergeben.add(vid)
        visuals.append(
            Visual(
                visual_id=vid,
                x=geo.get("x", 0), y=geo.get("y", 0),
                width=geo.get("width", 0), height=geo.get("height", 0),
                visual_type=vtyp,
                # BC-NARR-01 (K2/K3): the governed exhibit statement wins the title when
                # present; else fall back to the slot label / decision question.
                title=component.get("message") or component.get("slot_id", "") or component.get("decision_question", ""),
                bound_measures=bound,
                binds_measures=bool(bound),
            )
        )

    # component_3s (lead card) — single dict
    c3 = page.get("component_3s")
    if isinstance(c3, dict):
        add(c3, "3s")
    # component_30s — die drei Hauptspalten, in Reihenfolge. Ueberzaehlige
    # Komponenten bekommen KEINE Geometrie (statt einer vierten Spalte, die es im
    # Raster nicht gibt) — sichtbar leer ist besser als still danebengesetzt.
    for i, slot in enumerate(page.get("component_30s", []) or []):
        if isinstance(slot, dict):
            add(slot, "30s", _MAIN_SLOTS[i] if i < len(_MAIN_SLOTS) else "")
    # component_300s — detail (may carry visuals or evidence grid)
    c300 = page.get("component_300s")
    if isinstance(c300, dict):
        add(c300, "300s")

    # --- Pflicht-Moebel des Manifests (Schritt 2, 02.08.2026) ------------------
    #
    # Der Bracket deklariert nur drei Informationsbloecke (3s/30s/300s). Slicer,
    # Aktionspanel und Detail-Filterleiste sind **Template**-Sache, kein Autoreninhalt —
    # der Autor kann sie gar nicht deklarieren. Genau deshalb fehlten sie: gemessen am
    # 02.08.2026 wiesen 39 von 40 Seiten mindestens einen Pflicht-Slot nicht aus.
    #
    # Sie werden aus dem Manifest ergaenzt, nicht erfunden: Pflicht laut Variante UND
    # Geometrie im gebundenen Raster-Template. Fehlt die Geometrie (fuer fuenf Varianten
    # deklariert das Manifest kein Detail-Raster), wird **nichts** gesetzt — ein Visual
    # ohne Position waere schlimmer als sein Fehlen, weil `page_slots` es als erledigt
    # zaehlte und der Report es bei (0,0) stapelte.
    #
    # Sie binden keine Measures: ein Slicer beantwortet keine Frage (dieselbe Trennung
    # wie `CHROME_TOKENS` in der Visual-Library). Der Golden-Thread-Gate prueft
    # Measure-Anker und bleibt davon unberuehrt.
    if variant and ebene:
        from tooling.superversion.layer_tools.page_templates import load as _variante

        try:
            pflicht = _variante(variant).pflicht(ebene)
        except Exception:      # unbekannte Variante: das meldet `slot_luecken`, nicht hier
            pflicht = []
        for slot_id in pflicht:
            if slot_id in vergeben:
                continue
            geo = _slot_geometrie(slot_id, variant, ebene)
            if not geo:
                continue
            vergeben.add(slot_id)
            visuals.append(Visual(
                visual_id=slot_id,
                x=geo["x"], y=geo["y"], width=geo["width"], height=geo["height"],
                visual_type=_MOEBEL_VISUAL.get(slot_id, "text_box"),
                title="", has_title=False,
                bound_measures=[], binds_measures=False,
                slicer_field=_SLICER_FELD.get(slot_id, ""),
            ))

    # Die Seite deklariert DIESELBE Leinwand, gegen die ihre Visuals aufgeloest sind.
    #
    # Vorher nicht: `ReportPage` defaultet auf 1280x720 (design_base), die Geometrie
    # loest gegen `canvas.production` (1920x1080) auf. Der offizielle Validator hat den
    # Widerspruch am 02.08.2026 benannt — `PBIR_LAYOUT_OUT_OF_BOUNDS_WIDTH`:
    # „x:32 + w:1856 = 1888 > 1280". Das ist derselbe Fehler, den L13 eine Schicht
    # tiefer behoben hat: zwei Stellen behaupteten verschiedene Leinwaende, und beide
    # hatten recht ueber sich.
    #
    # Gelesen statt hartkodiert — sonst waere es die dritte Stelle mit einer eigenen
    # Meinung ueber die Leinwandgroesse.
    from tooling.superversion.layer_tools.layout_grid import load

    raster = load("production")
    seite = ReportPage(
        name=page_key,
        display_name=page.get("title", page_key),
        page_type="Default",
        visuals=visuals,
        width=raster.width,
        height=raster.height,
    )
    # Block-Konflikte reisen am Ergebnis mit, statt ueber eine zweite Berechnung —
    # sonst waeren Emission und Meldung zwei Wahrheiten ueber denselben Lauf.
    seite._block_konflikte = block_konflikte      # type: ignore[attr-defined]
    return seite


# --------------------------------------------------------------------------- #
# Haupt-Einstieg                                                              #
# --------------------------------------------------------------------------- #

def from_bracket(bracket: dict, catalog: KpiCatalog) -> CanonicalModel:
    """Baut das kanonische Modell aus einem geladenen UseCase-Bracket + KPI-Katalog."""
    _require(isinstance(bracket, dict), "Bracket muss ein Objekt sein")
    uc_id = bracket.get("id") or "UC"
    _require(isinstance(bracket.get("orchestration"), dict),
             f"{uc_id}: 'orchestration' (Objekt) ist Pflicht")

    # --- Measures aus referenzierten KPIs, gruppiert nach Quelltabelle ---
    tables_by_name: dict[str, Table] = {}
    measures_unrouted: list[Measure] = []
    for kid in _kpi_ids_from_bracket(bracket):
        kpi = catalog.get(kid)
        measure, src_table = _measure_from_kpi(kid, kpi, catalog)
        if src_table:
            t = tables_by_name.get(src_table)
            if t is None:
                t = Table(name=src_table)
                tables_by_name[src_table] = t
            t.measures.append(measure)
        else:
            measures_unrouted.append(measure)

    # Measures ohne klare Quelltabelle bündeln (Konvention: _Measures-Tabelle)
    if measures_unrouted:
        tables_by_name.setdefault("_Measures", Table(name="_Measures")).measures.extend(
            measures_unrouted
        )

    semantic = SemanticModel(
        name=f"{uc_id}_{_slug(bracket.get('title', ''))}",
        tables=list(tables_by_name.values()),
        relationships=[],   # ALUCA-Bracket trägt keine physischen Relationships (→ data_contracts/Stack)
        roles=_roles_from_governance(bracket.get("governance", {}) or {}),
    )

    # --- Report aus ux_layout_rules ---
    layout = bracket.get("ux_layout_rules", {}) or {}
    pages: list[ReportPage] = []
    for pk in ("page_1_summary", "page_2_execution"):
        if isinstance(layout.get(pk), dict):
            pages.append(_page_from_layout(pk, layout[pk], catalog))
    report = ReportModel(name=semantic.name, pages=pages)

    return CanonicalModel(semantic=semantic, report=report)


#: Welche Manifest-Ebene eine Bracket-Seite bedient. `from_aluca` kennt genau zwei
#: Seiten; das Manifest fuehrt seine Slots getrennt nach `overview_slots` und
#: `detail_slots`. Ohne diese Zuordnung pruefte man Detailmoebel gegen die
#: Uebersichtsseite und bekaeme Fehlalarme statt Befunde.
_EBENE_JE_SEITE = {
    "page_1_summary": "overview_slots",
    "page_2_execution": "detail_slots",
}


def slot_luecken(bracket_path: str | Path, kpis_dir: str | Path) -> list[dict]:
    """Welche **Pflicht**-Slots des governten Manifests emittiert der Adapter nicht?

    Gibt je Seite einen Eintrag zurueck (`use_case`, `page`, `variant`, `missing`,
    `emitted`). Leere `missing`-Listen bleiben enthalten, damit ein Aufrufer
    „geprueft und vollstaendig" von „gar nicht geprueft" unterscheiden kann — der
    Unterschied, an dem `RequiredSlots` gescheitert ist.

    Die Wahrheit ueber Pflicht-Slots steht **ausschliesslich** im Manifest
    (`layer_tools/page_templates.py`); hier wird nichts nachdefiniert.
    """
    from tooling.superversion.layer_tools.page_templates import fehlende_pflichtslots

    bracket = yaml.safe_load(Path(bracket_path).read_text(encoding="utf-8")) or {}
    catalog = KpiCatalog(Path(kpis_dir))
    layout = bracket.get("ux_layout_rules", {}) or {}
    uc = bracket.get("use_case_id") or bracket.get("id") or Path(bracket_path).parent.name

    out: list[dict] = []
    for pk, ebene in _EBENE_JE_SEITE.items():
        seite = layout.get(pk)
        if not isinstance(seite, dict):
            continue
        variant = seite.get("template_variant")
        if not variant:
            # Kein Raten: ohne deklarierte Variante gibt es keine Pflichtliste. Das
            # als „nichts fehlt" zu melden waere die Luege, gegen die dieses Modul
            # gebaut ist.
            out.append({"use_case": uc, "page": pk, "variant": None,
                        "missing": None, "emitted": []})
            continue
        gebaut = _page_from_layout(pk, seite, catalog)
        emittiert = [v.visual_id for v in gebaut.visuals]
        # Woher kam die Geometrie? Das Manifest deklariert fuer fuenf Varianten **kein**
        # Detail-Raster; dort greift das benannte Default-Raster. Ohne diese Angabe
        # laese sich eine vollstaendige Seite nicht von einer unterscheiden, die nur
        # durch einen Rueckfall vollstaendig aussieht — dieselbe Verwechslung wie
        # „nicht geprueft" gegen „nichts gefunden".
        from tooling.superversion.layer_tools.page_templates import raster_fuer
        eigenes = raster_fuer(variant, ebene)
        out.append({
            "use_case": uc, "page": pk, "variant": variant,
            "missing": fehlende_pflichtslots(variant, emittiert, ebene=ebene),
            "emitted": emittiert,
            "raster": eigenes.template_id if eigenes else None,
            "raster_default": eigenes is None,
            # Bracket-Visual widerspricht dem `information_block` des Slots. Gemeldet,
            # nicht ueberschrieben: bei sieben gleichlautenden Widerspruechen ist offen,
            # ob das Bracket oder die Slot-Zuweisung der Variante irrt.
            "block_conflicts": getattr(gebaut, "_block_konflikte", []),
        })
    return out


def _roles_from_governance(gov: dict) -> list[Role]:
    """Governance-Rollen → RLS-Role-Platzhalter (Owner/Steward als Modell-Metadaten)."""
    roles: list[Role] = []
    for key in ("owner_role", "steward_role"):
        r = gov.get(key)
        if isinstance(r, str) and r:
            roles.append(Role(name=r, table_permissions=[]))
    return roles


def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", (s or "").strip()).strip("_")


def from_bracket_file(bracket_path: Path, kpis_dir: Path) -> CanonicalModel:
    """Lädt ein UseCase_Bracket.yaml + den KPI-Katalog und baut das kanonische Modell."""
    bracket = yaml.safe_load(Path(bracket_path).read_text(encoding="utf-8"))
    return from_bracket(bracket, KpiCatalog(kpis_dir))


# --------------------------------------------------------------------------- #
# Serialisierung + CLI (I-1.5) — deterministisch, golden-snapshot-fähig        #
# --------------------------------------------------------------------------- #

def model_to_json(model: CanonicalModel) -> str:
    """Deterministische JSON-Repräsentation des kanonischen Modells.

    `asdict` erhält die Dataclass-Feldreihenfolge, `json.dumps` erhält die
    Dict-Reihenfolge → gleicher Input liefert byte-stabilen Output (Invariante
    I2). Endet mit Newline (POSIX-Textdatei, stabiler Golden-Snapshot)."""
    return json.dumps(asdict(model), indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def _default_kpis_dir() -> Path:
    """Repo-Standard-Katalog (tooling/superversion/from_aluca.py → repo-root)."""
    return Path(__file__).resolve().parents[2] / "core" / "kpi_catalog" / "kpis"


def main(argv: Optional[list[str]] = None) -> int:
    """CLI: `python -m tooling.superversion.from_aluca <bracket> [--out model.json]`.

    Additiv (Rollback: einfach nicht aufrufen). Ohne `--out` → stdout."""
    parser = argparse.ArgumentParser(
        prog="python -m tooling.superversion.from_aluca",
        description="ALUCA UseCase-Bracket → kanonisches Modell (JSON).",
    )
    parser.add_argument("bracket", type=Path, help="Pfad zu UseCase_Bracket.yaml")
    parser.add_argument("--out", type=Path, default=None,
                        help="Ausgabedatei (Default: stdout)")
    parser.add_argument("--kpis", type=Path, default=None,
                        help=f"KPI-Katalog-Verzeichnis (Default: {_default_kpis_dir()})")
    args = parser.parse_args(argv)

    kpis_dir = args.kpis or _default_kpis_dir()
    model = from_bracket_file(args.bracket, kpis_dir)
    payload = model_to_json(model)

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
