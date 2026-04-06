"""
Apache Superset Adapter — renders DashboardSpec to Superset dashboard ZIP export.

Lives in products/oss/ because it encodes Superset-specific knowledge
(chart types, dashboard JSON format, dataset references, ZIP structure).
The generator_core framework only knows the abstract GeneratorAdapter
interface — this is the concrete Superset implementation.

Status: STUB — implement render() and visual_type_map() before use.

Superset output format:
    A ZIP archive (dashboard_export.zip) that can be imported via:
    Superset UI → Dashboards → Import, or
    POST /api/v1/dashboard/import

ZIP structure:
    dashboard_export/
        dashboards/<slug>.yaml
        charts/<chart_id>.yaml
        datasets/<dataset_id>.yaml

Reference:
    https://superset.apache.org/docs/using-superset/importing-exporting-datasources
"""

from __future__ import annotations

from typing import Dict, List

from tooling.generator_core.adapters.base import GeneratorAdapter, RenderResult
from tooling.generator_core.ir.specs import (
    AdapterTarget,
    DashboardSpec,
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


class SupersetAdapter(GeneratorAdapter):
    """
    Renders a DashboardSpec to an Apache Superset dashboard ZIP export.

    This is a Superset-specific class. It knows about Superset chart types,
    dashboard YAML format, dataset references, and the ZIP import structure.
    Nothing here should ever be referenced by the Power BI generator.

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
        overview = spec.overview_page()
        if not overview:
            errors.append("IR missing Overview page")
        detail = spec.detail_page()
        if not detail:
            errors.append("IR missing Detail page")
        return errors

    def render(self, spec: DashboardSpec) -> RenderResult:
        # TODO: Implement Superset dashboard ZIP rendering.
        # Reference: products/oss/tooling/adapters/superset.py
        #
        # Steps:
        # 1. Create dashboards/<slug>.yaml with position_data for each visual
        # 2. For each visual, create charts/<chart_id>.yaml with viz_type from
        #    _VISUAL_TYPE_MAP and params (metrics, groupby, etc.)
        # 3. Create datasets/<dataset_id>.yaml referencing gold tables
        # 4. Map Position (canvas fractions) to Superset GRID_DEFAULT_CHART_WIDTH
        #    (12 columns total; y in GRID_BASE units = 8px)
        # 5. Bundle all YAML files into a ZIP and return as dashboard_export.zip
        raise NotImplementedError(
            "SupersetAdapter.render() is not yet implemented. "
            "See products/oss/tooling/adapters/superset.py for the stub."
        )
