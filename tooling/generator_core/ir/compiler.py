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

import re
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
_OVERVIEW_LAYOUT: Dict[str, Dict[str, float]] = {
    "KPI_Cards":   {"x": 0.0,    "y": 0.0,    "w": 0.80,  "h": 0.18},
    "Slicer_Date": {"x": 0.80,   "y": 0.0,    "w": 0.20,  "h": 0.18},
    "Main_1":      {"x": 0.0,    "y": 0.19,   "w": 0.50,  "h": 0.40},
    "Main_2":      {"x": 0.50,   "y": 0.19,   "w": 0.50,  "h": 0.40},
    "Main_3":      {"x": 0.0,    "y": 0.60,   "w": 1.00,  "h": 0.40},
}

# Detail page layout
_DETAIL_LAYOUT: Dict[str, Dict[str, float]] = {
    "Slicer_Pane":     {"x": 0.0,    "y": 0.0,    "w": 0.16,  "h": 1.00},
    "Smart_Narrative": {"x": 0.165,  "y": 0.0,    "w": 0.55,  "h": 0.18},
    "Detail_Matrix":   {"x": 0.165,  "y": 0.19,   "w": 0.61,  "h": 0.81},
    "ActionPanel":     {"x": 0.78,   "y": 0.0,    "w": 0.22,  "h": 1.00},
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

# Map bracket page_type → PageType enum
_PAGE_TYPE_MAP: Dict[str, PageType] = {
    "T1": PageType.T1_STRATEGIC_OVERVIEW,
    "T2": PageType.T2_TACTICAL_VARIANCE,
    "T3": PageType.T3_OPERATIONAL_MONITORING,
    "T4": PageType.T4_PRESCRIPTIVE_RECOMMENDATION,
}


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
    for f in action_codes_root.rglob(f"{ac_id}.yaml"):
        if "decision_spines" not in str(f):
            return f
    return None


def _position(layout: Dict[str, Dict[str, float]], slot: str) -> Position:
    g = layout.get(slot, {"x": 0.0, "y": 0.0, "w": 0.1, "h": 0.1})
    return Position(x=g["x"], y=g["y"], width=g["w"], height=g["h"])


def _render_action_text(
    action_code_ids: List[str],
    action_codes_root: Path,
    payload_mode: str = "full",
    title: str = "Recommended Actions",
) -> str:
    """Build ActionPanel display text from action code YAMLs."""
    lines: List[str] = [f"=== {title} ===", ""]
    for ac_id in action_code_ids:
        ac_path = _find_action_code_file(ac_id, action_codes_root)
        if not ac_path:
            lines.append(f"[{ac_id}: not found]")
            lines.append("")
            continue
        ac = _load_yaml(ac_path)
        name = ac.get("name", ac_id)
        owner = ac.get("owner", "")
        lines.append(f"[{ac_id}] {name}")
        if owner:
            lines.append(f"Owner: {owner}")
        if payload_mode in ("full", "summary"):
            # Trigger condition
            trigger = ac.get("trigger", {})
            for lvl in ("L1", "L2", "L3"):
                cond = trigger.get("levels", {}).get(lvl, {}).get("condition", "")
                if cond:
                    lines.append(f"Trigger ({lvl}): {cond}")
                    break
            # Impact
            impact = ac.get("impact", {})
            impact_cat = impact.get("category", "")
            impact_val = ac.get("impact_valuation", {}).get("method", "")
            if impact_cat:
                lines.append(f"Impact: {impact_cat}" + (f" ({impact_val})" if impact_val else ""))
        if payload_mode == "full":
            steps = ac.get("operational_execution", {}).get("steps", [])
            for i, step in enumerate(steps[:3], 1):
                step_text = step if isinstance(step, str) else step.get("description", str(step))
                lines.append(f"  {i}. {step_text}")
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
        self.kpi_catalog_root = Path(kpi_catalog_root)
        self.action_codes_root = Path(action_codes_root)
        self.target_adapter = target_adapter
        self.warnings: List[CompilerWarning] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compile(self, bracket_path: Path) -> DashboardSpec:
        """Compile bracket YAML into a DashboardSpec."""
        self.warnings = []
        bracket_path = Path(bracket_path)
        bracket = _load_yaml(bracket_path)

        use_case_id = bracket.get("id", bracket_path.parent.name.split("_")[0])
        domain = self._resolve_domain(bracket, use_case_id)
        title = bracket.get("title", use_case_id)
        semantic_model = f"{domain}.SemanticModel"

        measures = self._compile_measures(bracket)
        overview = self._compile_overview(bracket)
        detail, evidence_table, action_panel = self._compile_detail(bracket, use_case_id)

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

    def _compile_measures(self, bracket: Dict) -> List[MeasureSpec]:
        specs: List[MeasureSpec] = []
        seen: set = set()

        kpi_ids: List[str] = []
        kpi_ids += bracket.get("primary_kpi_ids", [])
        kpi_ids += bracket.get("influencing_kpi_ids", [])

        for kpi_id in kpi_ids:
            if kpi_id in seen:
                continue
            seen.add(kpi_id)
            kpi_file = _find_kpi_file(kpi_id, self.kpi_catalog_root)
            if not kpi_file:
                self.warnings.append(CompilerWarning(
                    "MISSING_KPI", f"KPI '{kpi_id}' not found in catalog"
                ))
                continue
            kpi = _load_yaml(kpi_file)
            name = kpi.get("name", kpi_id)
            dax = kpi.get("dax_expression", f"// TODO: DAX for {kpi_id}")
            fmt = kpi.get("format_string", "#,0")
            folder = kpi.get("display_folder", bracket.get("id", ""))
            specs.append(MeasureSpec(
                kpi_id=kpi_id,
                name=name,
                dax=dax,
                format_string=fmt,
                display_folder=folder,
            ))
        return specs

    # ------------------------------------------------------------------
    # Overview page
    # ------------------------------------------------------------------

    def _compile_overview(self, bracket: Dict) -> PageSpec:
        ux = bracket.get("ux_layout_rules", {})
        page1 = ux.get("page_1_summary", {})
        page_type_str = page1.get("page_type", "T1")
        page_type = _PAGE_TYPE_MAP.get(page_type_str, PageType.T1_STRATEGIC_OVERVIEW)

        visuals: List[VisualSpec] = []

        # KPI cards
        kpi_measures = [k for k in bracket.get("primary_kpi_ids", [])]
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
                measure = (comp.get("kpi_id") or comp.get("measure", "")) if isinstance(comp, dict) else ""
                category = (comp.get("category", "dim_date.Date")) if isinstance(comp, dict) else "dim_date.Date"
                visuals.append(VisualSpec(
                    id=slot_id,
                    visual_type=vt,
                    page_role=PageRole.OVERVIEW,
                    position=_position(_OVERVIEW_LAYOUT, slot_id),
                    binding=Binding(measure=measure or None, category=category),
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
        self, bracket: Dict, use_case_id: str
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
        eg = bracket.get("evidence_grain", {})
        if eg:
            cols = eg.get("columns", [])
            grain = eg.get("grain", "")
            evidence_table = EvidenceTableSpec(
                grain=grain,
                columns=cols,
                measures=bracket.get("primary_kpi_ids", []),
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
                    measures=bracket.get("primary_kpi_ids", []),
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
