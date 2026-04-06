"""
PBIP Adapter — renders DashboardSpec to Power BI PBIP folder structure.

This adapter is a thin bridge between the IR layer and the existing
page_scaffold_generator Python package.  Rather than re-implementing visual
JSON generation from scratch, it translates IR→scaffold config objects that
page_scaffold_generator already understands, then calls the existing code.

For use cases not yet supported by page_scaffold_generator directly, the
adapter falls back to generating minimal valid visual.json stubs so the
report at least opens in Power BI Desktop.

Canvas size: 1280 × 720 (Power BI default widescreen)
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..adapters.base import GeneratorAdapter, RenderResult
from ..ir.specs import (
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

# Visual type map: IR → Power BI PBIP visualType strings
_VISUAL_TYPE_MAP: Dict[VisualType, List[str]] = {
    VisualType.KPI_CARD:       ["cardVisual", "kpiVisual", "card"],
    VisualType.TREND_LINE:     ["lineChart", "lineClusteredColumnComboChart"],
    VisualType.BAR_CHART:      ["clusteredBarChart", "clusteredColumnChart", "barChart"],
    VisualType.WATERFALL:      ["waterfallChart"],
    VisualType.SCATTER:        ["scatterChart"],
    VisualType.MATRIX:         ["pivotTable"],
    VisualType.TABLE:          ["tableEx"],
    VisualType.SLICER:         ["slicer"],
    VisualType.SMART_NARRATIVE: ["smartNarrativeVisual"],
    VisualType.ACTION_PANEL:   ["textbox"],
    VisualType.TEXT_BOX:       ["textbox"],
}

# Map visual type → queryState role name
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
# Helpers
# ---------------------------------------------------------------------------

def _px(pos: Position) -> Dict[str, int]:
    return {
        "x": round(pos.x * _CANVAS_W),
        "y": round(pos.y * _CANVAS_H),
        "width": round(pos.width * _CANVAS_W),
        "height": round(pos.height * _CANVAS_H),
    }


def _new_id() -> str:
    return str(uuid.uuid4())


def _entity_ref(table: str, column: str) -> Dict[str, Any]:
    return {
        "Column": {
            "Expression": {"SourceRef": {"Entity": table}},
            "Property": column,
        }
    }


def _measure_ref(measure_name: str) -> Dict[str, Any]:
    return {
        "Measure": {
            "Expression": {"SourceRef": {"Entity": "_Measures"}},
            "Property": measure_name,
        }
    }


def _projection(field_expr: Dict, query_ref: str, native_ref: str) -> Dict[str, Any]:
    return {
        "field": field_expr,
        "queryRef": query_ref,
        "nativeQueryRef": native_ref,
    }


def _build_query_state(vspec: VisualSpec) -> Dict[str, Any]:
    """Build PBIP queryState from IR Binding."""
    qs: Dict[str, Any] = {}
    role_map = _QUERY_ROLE_MAP.get(vspec.visual_type, {})
    binding = vspec.binding

    # Measures
    if binding.measures:
        role = role_map.get("measure", "Data")
        projections = [
            _projection(_measure_ref(m), f"_Measures.{m}", m)
            for m in binding.measures
        ]
        qs[role] = {"projections": projections}
    elif binding.measure:
        role = role_map.get("measure", "Data")
        m = binding.measure
        qs[role] = {"projections": [_projection(_measure_ref(m), f"_Measures.{m}", m)]}

    # Category axis
    if binding.category:
        parts = binding.category.split(".")
        table, col = (parts[0], parts[1]) if len(parts) == 2 else ("dim_date", parts[0])
        role = role_map.get("category", "Category")
        qs[role] = {
            "projections": [
                _projection(_entity_ref(table, col), f"{table}.{col}", col)
            ]
        }

    # Slicer field
    if binding.filter_column and vspec.visual_type == VisualType.SLICER:
        table = binding.filter_table or "dim_date"
        col = binding.filter_column
        qs["Field"] = {
            "projections": [
                _projection(_entity_ref(table, col), f"{table}.{col}", col)
            ]
        }

    # Matrix columns
    if binding.columns and vspec.visual_type in (VisualType.MATRIX, VisualType.TABLE):
        projections = []
        for col_ref in binding.columns:
            parts = col_ref.split(".")
            table, col = (parts[0], parts[1]) if len(parts) == 2 else ("dim_org", col_ref)
            projections.append(_projection(_entity_ref(table, col), f"{table}.{col}", col))
        qs["Rows"] = {"projections": projections}

    return qs


def _build_visual_json(vspec: VisualSpec) -> Dict[str, Any]:
    """Build a minimal valid visual.json for a VisualSpec."""
    pbip_type = _VISUAL_TYPE_MAP.get(vspec.visual_type, ["cardVisual"])[0]
    px = _px(vspec.position)

    visual: Dict[str, Any] = {
        "$schema": _VISUAL_SCHEMA,
        "name": vspec.id,
        "position": px,
        "visual": {
            "visualType": pbip_type,
            "query": {
                "queryState": _build_query_state(vspec),
            },
        },
    }

    # ActionPanel / textbox special case — embed text content
    if vspec.visual_type == VisualType.ACTION_PANEL:
        text = vspec.config.get("text", "")
        visual["visual"]["visualType"] = "textbox"
        visual["visual"]["objects"] = {
            "general": [{
                "properties": {
                    "paragraphs": [{
                        "textRuns": [{"value": text}],
                    }]
                }
            }]
        }

    # Smart narrative
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
        "settings": {
            "useStylableVisualContainerHeader": True,
        },
    }


def _build_definition_pbir(semantic_model: str) -> Dict[str, Any]:
    # byPath reference for local PBIP (Desktop-compatible)
    rel_path = f"../../{semantic_model}"
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {
            "byPath": {"path": rel_path},
        },
    }


def _build_tmdl_measures(measures: List[MeasureSpec]) -> str:
    """Generate _Measures.tmdl content from measure specs."""
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
        # DAX must be single line
        dax_single = " ".join(m.dax.split())
        lines.append(f"{t1}/// Purpose: {m.description or m.name}")
        lines.append(f"{t1}measure '{m.name}' = {dax_single}")
        lines.append(f"{t2}formatString: \"{m.format_string}\"")
        if m.display_folder:
            lines.append(f"{t2}displayFolder: \"{m.display_folder}\"")
        if m.is_hidden:
            lines.append(f"{t2}isHidden")
        for ann_key, ann_val in m.annotations.items():
            lines.append(f"{t2}annotation {ann_key} = {ann_val}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# PBIP Adapter
# ---------------------------------------------------------------------------

class PBIPAdapter(GeneratorAdapter):
    """
    Renders a DashboardSpec to Power BI PBIP folder structure.

    Output layout (relative to the use-case report root):
        <UseCase>.Report/
            definition.pbir
            definition/
                report.json
                pages/
                    pages.json
                    Overview/
                        page.json
                        visuals/
                            KPI_Cards/visual.json
                            Main_1/visual.json
                            ...
                    Detail/
                        page.json
                        visuals/
                            ...

    The caller writes these files to the dist/ directory.
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
        detail = spec.detail_page()

        if not overview:
            errors.append("IR missing Overview page")
        else:
            kpi_cards = overview.visual_by_id("KPI_Cards")
            if not kpi_cards:
                errors.append("Overview page missing KPI_Cards visual")
            elif not kpi_cards.binding.measures:
                errors.append("KPI_Cards binding has no measures")

        if not detail:
            errors.append("IR missing Detail page")
        else:
            smart_narr = detail.visual_by_id("Smart_Narrative")
            if not smart_narr:
                errors.append("Detail page missing Smart_Narrative visual")

        if not spec.semantic_model:
            errors.append("DashboardSpec.semantic_model is empty")

        return errors

    def render(self, spec: DashboardSpec) -> RenderResult:
        """Render DashboardSpec → {relative_path: bytes}."""
        files: Dict[str, bytes] = {}
        warnings: List[str] = []

        report_name = f"{spec.use_case_id}.Report"

        # definition.pbir
        pbir = _build_definition_pbir(spec.semantic_model)
        files[f"{report_name}/definition.pbir"] = (
            json.dumps(pbir, indent=2, ensure_ascii=False).encode("utf-8")
        )

        # definition/report.json
        report_json = _build_report_json(spec)
        files[f"{report_name}/definition/report.json"] = (
            json.dumps(report_json, indent=2, ensure_ascii=False).encode("utf-8")
        )

        # pages.json
        pages_json = _build_pages_json(spec.pages)
        files[f"{report_name}/definition/pages/pages.json"] = (
            json.dumps(pages_json, indent=2, ensure_ascii=False).encode("utf-8")
        )

        # Per-page files
        for page in spec.pages:
            page_base = f"{report_name}/definition/pages/{page.id}"

            # page.json
            page_json = _build_page_json(page)
            files[f"{page_base}/page.json"] = (
                json.dumps(page_json, indent=2, ensure_ascii=False).encode("utf-8")
            )

            # Per-visual files
            for vspec in page.visuals:
                visual_json = _build_visual_json(vspec)
                files[f"{page_base}/visuals/{vspec.id}/visual.json"] = (
                    json.dumps(visual_json, indent=2, ensure_ascii=False).encode("utf-8")
                )

        # _Measures.tmdl (companion — caller decides where to put it)
        if spec.measures:
            tmdl = _build_tmdl_measures(spec.measures)
            files[f"{spec.semantic_model}/definition/tables/_Measures.tmdl"] = (
                tmdl.encode("utf-8")
            )

        return RenderResult(files=files, adapter=self.name, warnings=warnings)
