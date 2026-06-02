"""
PBIP Adapter — renders DashboardSpec to Power BI PBIP folder structure.

Lives in products/fabric/powerbi/ because it encodes Power BI-specific
knowledge (PBIP schema URLs, visualType strings, canvas dimensions, TMDL
format). The generator_core framework only knows the abstract GeneratorAdapter
interface — this is the concrete PBI implementation.

Canvas size: 1920 × 1080 (standard HD widescreen, matches all bracket definitions)
"""

from __future__ import annotations

import json
import re
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
from products.fabric.powerbi.tooling.schema_registry import (
    REPORT_SCHEMA as _REPORT_SCHEMA,
    PAGE_SCHEMA as _PAGE_SCHEMA,
    VISUAL_SCHEMA as _VISUAL_SCHEMA,
    PAGES_METADATA_SCHEMA as _PAGES_SCHEMA,
    VERSION_METADATA_SCHEMA as _VERSION_METADATA_SCHEMA,
    PBIP_SCHEMA as _PBIP_SCHEMA,
    DEFINITION_PBIR_SCHEMA as _DEFINITION_PBIR_SCHEMA,
    DEFINITION_PBIR_VERSION as _DEFINITION_PBIR_VERSION,
)

# Power BI canvas dimensions in pixels — must match bracket report_canvas (1920 × 1080)
_CANVAS_W = 1920
_CANVAS_H = 1080

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

