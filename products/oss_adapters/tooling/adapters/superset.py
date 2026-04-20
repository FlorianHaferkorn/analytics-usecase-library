"""
Apache Superset Adapter — renders DashboardSpec to Superset dashboard ZIP export.

Lives in products/oss/ because it encodes Superset-specific knowledge
(chart types, dashboard JSON format, dataset references, ZIP structure).
The generator_core framework only knows the abstract GeneratorAdapter
interface — this is the concrete Superset implementation.

Superset output format:
    A ZIP archive (dashboard_export.zip) importable via:
    Superset UI → Dashboards → Import, or
    POST /api/v1/dashboard/import

ZIP structure:
    dashboard_export/
        dashboards/<slug>.yaml
        charts/<chart_id>.yaml

Reference:
    https://superset.apache.org/docs/using-superset/importing-exporting-datasources
Grid translation (from OSS_Connector_Guide.md):
    Superset uses a 12-column fluid grid.
    Position (canvas fraction) → Superset grid:
        col_x  = round(pos.x * 12)
        col_w  = max(1, round(pos.width * 12))
        row_y  = round(pos.y * 100)   # row units (each ~1%)
        row_h  = max(2, round(pos.height * 40))
"""

from __future__ import annotations

import io
import json
import zipfile
from typing import Any, Dict, List, Optional

import yaml  # pyyaml required

from tooling.generator_core.adapters.base import GeneratorAdapter, RenderResult
from tooling.generator_core.ir.specs import (
    AdapterTarget,
    DashboardSpec,
    PageRole,
    VisualSpec,
    VisualType,
)

# IR VisualType → Superset viz_type strings
_VISUAL_TYPE_MAP: Dict[VisualType, List[str]] = {
    VisualType.KPI_CARD:        ["big_number_total", "big_number"],
    VisualType.TREND_LINE:      ["line", "echarts_timeseries_line"],
    VisualType.BAR_CHART:       ["bar", "echarts_timeseries_bar"],
    VisualType.WATERFALL:       ["waterfall"],
    VisualType.SCATTER:         ["scatter"],
    VisualType.MATRIX:          ["pivot_table_v2"],
    VisualType.TABLE:           ["table"],
    VisualType.SLICER:          ["filter_box"],
    VisualType.SMART_NARRATIVE: ["text"],
    VisualType.ACTION_PANEL:    ["text"],
    VisualType.TEXT_BOX:        ["text"],
}

# Semantic role → Superset conditional formatting color
_SEMANTIC_COLORS = {
    "positive": "#107C10",
    "negative": "#A4262C",
    "warning":  "#C98A00",
    "neutral":  "#605E5C",
}


def _pos_to_superset_grid(pos) -> Dict[str, int]:
    """Convert canvas-fraction Position to Superset grid coordinates."""
    return {
        "col_x":  round(pos.x * 12),
        "col_w":  max(1, round(pos.width * 12)),
        "row_y":  round(pos.y * 100),
        "row_h":  max(2, round(pos.height * 40)),
    }


def _build_chart_yaml(visual: VisualSpec, chart_id: int, dataset_name: str, viz_type: str) -> Dict[str, Any]:
    """Build a Superset chart export YAML dict for one visual."""
    binding = visual.binding
    metrics = []
    if binding.measure:
        metrics.append({"label": binding.measure, "expressionType": "SIMPLE",
                        "column": {"column_name": binding.measure}})
    for m in (binding.measures or []):
        metrics.append({"label": m, "expressionType": "SIMPLE",
                        "column": {"column_name": m}})

    groupby = []
    if binding.category:
        col = binding.category.split(".")[-1]
        groupby.append(col)

    params: Dict[str, Any] = {
        "viz_type":      viz_type,
        "metrics":       metrics,
        "groupby":       groupby,
        "time_range":    "No filter",
        "adhoc_filters": [],
    }

    # Conditional formatting for KPI cards
    if visual.visual_type == VisualType.KPI_CARD:
        params["comparison_type"] = "difference"

    # Semantic color thresholds for charts with a single metric
    if metrics and visual.visual_type in (VisualType.BAR_CHART, VisualType.TREND_LINE):
        params["conditional_formatting"] = [
            {"colorScheme": _SEMANTIC_COLORS["negative"],
             "operator": "<", "targetValue": 0,
             "column": metrics[0].get("label", "")},
        ]

    return {
        "slice_name":   visual.title or visual.id,
        "viz_type":     viz_type,
        "datasource_type": "table",
        "datasource_name": dataset_name,
        "params":       json.dumps(params),
        "cache_timeout": None,
        "uuid":         f"chart-{chart_id:04d}",
    }


