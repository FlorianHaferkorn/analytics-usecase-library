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
* All IR position values are in canvas-fraction units (0.0–1.0).
  The PBIP adapter scales them to the 1280×720 Power BI canvas.
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
# Canvas layout constants (fraction-based grid)
# ---------------------------------------------------------------------------

# Overview page layout (fraction of 1280×720 canvas)
# Layout uses fractional coordinates (0–1) relative to a 1920 × 1080 canvas.
# 32px margin = 32/1920 ≈ 0.0167 horizontal, 32/1080 ≈ 0.0296 vertical.
# KPI band: y=0.0296–0.174 (≈156 px tall), Main row: y=0.218 onward.
_OVERVIEW_LAYOUT: Dict[str, Dict[str, float]] = {
    # KPI card band: full width minus 32 px margins each side; height ≈156 px
    "KPI_Cards":   {"x": 0.0167, "y": 0.0296, "w": 0.9666, "h": 0.1444},
    # Date slicer below KPI band; same horizontal span; height ≈70 px
    "Slicer_Date": {"x": 0.0167, "y": 0.189,  "w": 0.9666, "h": 0.0648},
    # Three equal-width main chart columns, below slicer; height ≈750 px
    "Main_1":      {"x": 0.0167, "y": 0.268,  "w": 0.3111, "h": 0.694},
    "Main_2":      {"x": 0.3444, "y": 0.268,  "w": 0.3111, "h": 0.694},
    "Main_3":      {"x": 0.6722, "y": 0.268,  "w": 0.3111, "h": 0.694},
}

# Detail page layout: slicer pane (left), narrative + matrix (centre), action panel (right)
_DETAIL_LAYOUT: Dict[str, Dict[str, float]] = {
    "Slicer_Pane":     {"x": 0.0167, "y": 0.0296, "w": 0.1333, "h": 0.9407},
    "Smart_Narrative": {"x": 0.1667, "y": 0.0296, "w": 0.6389, "h": 0.0926},
    "Detail_Matrix":   {"x": 0.1667, "y": 0.137,  "w": 0.6389, "h": 0.833},
    "ActionPanel":     {"x": 0.8222, "y": 0.0296, "w": 0.1611, "h": 0.9407},
}

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
}

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


def _position(layout: Dict[str, Dict[str, float]], slot: str) -> Position:
    g = layout.get(slot, {"x": 0.0, "y": 0.0, "w": 0.1, "h": 0.1})
    return Position(x=g["x"], y=g["y"], width=g["w"], height=g["h"])


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


def _render_action_text(
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
    ) -> None:
        self.kpi_catalog_root = Path(kpi_catalog_root).resolve()
        self.action_codes_root = Path(action_codes_root).resolve()
        self.target_adapter = target_adapter
        self.warnings: List[CompilerWarning] = []
        # Lazy, cached resolvers parsed from the real markdown sources.
        self._kpi_names: Optional[Dict[str, str]] = None
        self._mdict_by_name: Optional[Dict[str, List[dict]]] = None

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
        visuals.append(VisualSpec(
            id="KPI_Cards",
            visual_type=VisualType.KPI_CARD,
            page_role=PageRole.OVERVIEW,
            position=_position(_OVERVIEW_LAYOUT, "KPI_Cards"),
            binding=Binding(measures=kpi_measures),
            title=None,
        ))

        # Date slicer
        visuals.append(VisualSpec(
            id="Slicer_Date",
            visual_type=VisualType.SLICER,
            page_role=PageRole.OVERVIEW,
            position=_position(_OVERVIEW_LAYOUT, "Slicer_Date"),
            binding=Binding(filter_table="dim_date", filter_column="Date"),
        ))

        # 30s components from bracket
        comp_30s = page1.get("component_30s", [])
        if isinstance(comp_30s, list):
            for i, comp in enumerate(comp_30s[:3], 1):
                slot_id = f"Main_{i}"
                vt_str = comp.get("visual_type", "trend_line") if isinstance(comp, dict) else "trend_line"
                vt = _VISUAL_TYPE_MAP.get(vt_str, VisualType.TREND_LINE)
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
                    position=_position(_OVERVIEW_LAYOUT, slot_id),
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
                position=_position(_OVERVIEW_LAYOUT, "Main_1"),
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
            position=_position(_DETAIL_LAYOUT, "Slicer_Pane"),
            binding=Binding(filter_table="dim_org", filter_column="OrgName"),
        ))

        # Smart narrative
        visuals.append(VisualSpec(
            id="Smart_Narrative",
            visual_type=VisualType.SMART_NARRATIVE,
            page_role=PageRole.DETAIL,
            position=_position(_DETAIL_LAYOUT, "Smart_Narrative"),
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
                position=_position(_DETAIL_LAYOUT, "Detail_Matrix"),
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
                    rendered = _render_action_text(
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
                position=_position(_DETAIL_LAYOUT, "ActionPanel"),
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
