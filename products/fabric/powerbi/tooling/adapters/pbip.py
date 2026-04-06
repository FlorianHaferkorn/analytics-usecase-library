"""
PBIP Adapter — renders DashboardSpec to Power BI PBIP folder structure.

Lives in products/fabric/powerbi/ because it encodes Power BI-specific
knowledge (PBIP schema URLs, visualType strings, canvas dimensions, TMDL
format). The generator_core framework only knows the abstract GeneratorAdapter
interface — this is the concrete PBI implementation.

Canvas size: 1280 × 720 (Power BI default widescreen)
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from tooling.generator_core.adapters.base import GeneratorAdapter, RenderResult
from tooling.generator_core.ir.specs import (
    AdapterTarget,
    Binding,
    DashboardSpec,
    MeasureSpec,
    PageRole,
    PageSpec,
    Position,
    VisualSpec,
    VisualType,
)

# Power BI canvas dimensions in pixels
_CANVAS_W = 1280
_CANVAS_H = 720

# PBIP schema constants
_REPORT_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/1.0.0/schema.json"
_PAGE_SCHEMA   = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/1.0.0/schema.json"
_VISUAL_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/1.2.0/schema.json"
_PAGES_SCHEMA  = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pages/1.0.0/schema.json"

# IR VisualType → Power BI PBIP visualType strings
_VISUAL_TYPE_MAP: Dict[VisualType, List[str]] = {
    VisualType.KPI_CARD:        ["cardVisual", "kpiVisual", "card"],
    VisualType.TREND_LINE:      ["lineChart", "lineClusteredColumnComboChart"],
    VisualType.BAR_CHART:       ["clusteredBarChart", "clusteredColumnChart", "barChart"],
    VisualType.WATERFALL:       ["waterfallChart"],
    VisualType.SCATTER:         ["scatterChart"],
    VisualType.MATRIX:          ["pivotTable"],
    VisualType.TABLE:           ["tableEx"],
    VisualType.SLICER:          ["slicer"],
    VisualType.SMART_NARRATIVE: ["smartNarrativeVisual"],
    VisualType.ACTION_PANEL:    ["textbox"],
    VisualType.TEXT_BOX:        ["textbox"],
}

# IR VisualType → queryState role names (Power BI field-well roles)
_QUERY_ROLE_MAP: Dict[VisualType, Dict[str, str]] = {
    VisualType.TREND_LINE:  {"measure": "Y", "category": "Category"},
    VisualType.BAR_CHART:   {"measure": "Y", "category": "Category"},
    VisualType.WATERFALL:   {"measure": "Y", "category": "Category"},
    VisualType.SCATTER:     {"measure": "Y", "category": "X"},
    VisualType.MATRIX:      {"measure": "Values", "category": "Rows"},
    VisualType.TABLE:       {"measure": "Values", "category": "Values"},
    VisualType.KPI_CARD:    {"measure": "Data"},
    VisualType.SLICER:      {"category": "Field"},
}


# ---------------------------------------------------------------------------
# Private rendering helpers
# ---------------------------------------------------------------------------

def _px(pos: Position) -> Dict[str, int]:
    return {
        "x": round(pos.x * _CANVAS_W),
        "y": round(pos.y * _CANVAS_H),
        "width":  round(pos.width  * _CANVAS_W),
        "height": round(pos.height * _CANVAS_H),
    }


def _entity_ref(table: str, column: str) -> Dict[str, Any]:
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": column}}


def _measure_ref(measure_name: str) -> Dict[str, Any]:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": measure_name}}


def _projection(field_expr: Dict, query_ref: str, native_ref: str) -> Dict[str, Any]:
    return {"field": field_expr, "queryRef": query_ref, "nativeQueryRef": native_ref}


def _build_query_state(vspec: VisualSpec) -> Dict[str, Any]:
    qs: Dict[str, Any] = {}
    role_map = _QUERY_ROLE_MAP.get(vspec.visual_type, {})
    b = vspec.binding

    if b.measures:
        role = role_map.get("measure", "Data")
        qs[role] = {"projections": [_projection(_measure_ref(m), f"_Measures.{m}", m) for m in b.measures]}
    elif b.measure:
        role = role_map.get("measure", "Data")
        qs[role] = {"projections": [_projection(_measure_ref(b.measure), f"_Measures.{b.measure}", b.measure)]}

    if b.category:
        parts = b.category.split(".")
        table, col = (parts[0], parts[1]) if len(parts) == 2 else ("dim_date", parts[0])
        role = role_map.get("category", "Category")
        qs[role] = {"projections": [_projection(_entity_ref(table, col), f"{table}.{col}", col)]}

    if b.filter_column and vspec.visual_type == VisualType.SLICER:
        table = b.filter_table or "dim_date"
        qs["Field"] = {"projections": [_projection(_entity_ref(table, b.filter_column), f"{table}.{b.filter_column}", b.filter_column)]}

    if b.columns and vspec.visual_type in (VisualType.MATRIX, VisualType.TABLE):
        projections = []
        for col_ref in b.columns:
            parts = col_ref.split(".")
            t, c = (parts[0], parts[1]) if len(parts) == 2 else ("dim_org", col_ref)
            projections.append(_projection(_entity_ref(t, c), f"{t}.{c}", c))
        qs["Rows"] = {"projections": projections}

    return qs


def _build_visual_json(vspec: VisualSpec) -> Dict[str, Any]:
    pbip_type = _VISUAL_TYPE_MAP.get(vspec.visual_type, ["cardVisual"])[0]
    visual: Dict[str, Any] = {
        "$schema": _VISUAL_SCHEMA,
        "name": vspec.id,
        "position": _px(vspec.position),
        "visual": {
            "visualType": pbip_type,
            "query": {"queryState": _build_query_state(vspec)},
        },
    }
    if vspec.visual_type == VisualType.ACTION_PANEL:
        visual["visual"]["visualType"] = "textbox"
        visual["visual"]["objects"] = {
            "general": [{"properties": {"paragraphs": [{"textRuns": [{"value": vspec.config.get("text", "")}]}]}}]
        }
    if vspec.visual_type == VisualType.SMART_NARRATIVE:
        visual["visual"]["visualType"] = "smartNarrativeVisual"
    return visual


def _build_page_json(page: PageSpec) -> Dict[str, Any]:
    return {
        "$schema": _PAGE_SCHEMA,
        "name": page.id,
        "displayName": page.display_name,
        "displayOption": 1,
        "width": _CANVAS_W,
        "height": _CANVAS_H,
        "background": {"transparency": 100},
        "ordinal": page.order,
    }


def _build_pages_json(pages: List[PageSpec]) -> Dict[str, Any]:
    return {
        "$schema": _PAGES_SCHEMA,
        "pageOrder": [p.id for p in pages],
        "activePageName": pages[0].id if pages else "",
    }


def _build_report_json(spec: DashboardSpec) -> Dict[str, Any]:
    return {
        "$schema": _REPORT_SCHEMA,
        "themeCollection": {"baseTheme": {"name": "CY24SU06"}},
        "settings": {"useStylableVisualContainerHeader": True},
    }


def _build_definition_pbir(semantic_model: str) -> Dict[str, Any]:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../../{semantic_model}"}},
    }


def _build_tmdl_measures(measures: List[MeasureSpec]) -> str:
    t1, t2 = "\t", "\t\t"
    lines: List[str] = [
        "table _Measures",
        f"{t1}partition _Measures = m",
        f"{t2}mode: import",
        f"{t2}source",
        f"{t2}\tlet",
        f"{t2}\t\tSource = Table.FromRows({{}})",
        f"{t2}\tin",
        f"{t2}\t\tSource",
        "",
        f"{t1}isHidden",
        "",
    ]
    for m in measures:
        dax = " ".join(m.dax.split())
        lines += [
            f"{t1}/// Purpose: {m.description or m.name}",
            f"{t1}measure '{m.name}' = {dax}",
            f'{t2}formatString: "{m.format_string}"',
        ]
        if m.display_folder:
            lines.append(f'{t2}displayFolder: "{m.display_folder}"')
        if m.is_hidden:
            lines.append(f"{t2}isHidden")
        for k, v in m.annotations.items():
            lines.append(f"{t2}annotation {k} = {v}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# PBIPAdapter — the concrete Power BI implementation of GeneratorAdapter
# ---------------------------------------------------------------------------

class PBIPAdapter(GeneratorAdapter):
    """
    Renders a DashboardSpec to Power BI PBIP folder structure.

    This is a Power BI-specific class. It knows about PBIP schemas, TMDL
    syntax, Power BI visualType strings, and queryState field-well roles.
    Nothing here should ever be referenced by the OSS generator.

    Output layout (relative to dist/):
        <ID>.Report/
            definition.pbir
            definition/
                report.json
                pages/pages.json
                Overview/page.json + visuals/<slot>/visual.json
                Detail/page.json   + visuals/<slot>/visual.json
        <Domain>.SemanticModel/definition/tables/_Measures.tmdl
    """

    @property
    def name(self) -> str:
        return "pbip"

    @property
    def target(self) -> AdapterTarget:
        return AdapterTarget.PBIP

    def visual_type_map(self) -> Dict[VisualType, List[str]]:
        return _VISUAL_TYPE_MAP

    def validate_ir(self, spec: DashboardSpec) -> List[str]:
        errors: List[str] = []
        overview = spec.overview_page()
        detail   = spec.detail_page()
        if not overview:
            errors.append("IR missing Overview page")
        elif not overview.visual_by_id("KPI_Cards"):
            errors.append("Overview page missing KPI_Cards visual")
        elif not overview.visual_by_id("KPI_Cards").binding.measures:
            errors.append("KPI_Cards binding has no measures")
        if not detail:
            errors.append("IR missing Detail page")
        elif not detail.visual_by_id("Smart_Narrative"):
            errors.append("Detail page missing Smart_Narrative visual")
        if not spec.semantic_model:
            errors.append("DashboardSpec.semantic_model is empty")
        return errors

    def render(self, spec: DashboardSpec) -> RenderResult:
        files: Dict[str, bytes] = {}
        report_name = f"{spec.use_case_id}.Report"

        def _json(obj: Any) -> bytes:
            return json.dumps(obj, indent=2, ensure_ascii=False).encode("utf-8")

        files[f"{report_name}/definition.pbir"]            = _json(_build_definition_pbir(spec.semantic_model))
        files[f"{report_name}/definition/report.json"]     = _json(_build_report_json(spec))
        files[f"{report_name}/definition/pages/pages.json"] = _json(_build_pages_json(spec.pages))

        for page in spec.pages:
            base = f"{report_name}/definition/pages/{page.id}"
            files[f"{base}/page.json"] = _json(_build_page_json(page))
            for vspec in page.visuals:
                files[f"{base}/visuals/{vspec.id}/visual.json"] = _json(_build_visual_json(vspec))

        if spec.measures:
            files[f"{spec.semantic_model}/definition/tables/_Measures.tmdl"] = (
                _build_tmdl_measures(spec.measures).encode("utf-8")
            )

        return RenderResult(files=files, adapter=self.name)