def _build_dashboard_yaml(spec: DashboardSpec, chart_ids: List[int],
                           visuals: List[VisualSpec]) -> Dict[str, Any]:
    """Build the Superset dashboard export YAML dict."""
    slug = spec.use_case_id.lower().replace("-", "_")

    position_data: Dict[str, Any] = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
    }

    for visual, chart_id in zip(visuals, chart_ids):
        g = _pos_to_superset_grid(visual.position)
        container_id = f"CHART-{chart_id}"
        position_data[container_id] = {
            "type": "CHART",
            "id": container_id,
            "meta": {
                "chartId": chart_id,
                "width": g["col_w"],
                "height": g["row_h"],
                "sliceName": visual.title or visual.id,
            },
            "parents": ["ROOT_ID", "GRID_ID"],
            "children": [],
        }
        position_data["GRID_ID"]["children"].append(container_id)

    return {
        "dashboard_title": spec.title,
        "description":     f"Generated from {spec.use_case_id} UseCase_Bracket",
        "slug":            slug,
        "uuid":            f"dashboard-{slug}",
        "position_data":   json.dumps(position_data),
        "metadata":        json.dumps({"color_scheme": "bnbColors", "expanded_slices": {}}),
        "version":         "1.0.0",
    }


class SupersetAdapter(GeneratorAdapter):
    """
    Renders a DashboardSpec to an Apache Superset dashboard ZIP export.

    Output:
        dashboard_export.zip — importable via Superset UI or API
    """

    @property
    def name(self) -> str:
        return "superset"

    @property
    def target(self) -> AdapterTarget:
        return AdapterTarget.SUPERSET

    def visual_type_map(self) -> Dict[VisualType, List[str]]:
        return _VISUAL_TYPE_MAP

    def validate_ir(self, spec: DashboardSpec) -> List[str]:
        errors: List[str] = []
        if not spec.overview_page():
            errors.append("IR missing Overview page")
        if not spec.detail_page():
            errors.append("IR missing Detail page")
        return errors

    def deploy(
        self,
        result: RenderResult,
        target_url: str,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Deploy dashboard_export.zip to a live Superset instance via POST /api/v1/dashboard/import."""
        import urllib.request
        token = (credentials or {}).get("token", "")
        if not token:
            raise ValueError("deploy() requires credentials={'token': '<access_token>'}")
        content = result.files.get("dashboard_export.zip", b"")
        # Superset import expects multipart/form-data; use a simple boundary
        boundary = b"----AnalyticsBoundary"
        body = (
            b"--" + boundary + b"\r\n"
            b'Content-Disposition: form-data; name="formData"; filename="dashboard_export.zip"\r\n'
            b"Content-Type: application/zip\r\n\r\n"
            + content + b"\r\n"
            b"--" + boundary + b"--\r\n"
        )
        req = urllib.request.Request(
            f"{target_url.rstrip('/')}/api/v1/dashboard/import",
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary.decode()}",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status in (200, 201, 202)

    def render(self, spec: DashboardSpec) -> RenderResult:
        """
        Render DashboardSpec → Superset dashboard ZIP.

        Returns RenderResult with one file:
            "dashboard_export.zip" → bytes of the importable ZIP archive
        """
        warnings: List[str] = []
        dataset_name = f"{spec.domain}_{spec.use_case_id}".lower().replace("-", "_")

        # Collect all visuals from all pages
        all_visuals: List[VisualSpec] = []
        for page in spec.pages:
            all_visuals.extend(page.visuals)

        chart_yamls: Dict[str, str] = {}
        chart_ids: List[int] = []

        for i, visual in enumerate(all_visuals):
            chart_id = 1000 + i
            chart_ids.append(chart_id)
            viz_type = self.map_visual_type(visual.visual_type)
            if viz_type == visual.visual_type.value:
                warnings.append(f"No Superset mapping for visual_type '{visual.visual_type}' ({visual.id})")
            chart_data = _build_chart_yaml(visual, chart_id, dataset_name, viz_type)
            chart_yamls[f"dashboard_export/charts/chart_{chart_id:04d}.yaml"] = yaml.dump(
                chart_data, default_flow_style=False, allow_unicode=True
            )

        dashboard_data = _build_dashboard_yaml(spec, chart_ids, all_visuals)
        slug = dashboard_data["slug"]

        # Build ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                f"dashboard_export/dashboards/{slug}.yaml",
                yaml.dump(dashboard_data, default_flow_style=False, allow_unicode=True),
            )
            for path, content in chart_yamls.items():
                zf.writestr(path, content)
            # Metadata file
            zf.writestr(
                "dashboard_export/metadata.yaml",
                yaml.dump({
                    "type": "Dashboard",
                    "version": "1.0.0",
                    "timestamp": spec.generated_at or "unknown",
                    "generator": f"analytics-usecase-library/{spec.generator_version}",
                    "use_case_id": spec.use_case_id,
                }, default_flow_style=False),
            )

        return RenderResult(
            files={"dashboard_export.zip": zip_buffer.getvalue()},
            adapter=self.name,
            warnings=warnings,
        )