def _px(pos: Position, z: int = 10000, tab_order: int = 3000) -> Dict[str, int]:
    return {
        "x": round(pos.x * _CANVAS_W),
        "y": round(pos.y * _CANVAS_H),
        "z": z,
        "width":  round(pos.width  * _CANVAS_W),
        "height": round(pos.height * _CANVAS_H),
        "tabOrder": tab_order,
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
        qs["Values"] = {"projections": [_projection(_entity_ref(table, b.filter_column), f"{table}.{b.filter_column}", b.filter_column)]}

    if b.columns and vspec.visual_type in (VisualType.MATRIX, VisualType.TABLE):
        projections = []
        for col_ref in b.columns:
            parts = col_ref.split(".")
            t, c = (parts[0], parts[1]) if len(parts) == 2 else ("dim_org", col_ref)
            projections.append(_projection(_entity_ref(t, c), f"{t}.{c}", c))
        qs["Rows"] = {"projections": projections}

    return qs


def _build_visual_json(vspec: VisualSpec, tab_order: int = 3000) -> Dict[str, Any]:
    pbip_type = _VISUAL_TYPE_MAP.get(vspec.visual_type, ["cardVisual"])[0]
    visual: Dict[str, Any] = {
        "$schema": _VISUAL_SCHEMA,
        "name": vspec.id,
        "position": _px(vspec.position, z=10000, tab_order=tab_order),
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
        "displayOption": "FitToPage",
        "width": _CANVAS_W,
        "height": _CANVAS_H,
    }


def _build_pages_json(pages: List[PageSpec]) -> Dict[str, Any]:
    return {
        "$schema": _PAGES_SCHEMA,
        "pageOrder": [p.id for p in pages],
        "activePageName": pages[0].id if pages else "",
    }


def _build_report_json(spec: DashboardSpec) -> Dict[str, Any]:
    theme_name = Path(spec.theme_path).stem if spec.theme_path else None
    theme_collection: Dict[str, Any] = {
        "baseTheme": {
            "name": "CY25SU10",
            "reportVersionAtImport": {"visual": "2.1.0", "report": "3.0.0", "page": "2.3.0"},
            "type": "SharedResources",
        }
    }
    resource_packages: list = []
    if theme_name:
        theme_collection["customTheme"] = {
            "name": f"{theme_name}.json",
            "reportVersionAtImport": {"visual": "2.1.0", "report": "3.0.0", "page": "2.3.0"},
            "type": "RegisteredResources",
        }
        resource_packages = [
            {
                "name": "SharedResources",
                "type": "SharedResources",
                "items": [{"name": "CY25SU10", "path": "BaseThemes/CY25SU10.json", "type": "BaseTheme"}],
            },
            {
                "name": "RegisteredResources",
                "type": "RegisteredResources",
                "items": [{"name": f"{theme_name}.json", "path": f"{theme_name}.json", "type": "CustomTheme"}],
            },
        ]
    report: Dict[str, Any] = {
        "$schema": _REPORT_SCHEMA,
        "themeCollection": theme_collection,
        "settings": {
            "useStylableVisualContainerHeader": True,
            "exportDataMode": "AllowSummarized",
            "defaultFilterActionIsDataFilter": True,
            "defaultDrillFilterOtherVisuals": True,
            "allowChangeFilterTypes": True,
            "useEnhancedTooltips": True,
            "useDefaultAggregateDisplayName": True,
        },
    }
    if resource_packages:
        report["resourcePackages"] = resource_packages
    return report


def _build_definition_pbir(semantic_model: str) -> Dict[str, Any]:
    # Path is relative to definition.pbir (report root). Both report and model
    # land in dist/, so a single ../ step reaches the sibling model folder.
    return {
        "$schema": _DEFINITION_PBIR_SCHEMA,
        "version": _DEFINITION_PBIR_VERSION,
        "datasetReference": {"byPath": {"path": f"../{semantic_model}"}},
    }


def _build_definition_pbism() -> Dict[str, Any]:
    """Build definition.pbism — mandatory root descriptor for every PBIP SemanticModel."""
    return {"version": "4.2", "settings": {"qnaEnabled": True}}


def _build_database_tmdl(database_name: str) -> str:
    """Build definition/database.tmdl — required by Power BI Desktop and Fabric API."""
    return f"database '{database_name}'\n\tcompatibilityLevel: 1702\n\tcompatibilityMode: powerBI\n"


def _build_model_tmdl() -> str:
    """Build definition/model.tmdl — required for Import mode models."""
    return (
        "model Model\n"
        "\tculture: en-US\n"
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3\n"
        "\tdiscourageImplicitMeasures\n"
    )


def _build_version_json() -> Dict[str, Any]:
    """Build definition/version.json — required by Desktop and validate_pbip."""
    return {
        "$schema": _VERSION_METADATA_SCHEMA,
        "version": "2.0.0",
    }


def _build_pbip_root() -> Dict[str, Any]:
    """Build the root .pbip file that tells Desktop which artifact this folder is."""
    return {
        "$schema": _PBIP_SCHEMA,
        "version": "1.0",
        "artifacts": [{"report": {"path": "."}}],
    }


def _speaking_report_name(use_case_id: str, title: str) -> str:
    """Derive speaking report folder name (e.g. 'COM-001_Sales_Performance').

    Matches the convention used by the scaffold writer: ID + sanitized title.
    Only word characters and hyphens are kept; everything else becomes '_'.
    This intentionally strips '&', '(', ')', '+', '!', ',', ';', '#', etc.
    so that folder names remain safe on all filesystems and in Power BI Service.
    """
    safe_title = re.sub(r'[^\w-]+', "_", title).strip("_")
    return f"{use_case_id}_{safe_title}" if safe_title else use_case_id


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

    def diff(self, spec_a: DashboardSpec, spec_b: DashboardSpec) -> List[str]:
        """PBIP-aware diff: compares TMDL output byte-by-byte as a final check."""
        base_changes = super().diff(spec_a, spec_b)
        tmdl_a = _build_tmdl_measures(spec_a.measures)
        tmdl_b = _build_tmdl_measures(spec_b.measures)
        if tmdl_a != tmdl_b:
            base_changes.append("tmdl_output: content differs")
        return base_changes

    def deploy(
        self,
        result: RenderResult,
        target_url: str,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Deploy PBIP output via Fabric REST API (fab import equivalent).

        target_url: Fabric workspace API endpoint, e.g.
            https://api.fabric.microsoft.com/v1/workspaces/<ws_id>
        credentials: dict with 'token' key (Bearer token from az/fab auth).
        """
        import json
        import urllib.request

        token = (credentials or {}).get("token", "")
        if not token:
            raise ValueError("deploy() requires credentials={'token': '<bearer_token>'}")

        # For each rendered file, POST via Fabric Update Item Definition API
        # This is a minimal implementation — production use should use `fab import`
        for rel_path, content in result.files.items():
            api_url = f"{target_url.rstrip('/')}/items"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            payload = json.dumps({
                "displayName": rel_path,
                "type": "Report",
                "definition": {"parts": [{"path": rel_path, "payload": content.hex(), "payloadType": "InlineBase64"}]},
            }).encode("utf-8")
            req = urllib.request.Request(api_url, data=payload, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    if resp.status not in (200, 201, 202):
                        return False
            except Exception as exc:
                raise RuntimeError(f"Fabric deploy failed for {rel_path}: {exc}") from exc
        return True

    def render(self, spec: DashboardSpec) -> RenderResult:
        files: Dict[str, bytes] = {}
        base_name = _speaking_report_name(spec.use_case_id, spec.title)
        report_name = f"{base_name}.Report"
        pbip_filename = f"{base_name}.pbip"

        def _json(obj: Any) -> bytes:
            return json.dumps(obj, indent=2, ensure_ascii=False).encode("utf-8")

        files[f"{report_name}/{pbip_filename}"]              = _json(_build_pbip_root())
        files[f"{report_name}/definition.pbir"]              = _json(_build_definition_pbir(spec.semantic_model))
        files[f"{report_name}/definition/version.json"]      = _json(_build_version_json())
        files[f"{report_name}/definition/report.json"]       = _json(_build_report_json(spec))
        files[f"{report_name}/definition/pages/pages.json"]  = _json(_build_pages_json(spec.pages))

        for page in spec.pages:
            base = f"{report_name}/definition/pages/{page.id}"
            files[f"{base}/page.json"] = _json(_build_page_json(page))
            for tab_idx, vspec in enumerate(page.visuals):
                files[f"{base}/visuals/{vspec.id}/visual.json"] = _json(
                    _build_visual_json(vspec, tab_order=3000 + tab_idx)
                )

        # Semantic model scaffold — required by Power BI Desktop to open the report locally.
        # definition.pbism, database.tmdl and model.tmdl are ONE-TIME seeds: they must NOT
        # overwrite an existing real semantic model (overwriting model.tmdl triggers the AS
        # error PFE_TM_DDL_MODIFIED_CULTURE_OR_COLLATION_AFTER_CHILDREN_CREATION).
        no_overwrite: set = set()
        if spec.semantic_model:
            db_name = spec.semantic_model.replace(".SemanticModel", "")
            pbism_key = f"{spec.semantic_model}/definition.pbism"
            db_key    = f"{spec.semantic_model}/definition/database.tmdl"
            model_key = f"{spec.semantic_model}/definition/model.tmdl"
            files[pbism_key] = (
                json.dumps(_build_definition_pbism(), indent=2, ensure_ascii=False).encode("utf-8")
            )
            files[db_key]    = _build_database_tmdl(db_name).encode("utf-8")
            files[model_key] = _build_model_tmdl().encode("utf-8")
            # Mark all three as "write only if missing" so they never clobber a real model.
            no_overwrite.update({pbism_key, db_key, model_key})

            if spec.measures:
                files[f"{spec.semantic_model}/definition/tables/_Measures.tmdl"] = (
                    _build_tmdl_measures(spec.measures).encode("utf-8")
                )

        # Embed custom theme file into StaticResources/RegisteredResources/
        if spec.theme_path:
            theme_file = Path(spec.theme_path)
            if theme_file.exists():
                files[f"{report_name}/StaticResources/RegisteredResources/{theme_file.name}"] = (
                    theme_file.read_bytes()
                )

        return RenderResult(files=files, adapter=self.name, no_overwrite_paths=no_overwrite)
