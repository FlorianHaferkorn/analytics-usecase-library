"""
Bracket Compiler — translates UseCase_Bracket.yaml + KPI Catalog into IR.

Usage
-----
    from tooling.generator_core.ir.compiler import BracketCompiler

    compiler = BracketCompiler(
        kpi_catalog_root=Path("core/kpi_catalog"),
        action_codes_root=Path("core/action_codes"),
    )
    spec = compiler.compile(bracket_path=Path("core/usecases/core/COM-001_.../UseCase_Bracket.yaml"))

Design notes
------------
* The compiler is read-only — it never writes files.
* Geometrie wird in **Logical Units** verfasst (`_OVERVIEW_LU` / `_DETAIL_LU`) und
  ausschliesslich in `lu_to_pixels()` aufgeloest — Gutter und Aussenrand inbegriffen.
  Das IR fuehrt weiterhin Leinwandbrueche, aber ABGELEITET statt handgeschrieben.
  Zielleinwand ist `canvas.production` aus `layout_grid.yaml` (1920x1080) — dieselbe,
  die `products/fabric/powerbi/tooling/adapters/pbip.py` verwendet. Der frueher hier
  behauptete Wert 1280x720 war der Widerspruch, den Task L13 aufgeloest hat.
* measure_spec entries come from the KPI catalog dax_expression field.
  If a KPI is not in the catalog the compiler records a warning and skips it.
* Action panel text is rendered here so downstream adapters get a ready-to-use
  string without needing to re-load YAML files.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from .specs import (
    ActionPanelSpec,
    AdapterTarget,
    Binding,
    DashboardSpec,
    EvidenceTableSpec,
    MeasureSpec,
    PageRole,
    PageSpec,
    PageType,
    Position,
    VisualSpec,
    VisualType,
)


# ---------------------------------------------------------------------------
# Ein Koordinatensystem: Logical Units, aufgeloest erst im Konnektor (Task L13)
# ---------------------------------------------------------------------------
#
# Vorher standen hier Brueche der Leinwand. Das war auf zwei Arten kaputt, beides
# am 02.08.2026 gemessen statt vermutet:
#
#  1. Die Brueche waren gegen **1920x1080** geschrieben (0.0167 * 1920 = 32.1 px =
#     `outer_margin`), waehrend `layout_grid.yaml` seine Logical Units gegen
#     **1280x720** rechnet. Auf der design_base lag der erste Slot bei Spalte -0.10,
#     also ausserhalb des Rasters. Der Docstring dieser Datei behauptete 1280x720,
#     `products/.../adapters/pbip.py` sagte 1920x1080 — beide Seiten hatten recht
#     ueber sich und unrecht ueber die andere.
#  2. Selbst auf 1920 ging es nicht auf: `Main_1` ergab **3.93** statt 4 Spalten.
#     Ursache war kein Rundungsfehler, sondern eine Inkonsistenz im Modell — die
#     Brueche skalieren mit der Leinwand, `gutter` und `outer_margin` sind absolute
#     Pixel und skalieren nicht mit. Eine Groesse, die zur Haelfte mitskaliert, ist
#     ausserhalb ihrer Autorenleinwand auf keiner Leinwand korrekt.
#
# Jetzt: Position UND Spanne in Logical Units, Gutter und Aussenrand inbegriffen.
# Pixel entstehen ausschliesslich in `_lu_position()` aus der Leinwand des Profils.
# Die Formel spiegelt `core/templates/page_templates/preview/src/grid/slot-pos.ts`
# — dort loest CSS `calc()` denselben Vertrag bereits korrekt auf; ein Test haelt
# beide Seiten deckungsgleich, statt sich auf Nachlesen zu verlassen.
#
# HORIZONTAL ganzzahlig, VERTIKAL bewusst fraktional — und das ist kein Kompromiss
# aus Bequemlichkeit:
#   * Waagerecht ist das Raster echt. Overview = drei Spalten zu 4 LU (0/4/8),
#     Detail = 2 + 8 + 2 = 12. Genau hier sass der 3.93-Fehler; hier wird gerundet.
#   * Senkrecht ist es das nicht. Ein Zwang auf 12 Zeilen liesse `Benchmark_Caption`
#     und `Slicer_Date` auf dieselbe Zeile 2 fallen (Kollision) und verschoebe Slots
#     um bis zu 40 px. Vor allem aber hat der Datums-Slicer eine **dokumentierte
#     Mindesthoehe** von 76 px (Header 28 + Selektor 32 + Padding); darunter meldet
#     die offizielle CLI `PBIR_SLICER_HEIGHT_BELOW_FLOOR` und das Control schneidet
#     im Service ab. Ein Raster, das eine Plattform-Zusicherung bricht, gewinnt nicht.
#     `slot-pos.ts` erlaubt fraktionale Zeilen ausdruecklich ("may be fractional").
#
# Format je Slot: (col, row, colSpan, rowSpan) in Logical Units.
#
# GELESEN, nicht hartkodiert (02.08.2026). Bis dahin standen diese Zahlen hier als
# Python-Tabelle — die dritte von drei Geometrie-Quellen und die einzige, die der
# lebende Pfad benutzte (§13).
#
# Aufgeloest wurde die Dublette durch **Promotion**, nicht durch Gleichsetzung: das
# Layout hier ist NICHT `pulse`/`action_matrix`. Gemessen unterscheidet es sich in drei
# Punkten, und keiner davon ist eine Rundung — ein breiter Datums-Slicer (12 LU) statt
# dreier schmaler (4+4+4 mit Region/Product), volle Seitenschienen (12 LU) statt
# geteilter (6+6 mit Slicer_Entity), und ein `ActionPanel` ueber die ganze Hoehe statt
# buendig zur Matrix. Dazu `Benchmark_Caption`, das in keinem anderen Raster vorkommt.
#
# Es einfach auf `pulse` zu ziehen haette den Datums-Slicer auf ein Drittel geschrumpft
# und zwei Drittel der Zeile leer gelassen — eine Regression, die wie Konsolidierung
# aussieht. Stattdessen sind die beiden Layouts jetzt governte Raster-Templates
# (`pulse_wide`, `action_rail`) und werden von dort gelesen. Gleiche Zahlen, eine
# Autoritaet; ein Test haelt die Positionen byte-identisch fest.
def _lu_aus_template(template_id: str) -> Dict[str, Tuple[float, float, float, float]]:
    from tooling.superversion.layer_tools.page_templates import grid_template

    return {slot: tuple(lu) for slot, lu in grid_template(template_id).slots.items()}


_OVERVIEW_LU: Dict[str, Tuple[float, float, float, float]] = _lu_aus_template("pulse_wide")
_DETAIL_LU: Dict[str, Tuple[float, float, float, float]] = _lu_aus_template("action_rail")

# Map bracket visual_type → VisualType enum
_VISUAL_TYPE_MAP: Dict[str, VisualType] = {
    "kpi_card":       VisualType.KPI_CARD,
    "trend_line":     VisualType.TREND_LINE,
    "bar_chart":      VisualType.BAR_CHART,
    "waterfall":      VisualType.WATERFALL,
    "scatter":        VisualType.SCATTER,
    "matrix":         VisualType.MATRIX,
    "table":          VisualType.TABLE,
    "slicer":         VisualType.SLICER,
    "smart_narrative": VisualType.SMART_NARRATIVE,
    "action_panel":   VisualType.ACTION_PANEL,
    # Alt-Token, die hier FEHLTEN und deshalb bis zum 02.08.2026 still auf den
    # TREND_LINE-Fallback liefen. `bar_chart_horizontal` ist der teure Fall: vier
    # Bracket-Deklarationen (OPS/SCM/COM, Main_2 + Main_3) sagen „horizontaler Balken"
    # und wurden als Trendlinie kompiliert. `line_chart` traf es ebenso, blieb aber
    # folgenlos, weil das Ziel zufaellig dasselbe Visual ist. Genau diese Asymmetrie
    # ist der Grund, warum ein stiller Default schlimmer ist als ein Abbruch: er ist
    # manchmal harmlos, und deshalb faellt er nie auf.
    "bar_chart_horizontal": VisualType.HORIZONTAL_BAR,
    "bar_chart_column":     VisualType.COLUMN_CHART,
    "line_chart":     VisualType.LINE_CHART,
    # Registry-Vokabular (ADR-0018) — dieselben Visuals unter ihrem SoT-Namen. Bis die
    # Brackets normalisiert sind (L2-Rest), muessen BEIDE Schreibweisen ankommen.
    "kpi_card_with_delta":  VisualType.KPI_CARD,
    "horizontal_bar_chart": VisualType.HORIZONTAL_BAR,
    "column_chart":         VisualType.COLUMN_CHART,
    "waterfall_chart":      VisualType.WATERFALL,
    "variance_bar":         VisualType.VARIANCE_BAR,
    "scatter_plot":         VisualType.SCATTER,
    "exception_table":      VisualType.EXCEPTION_TABLE,
}


class UnknownVisualTypeError(ValueError):
    """Ein `visual_type`, den weder Bracket- noch Registry-Vokabular kennt."""


def _resolve_visual_type(vt_str: str, slot_id: str) -> VisualType:
    """Bracket-Token → `VisualType`. Unbekanntes bricht ab, statt still zu raten.

    Vorher stand hier `_VISUAL_TYPE_MAP.get(vt_str, VisualType.TREND_LINE)`. Der
    Default war kein Sicherheitsnetz, sondern ein Verdeckungsmechanismus: ein Tippfehler
    oder ein per Schema erlaubter, aber ungemappter Typ (`funnel_chart`, `status_tile`)
    wurde klammheimlich zur Trendlinie. Der Generator lief durch, der Report war falsch,
    und nichts wurde rot — die Fehlerklasse, die dieses Repo wiederholt getroffen hat.

    Ein unbekannter Typ ist ein Autorenfehler und gehoert laut gemeldet.
    """
    if vt_str in _VISUAL_TYPE_MAP:
        return _VISUAL_TYPE_MAP[vt_str]
    raise UnknownVisualTypeError(
        f"unbekannter visual_type '{vt_str}' in Slot {slot_id}. "
        f"Autoritaet ist core/templates/page_templates/visual_registry.yaml (ADR-0018); "
        f"Alt-Token werden in tooling/superversion/layer_tools/visual_library.py "
        f"(LEGACY_TO_REGISTRY) uebersetzt. Bekannt: {sorted(_VISUAL_TYPE_MAP)}"
    )

# Map bracket page_type / template_variant → PageType enum.
# Both short forms ("T2") and full forms ("T2_Tactical_Variance", "T2_DriverBridge") are
# supported; resolution uses the first two characters of the key.
_PAGE_TYPE_MAP: Dict[str, PageType] = {
    "T1": PageType.T1_STRATEGIC_OVERVIEW,
    "T2": PageType.T2_TACTICAL_VARIANCE,
    "T3": PageType.T3_OPERATIONAL_MONITORING,
    "T4": PageType.T4_PRESCRIPTIVE_RECOMMENDATION,
}


def _resolve_page_type(raw: str) -> PageType:
    """Resolve a page_type or template_variant string to a PageType enum.

    Handles short ("T2") and long ("T2_Tactical_Variance", "T2_DriverBridge") forms.
    Falls back to T1 when the string is unrecognised.
    """
    family = (raw or "").strip()[:2].upper()
    return _PAGE_TYPE_MAP.get(family, PageType.T1_STRATEGIC_OVERVIEW)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _find_kpi_file(kpi_id: str, catalog_root: Path) -> Optional[Path]:
    """Glob for <kpi_id>.yaml anywhere under catalog_root."""
    filename = f"{kpi_id}.yaml"
    matches = list(catalog_root.rglob(filename))
    return matches[0] if matches else None


def _find_action_code_file(ac_id: str, action_codes_root: Path) -> Optional[Path]:
    """Find action code YAML anywhere under action_codes_root, skip decision_spines/."""
    if not action_codes_root.is_dir():
        return None
    for f in action_codes_root.rglob(f"{ac_id}.yaml"):
        if "decision_spines" not in f.parts:
            return f
    return None


def _format_threshold_value(val: Any, unit: str, metric: str = "") -> str:
    """Format threshold for display; avoid redundant units (e.g. metric ending in .amount)."""
    unit = (unit or "").strip()
    metric = (metric or "").strip()
    if unit and metric and (metric.endswith(f".{unit}") or metric.split(".")[-1] == unit):
        unit = ""
    if unit in ("%", "pp"):
        return f"{val}{unit}"
    if unit:
        return f"{val} {unit}"
    return str(val)


def _format_trigger(ac: Dict[str, Any]) -> Optional[str]:
    trigger = ac.get("trigger") or {}
    if not isinstance(trigger, dict):
        return None
    levels = trigger.get("levels") or {}
    if not isinstance(levels, dict):
        return None
    for level_key in ("L2", "L1", "L3"):
        level = levels.get(level_key)
        if not isinstance(level, dict):
            continue
        cond = level.get("condition") or {}
        if not isinstance(cond, dict):
            continue
        metric = cond.get("metric_kpi_id") or ""
        comp = cond.get("comparator") or ""
        th = cond.get("threshold")
        if isinstance(th, dict):
            val, unit = th.get("value"), (th.get("unit") or "")
        else:
            val, unit = th, ""
        if metric and comp and val is not None:
            comp_text = "<" if comp == "lt" else ">" if comp == "gt" else comp
            return f"{metric} {comp_text} {_format_threshold_value(val, unit, metric)}".strip()
    return None


def _format_impact(ac: Dict[str, Any]) -> Optional[str]:
    impact = ac.get("impact") or {}
    if isinstance(impact, dict) and impact.get("category"):
        cat = impact.get("category", "")
        val = ac.get("impact_valuation") or {}
        method = val.get("method", "") if isinstance(val, dict) else ""
        return f"Impact: {cat}, {method}" if method else f"Impact: {cat}"
    val = ac.get("impact_valuation") or {}
    if isinstance(val, dict) and val.get("method"):
        return f"Impact: {val.get('method')}"
    return None


def _measure_name_map(measures: List[MeasureSpec]) -> Dict[str, str]:
    return {m.kpi_id: m.name for m in measures}


def _resolve_measure_ref(ref: str, kpi_map: Dict[str, str]) -> str:
    if not ref:
        return ref
    return kpi_map.get(ref, ref)


def _component_measure_refs(comp: Dict[str, Any]) -> List[str]:
    kids = comp.get("kpi_ids") or []
    if not isinstance(kids, list):
        kids = [kids] if kids else []
    kid = comp.get("kpi_id")
    if kid:
        kids = [kid] + [k for k in kids if k != kid]
    return [str(k) for k in kids if k]


_EVIDENCE_DIM_TOKENS: Dict[str, tuple[str, str]] = {
    "entity": ("dim_org", "OrgName"),
    "region": ("dim_org", "Region"),
    "channel": ("dim_org", "Channel"),
    "product_category": ("dim_product", "Category"),
    "customer_segment": ("dim_customer", "Segment"),
}


def _resolve_evidence_columns(
    comp_300s: Dict[str, Any], kpi_map: Dict[str, str]
) -> tuple[List[str], List[str]]:
    cols_raw = comp_300s.get("evidence_columns") or []
    dim_cols: List[str] = []
    measures: List[str] = []
    for token in cols_raw:
        if not isinstance(token, str):
            continue
        if token in _EVIDENCE_DIM_TOKENS:
            table, col = _EVIDENCE_DIM_TOKENS[token]
            dim_cols.append(f"{table}.{col}")
        else:
            measures.append(_resolve_measure_ref(token, kpi_map))
    return dim_cols, measures


# Raster und Aufloesung leben ausschliesslich in `layer_tools/layout_grid.py`.
# Hier standen kurzzeitig zwei Weiterleitungen (`_grid_params`, `lu_to_pixels`) — bequem
# fuer die Umstellung, aber genau das, was konsolidiert werden sollte: zwei Namen fuer
# eine Sache. Sie sind entfernt; Aufrufer importieren den Leser direkt.


def _position(layout: Dict[str, Tuple[float, float, float, float]], slot: str) -> Position:
    """LU-Slot → `Position` des IR.

    Das IR fuehrt weiterhin Leinwandbrueche — daran haengen Adapter, die hier nicht
    umgebaut werden. Der Unterschied zu vorher ist aber grundlegend: die Brueche
    werden jetzt AUS den Logical Units gegen die Produktionsleinwand **abgeleitet**
    statt von Hand geschrieben. Damit gibt es nur noch eine Autorenquelle, und die
    Gutter gehen in die Rechnung ein.
    """
    from tooling.superversion.layer_tools.layout_grid import load, to_pixels

    lu = layout.get(slot, (0.0, 0.0, 1.0, 1.0))
    g = load("production")
    px = to_pixels(*lu, params=g)
    return Position(
        x=px["x"] / g.width,
        y=px["y"] / g.height,
        width=px["width"] / g.width,
        height=px["height"] / g.height,
    )


def _card_kpi_ids(bracket: Dict[str, Any]) -> List[str]:
    """KPI card band: component_3s lead + influencing KPIs, deduped, max 4."""
    ux = bracket.get("ux_layout_rules") or {}
    p1 = ux.get("page_1_summary") or {}
    c3s = p1.get("component_3s") if isinstance(p1, dict) else {}
    orch = bracket.get("orchestration") or {}
    lead = (c3s.get("kpi_id") if isinstance(c3s, dict) else None) or orch.get("strategic_kpi_id")
    influencing = orch.get("influencing_kpi_ids") or []
    out: List[str] = []
    seen: set = set()
    for kid in ([lead] if lead else []) + list(influencing):
        if not kid or kid in seen:
            continue
        seen.add(kid)
        out.append(str(kid))
        if len(out) >= 4:
            break
    return out


_UNIT_SYMBOL = {"pct": "%", "days": " days"}


def _format_benchmark_label(entry: Dict[str, Any], value: Any, basis: str) -> str:
    """Render the visible reference-label for a benchmark, honestly qualified.

    normative → "vs. world-class 85%"; empirical + peer segment → "vs. Retail peer 45";
    empirical fallback → "vs. cross-industry 44 (no sector match)". The label never
    presents a cross-industry average as if it were a peer benchmark — that honesty
    is the whole point of the normative/empirical split (K4).
    """
    sym = _UNIT_SYMBOL.get(entry.get("unit", ""), "")
    vs = f"{value:g}{sym}" if isinstance(value, (int, float)) and not isinstance(value, bool) else f"{value}{sym}"
    if basis == "universal":
        metric = entry.get("metric", "")
        label = "world-class" if metric == "world_class" else (metric or "benchmark")
        return f"vs. {label} {vs}"
    if isinstance(basis, str) and basis.startswith("segment:"):
        return f"vs. {basis.split(':', 1)[1]} peer {vs}"
    return f"vs. cross-industry {vs} (no sector match)"


def render_action_text(
    action_code_ids: List[str],
    action_codes_root: Path,
    payload_mode: str = "full",
    title: str = "Recommended actions (from action codes)",
) -> str:
    """Build ActionPanel display text from action code YAMLs."""
    lines: List[str] = [title, ""]
    for ac_id in action_code_ids:
        if not isinstance(ac_id, str) or not ac_id.strip():
            continue
        ac_id = ac_id.strip()
        ac_path = _find_action_code_file(ac_id, action_codes_root)
        if not ac_path:
            lines.append(f"• {ac_id} (definition not found)")
            lines.append("")
            continue
        ac = _load_yaml(ac_path)
        name = ac.get("name") or ac_id
        owner = ac.get("owner_role") or ac.get("owner") or "—"
        lines.append(f"• {ac_id} — {name}")
        lines.append(f"  Owner: {owner}")
        if payload_mode != "minimal":
            trigger_text = _format_trigger(ac)
            if trigger_text:
                lines.append(f"  Trigger: {trigger_text}")
            impact_text = _format_impact(ac)
            if impact_text:
                lines.append(f"  {impact_text}")
            impact = ac.get("impact") or {}
            if isinstance(impact, dict):
                rng = impact.get("expected_range") or {}
                if isinstance(rng, dict) and rng.get("value_low") is not None:
                    lo = rng.get("value_low")
                    hi = rng.get("value_high")
                    unit = (rng.get("unit") or "").strip()
                    range_str = f"{lo}–{hi} {unit}".strip()
                    lines.append(f"  Expected: {range_str}")
                conf = impact.get("confidence") or {}
                if isinstance(conf, dict) and conf.get("level"):
                    lines.append(f"  Confidence: {conf['level']}")
        if payload_mode == "full":
            exec_block = ac.get("operational_execution") or {}
            steps = exec_block.get("steps") or [] if isinstance(exec_block, dict) else []
            for step in list(steps)[:3]:
                if isinstance(step, str):
                    lines.append(f"  · {step}")
            gating = ac.get("trigger", {}).get("gating_rules") if isinstance(ac.get("trigger"), dict) else []
            if isinstance(gating, list) and gating:
                lines.append(f"  ⚠ {gating[0]}")
                if len(gating) > 1:
                    lines.append(f"  ⚠ {gating[1]}")
        lines.append("")
    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# Compiler
# ---------------------------------------------------------------------------

class CompilerWarning:
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class BracketCompiler:
    """
    Compiles a UseCase_Bracket.yaml into a DashboardSpec.

    Parameters
    ----------
    kpi_catalog_root
        Path to the KPI catalog directory (contains per-KPI YAML files).
    action_codes_root
        Path to action codes directory.
    target_adapter
        Which adapter the spec is intended for (default: PBIP).
    """

    def __init__(
        self,
        kpi_catalog_root: Path,
        action_codes_root: Path,
        target_adapter: AdapterTarget = AdapterTarget.PBIP,
        deployment_industry: Optional[str] = None,
        benchmarks_path: Optional[Path] = None,
    ) -> None:
        self.kpi_catalog_root = Path(kpi_catalog_root).resolve()
        self.action_codes_root = Path(action_codes_root).resolve()
        self.target_adapter = target_adapter
        # ALUCA is a library — the client's industry is a *deployment* parameter,
        # supplied when the library is deployed, not committed. It selects the
        # peer segment for empirical benchmarks (K4). None → cross-industry fallback.
        self.deployment_industry = deployment_industry
        self._benchmarks_path = (
            Path(benchmarks_path) if benchmarks_path
            else self.kpi_catalog_root / "benchmarks.yaml"
        )
        self.warnings: List[CompilerWarning] = []
        # Lazy, cached resolvers parsed from the real markdown sources.
        self._kpi_names: Optional[Dict[str, str]] = None
        self._mdict_by_name: Optional[Dict[str, List[dict]]] = None
        self._benchmarks: Optional[Dict[str, dict]] = None

    def _benchmark_reference(self, kpi_id: str) -> Optional[Dict[str, Any]]:
        """Resolve a hero KPI's benchmark to a visible, peer-relative reference-label.

        Reuses the governed resolver from tooling.validation.check_benchmarks (no
        second copy of the resolution logic — Golden Thread + Tool-Reuse). Returns
        None when the KPI has no governed benchmark, so the caller stays quiet.
        """
        if self._benchmarks is None:
            self._benchmarks = {}
            if self._benchmarks_path.is_file():
                data = yaml.safe_load(self._benchmarks_path.read_text(encoding="utf-8")) or {}
                for e in data.get("benchmarks", []) or []:
                    if e.get("kpi_id"):
                        self._benchmarks[e["kpi_id"]] = e
        entry = self._benchmarks.get(kpi_id)
        if not entry:
            return None
        from tooling.validation.check_benchmarks import resolve_benchmark  # noqa: PLC0415
        value, basis = resolve_benchmark(entry, self.deployment_industry or "")
        if value is None:
            return None
        return {
            "kpi_id": kpi_id,
            "value": value,
            "unit": entry.get("unit"),
            "basis": basis,
            "benchmark_class": entry.get("benchmark_class"),
            "label": _format_benchmark_label(entry, value, basis),
        }

    def _ensure_resolvers(self) -> None:
        if self._kpi_names is not None:
            return
        from .catalog_readers import load_kpi_catalog_names, load_measure_dictionary

        self._kpi_names = load_kpi_catalog_names(self.kpi_catalog_root / "KPI_Catalog.md")
        domains_dir = self.kpi_catalog_root.parent / "semantic_models" / "domains"
        self._mdict_by_name = load_measure_dictionary(domains_dir)

    def _resolve_measure(
        self, kpi_id: str, bracket: Dict, domain: str
    ) -> Optional[Tuple[str, str, str]]:
        """Resolve a kpi_id to ``(name, dax, display_folder)`` or ``None``.

        Resolution chain (first hit wins):
          1. per-KPI YAML file (legacy / unit-test fixtures)
          2. catalog display name (``kpi_key``) + DAX from the measure dictionary,
             preferring the entry in this use case's ``domain`` (so ``Gross Margin %``
             resolves to the Commercial measure, not the ``(XD)`` variant)
          3. catalog display name with a BLANK() placeholder + warning if no DAX

        Resolving by display name (not ``kpi_id``) guarantees the measure name
        matches what report visuals bind to -- the failure mode that produced the
        96 missing-measure criticals.
        """
        kpi_file = _find_kpi_file(kpi_id, self.kpi_catalog_root)
        if kpi_file:
            kpi = _load_yaml(kpi_file)
            # Only legacy fixtures carry an inline display name + DAX. Production
            # per-KPI catalog files use ``kpi_key`` + ``technical.measure_name``
            # and keep DAX in the measure dictionary, so fall through to the
            # display-name resolver (step 2) instead of short-circuiting to a
            # ``kpi_id`` name + ``BLANK()`` DAX.
            if "name" in kpi or "dax_expression" in kpi:
                return (
                    kpi.get("name", kpi_id),
                    kpi.get("dax_expression", "BLANK()"),
                    kpi.get("display_folder", bracket.get("id", "")),
                )

        self._ensure_resolvers()
        assert self._kpi_names is not None and self._mdict_by_name is not None

        display_name = self._kpi_names.get(kpi_id)
        if not display_name:
            return None

        entries = self._mdict_by_name.get(display_name, [])
        entry = next((e for e in entries if e["domain"] == domain), entries[0] if entries else None)
        if entry:
            return (display_name, entry["dax"], entry["display_folder"] or bracket.get("id", ""))

        self.warnings.append(CompilerWarning(
            "PLACEHOLDER_DAX",
            f"KPI '{kpi_id}' resolved to measure '{display_name}' but no DAX found in any "
            f"Measure_Dictionary; emitting BLANK() placeholder",
        ))
        return (display_name, "BLANK()", bracket.get("id", ""))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compile(self, bracket_path: Path) -> DashboardSpec:
        """Compile bracket YAML into a DashboardSpec."""
        self.warnings = []
        bracket_path = Path(bracket_path)
        if not self.action_codes_root.is_dir():
            self.warnings.append(CompilerWarning(
                "MISSING_ACTION_CODES_ROOT",
                f"Action codes root not found: {self.action_codes_root}",
            ))
        bracket = _load_yaml(bracket_path)

        use_case_id = bracket.get("id", bracket_path.parent.name.split("_")[0])
        domain = self._resolve_domain(bracket, use_case_id)
        title = bracket.get("title", use_case_id)
        semantic_model = f"{domain}.SemanticModel"

        measures = self._compile_measures(bracket, domain)
        kpi_map = _measure_name_map(measures)
        overview = self._compile_overview(bracket, kpi_map)
        detail, evidence_table, action_panel = self._compile_detail(bracket, use_case_id, kpi_map)

        return DashboardSpec(
            use_case_id=use_case_id,
            domain=domain,
            title=title,
            pages=[overview, detail],
            measures=measures,
            semantic_model=semantic_model,
            source_bracket=str(bracket_path),
            target_adapter=self.target_adapter,
            evidence_table=evidence_table,
            action_panel=action_panel,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # Domain resolution
    # ------------------------------------------------------------------

    def _resolve_domain(self, bracket: Dict, use_case_id: str) -> str:
        # Explicit domain field first
        if "domain" in bracket:
            return bracket["domain"]
        # Infer from use_case_id prefix
        prefix = use_case_id.split("-")[0].upper()
        _domain_map = {
            "COM": "Commercial",
            "FIN": "Finance",
            "OPS": "Operations",
            "SCM": "SupplyChain",
            "XD": "Experience",
        }
        return _domain_map.get(prefix, prefix.capitalize())

    # ------------------------------------------------------------------
    # Measures
    # ------------------------------------------------------------------

    def _compile_measures(self, bracket: Dict, domain: str) -> List[MeasureSpec]:
        specs: List[MeasureSpec] = []
        seen: set = set()

        # KPI IDs live under orchestration (Lean 2.0 bracket schema)
        orch = bracket.get("orchestration") or {}
        kpi_ids: List[str] = []
        strategic = orch.get("strategic_kpi_id")
        if strategic:
            kpi_ids.append(strategic)
        kpi_ids += orch.get("influencing_kpi_ids") or []
        kpi_ids += orch.get("supporting_kpi_ids") or []
        # Legacy top-level fields kept for backwards compatibility
        kpi_ids += bracket.get("primary_kpi_ids") or []
        kpi_ids += bracket.get("influencing_kpi_ids") or []

        for kpi_id in kpi_ids:
            if kpi_id in seen:
                continue
            seen.add(kpi_id)
            resolved = self._resolve_measure(kpi_id, bracket, domain)
            if resolved is None:
                self.warnings.append(CompilerWarning(
                    "MISSING_KPI", f"KPI '{kpi_id}' not found in catalog or measure dictionary"
                ))
                continue
            name, dax, folder = resolved
            specs.append(MeasureSpec(
                kpi_id=kpi_id,
                name=name,
                dax=dax,
                format_string="#,0",
                display_folder=folder,
            ))
        return specs

    # ------------------------------------------------------------------
    # Overview page
    # ------------------------------------------------------------------

    def _compile_overview(self, bracket: Dict, kpi_map: Dict[str, str]) -> PageSpec:
        ux = bracket.get("ux_layout_rules", {})
        page1 = ux.get("page_1_summary", {})
        # Prefer template_variant ("T2_DriverBridge") over page_type ("T2_Tactical_Variance")
        page_type_str = page1.get("template_variant") or page1.get("page_type") or "T1"
        page_type = _resolve_page_type(page_type_str)

        visuals: List[VisualSpec] = []

        # KPI cards: component_3s lead + influencing (deduped, max 4)
        kpi_measures = [
            _resolve_measure_ref(k, kpi_map) for k in _card_kpi_ids(bracket)
        ]
        c3s = page1.get("component_3s") if isinstance(page1, dict) else {}
        card_config: Dict[str, Any] = {}
        bench_ref: Optional[Dict[str, Any]] = None
        # Third comparison axis: a hero card opting into `benchmark: true` carries a
        # visible, peer-relative reference-label ("vs. Retail peer 45"), resolved from
        # the governed registry. The card itself keeps its primary comparison (vs_target).
        if isinstance(c3s, dict) and c3s.get("benchmark") is True and c3s.get("kpi_id"):
            bench_ref = self._benchmark_reference(str(c3s["kpi_id"]))
            if bench_ref is None:
                self.warnings.append(CompilerWarning(
                    "MISSING_BENCHMARK",
                    f"hero card opts into the benchmark axis but no governed benchmark "
                    f"for '{c3s['kpi_id']}' — reference-label omitted",
                ))
            else:
                card_config["benchmark_reference"] = bench_ref
        visuals.append(VisualSpec(
            id="KPI_Cards",
            visual_type=VisualType.KPI_CARD,
            page_role=PageRole.OVERVIEW,
            position=_position(_OVERVIEW_LU, "KPI_Cards"),
            binding=Binding(measures=kpi_measures),
            title=None,
            config=card_config,
            kpi_id=bench_ref["kpi_id"] if bench_ref else None,
        ))
        # Render the reference-label as its own caption textbox (the corpus-verified
        # text shape) — a card reference-*line* would need an unverified PBIR object.
        if bench_ref is not None:
            visuals.append(VisualSpec(
                id="Benchmark_Caption",
                visual_type=VisualType.TEXT_BOX,
                page_role=PageRole.OVERVIEW,
                position=_position(_OVERVIEW_LU, "Benchmark_Caption"),
                binding=Binding(),
                config={"text": bench_ref["label"], "align": "right"},
                kpi_id=bench_ref["kpi_id"],
            ))

        # Date slicer
        visuals.append(VisualSpec(
            id="Slicer_Date",
            visual_type=VisualType.SLICER,
            page_role=PageRole.OVERVIEW,
            position=_position(_OVERVIEW_LU, "Slicer_Date"),
            binding=Binding(filter_table="dim_date", filter_column="Date"),
        ))

        # 30s components from bracket
        comp_30s = page1.get("component_30s", [])
        if isinstance(comp_30s, list):
            for i, comp in enumerate(comp_30s[:3], 1):
                slot_id = f"Main_{i}"
                vt_str = comp.get("visual_type", "trend_line") if isinstance(comp, dict) else "trend_line"
                vt = _resolve_visual_type(vt_str, slot_id)
                measure_refs = [
                    _resolve_measure_ref(k, kpi_map) for k in _component_measure_refs(comp)
                ]
                category = (
                    comp.get("category_field") or comp.get("category", "dim_date.Date")
                    if isinstance(comp, dict) else "dim_date.Date"
                )
                if len(measure_refs) > 1:
                    binding = Binding(measures=measure_refs, category=category)
                elif len(measure_refs) == 1:
                    binding = Binding(measure=measure_refs[0], category=category)
                else:
                    binding = Binding(category=category)
                visuals.append(VisualSpec(
                    id=slot_id,
                    visual_type=vt,
                    page_role=PageRole.OVERVIEW,
                    position=_position(_OVERVIEW_LU, slot_id),
                    binding=binding,
                ))
        elif isinstance(comp_30s, dict):
            # Single object form
            vt_str = comp_30s.get("visual_type", "trend_line")
            vt = _VISUAL_TYPE_MAP.get(vt_str, VisualType.TREND_LINE)
            visuals.append(VisualSpec(
                id="Main_1",
                visual_type=vt,
                page_role=PageRole.OVERVIEW,
                position=_position(_OVERVIEW_LU, "Main_1"),
                binding=Binding(category="dim_date.Date"),
            ))

        return PageSpec(
            id="Overview",
            display_name="Overview",
            role=PageRole.OVERVIEW,
            page_type=page_type,
            visuals=visuals,
            order=0,
        )

    # ------------------------------------------------------------------
    # Detail page
    # ------------------------------------------------------------------

    def _compile_detail(
        self, bracket: Dict, use_case_id: str, kpi_map: Dict[str, str]
    ) -> Tuple[PageSpec, Optional[EvidenceTableSpec], Optional[ActionPanelSpec]]:
        ux = bracket.get("ux_layout_rules", {})
        page2 = ux.get("page_2_execution", {})
        comp_300s = page2.get("component_300s", {}) if isinstance(page2, dict) else {}

        visuals: List[VisualSpec] = []

        # Slicer pane
        visuals.append(VisualSpec(
            id="Slicer_Pane",
            visual_type=VisualType.SLICER,
            page_role=PageRole.DETAIL,
            position=_position(_DETAIL_LU, "Slicer_Pane"),
            binding=Binding(filter_table="dim_org", filter_column="OrgName"),
        ))

        # Smart narrative
        visuals.append(VisualSpec(
            id="Smart_Narrative",
            visual_type=VisualType.SMART_NARRATIVE,
            page_role=PageRole.DETAIL,
            position=_position(_DETAIL_LU, "Smart_Narrative"),
            binding=Binding(),
        ))

        # Evidence / detail matrix
        evidence_table: Optional[EvidenceTableSpec] = None
        # evidence_grain may be a top-level key or inside component_300s
        eg = bracket.get("evidence_grain") or (
            {"grain": comp_300s.get("evidence_grain")}
            if isinstance(comp_300s, dict) and comp_300s.get("evidence_grain")
            else {}
        )
        # Die governte Evidenz-Sortierung steht bei ALLEN 20 Brackets unter
        # `component_300s.sort_by` — bei keinem unter `evidence_grain.sort_by`. Der
        # Compiler las bis 01.08.2026 nur letzteres und liess die Sortierung damit
        # ausnahmslos fallen. Sichtbar wurde das als `knockout-unsorted-evidence`;
        # kaschiert hat es, dass 14 dist-Reports die sortDefinition von Hand
        # nachgetragen bekamen — der Generator erzeugte sie nie.
        # Reihenfolge: eine explizite `evidence_grain.sort_by` gewinnt, sonst das
        # Bracket. Damit bleibt der bisher gemeinte Weg gueltig, ohne den tatsaechlich
        # benutzten zu ignorieren.
        if isinstance(comp_300s, dict) and comp_300s.get("sort_by") and not eg.get("sort_by"):
            eg = {**eg, "sort_by": comp_300s["sort_by"]}
        _detail_measures = [
            _resolve_measure_ref(k, kpi_map) for k in _card_kpi_ids(bracket)
        ]
        _detail_columns: List[str] = []
        if isinstance(comp_300s, dict) and comp_300s.get("evidence_columns"):
            _detail_columns, _detail_measures = _resolve_evidence_columns(comp_300s, kpi_map)
        # Legacy fallback
        if not _detail_measures:
            _detail_measures = [
                _resolve_measure_ref(k, kpi_map)
                for k in (bracket.get("primary_kpi_ids") or [])
            ]
        if eg:
            cols = _detail_columns or eg.get("columns", [])
            grain = eg.get("grain", "")
            evidence_table = EvidenceTableSpec(
                grain=grain,
                columns=cols,
                measures=_detail_measures,
                sort_by=eg.get("sort_by"),
                limit=eg.get("limit", 500),
                data_bars=eg.get("data_bars", False),
            )
            visuals.append(VisualSpec(
                id="Detail_Matrix",
                visual_type=VisualType.MATRIX,
                page_role=PageRole.DETAIL,
                position=_position(_DETAIL_LU, "Detail_Matrix"),
                binding=Binding(
                    columns=cols,
                    measures=_detail_measures,
                    sort_by=eg.get("sort_by"),
                ),
            ))

        # Action panel
        action_panel: Optional[ActionPanelSpec] = None
        ap_enabled = False
        if isinstance(comp_300s, dict):
            ap_enabled = comp_300s.get("action_panel", False)
        elif isinstance(comp_300s, list):
            ap_enabled = any(
                (c.get("action_panel") if isinstance(c, dict) else False)
                for c in comp_300s
            )

        if ap_enabled:
            ac_ids: List[str] = (
                bracket.get("orchestration", {}).get("action_code_ids", [])
            )
            mode = "full"
            if isinstance(comp_300s, dict):
                mode = comp_300s.get("payload_mode", "full")
            rendered = ""
            if ac_ids:
                try:
                    rendered = render_action_text(
                        ac_ids, self.action_codes_root, mode
                    )
                except Exception as exc:
                    self.warnings.append(CompilerWarning(
                        "ACTION_PANEL_RENDER",
                        f"Failed to render action panel text: {exc}",
                    ))
            action_panel = ActionPanelSpec(
                enabled=True,
                action_code_ids=ac_ids,
                payload_mode=mode,
                rendered_text=rendered,
            )
            visuals.append(VisualSpec(
                id="ActionPanel",
                visual_type=VisualType.ACTION_PANEL,
                page_role=PageRole.DETAIL,
                position=_position(_DETAIL_LU, "ActionPanel"),
                binding=Binding(),
                config={"text": rendered},
                action_code_id=ac_ids[0] if ac_ids else None,
            ))

        return (
            PageSpec(
                id="Detail",
                display_name="Detail",
                role=PageRole.DETAIL,
                page_type=PageType.T4_PRESCRIPTIVE_RECOMMENDATION,
                visuals=visuals,
                order=1,
            ),
            evidence_table,
            action_panel,
        )
