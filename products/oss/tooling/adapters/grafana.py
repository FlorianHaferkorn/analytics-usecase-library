"""
Grafana Adapter — renders DashboardSpec to Grafana dashboard JSON.

Lives in products/oss/ because it encodes Grafana-specific knowledge
(panel types, grid layout units, data source references, PromQL/SQL
query format). The generator_core framework only knows the abstract
GeneratorAdapter interface — this is the concrete Grafana implementation.

Status: STUB — implement render() and visual_type_map() before use.

Grafana output format:
    A single dashboard.json that can be imported via:
    Grafana UI → Dashboards → Import, or
    POST /api/dashboards/import

Reference:
    https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/import-dashboards/
"""

from __future__ import annotations

from typing import Dict, List

from tooling.generator_core.adapters.base import GeneratorAdapter, RenderResult
from tooling.generator_core.ir.specs import (
    AdapterTarget,
    DashboardSpec,
    VisualType,
)

# IR VisualType → Grafana panel type strings
_VISUAL_TYPE_MAP: Dict[VisualType, List[str]] = {
    VisualType.KPI_CARD:        ["stat"],
    VisualType.TREND_LINE:      ["timeseries"],
    VisualType.BAR_CHART:       ["barchart"],
    VisualType.WATERFALL:       ["barchart"],
    VisualType.SCATTER:         ["scatterplot", "xychart"],
    VisualType.MATRIX:          ["table"],
    VisualType.TABLE:           ["table"],
    VisualType.SLICER:          ["text"],
    VisualType.SMART_NARRATIVE: ["text"],
    VisualType.ACTION_PANEL:    ["text"],
    VisualType.TEXT_BOX:        ["text"],
}


class GrafanaAdapter(GeneratorAdapter):
    """
    Renders a DashboardSpec to a Grafana dashboard JSON export.

    This is a Grafana-specific class. It knows about Grafana panel types,
    grid layout (24-column, variable row height), data source references,
    and query target format. Nothing here should ever be referenced by the
    Power BI generator.

    Output:
        dashboard.json — importable via Grafana UI or API
    """

    @property
    def name(self) -> str:
        return "grafana"

    @property
    def target(self) -> AdapterTarget:
        return AdapterTarget.GRAFANA

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
        # TODO: Implement Grafana dashboard JSON rendering.
        # Reference: products/oss/tooling/adapters/grafana.py
        #
        # Steps:
        # 1. Create Grafana dashboard skeleton (title, uid, schemaVersion, panels)
        # 2. For each page/visual, create a Grafana "panel" with the correct
        #    type from _VISUAL_TYPE_MAP
        # 3. Map Position (canvas fractions) to Grafana grid: x (0–23), y, w, h
        #    Grafana grid width=24; use round(pos.x * 24) etc.
        # 4. Add targets (data source queries) from measure bindings
        # 5. Return {"dashboard": {...}} as dashboard.json
        raise NotImplementedError(
            "GrafanaAdapter.render() is not yet implemented. "
            "See products/oss/tooling/adapters/grafana.py for the stub."
        )
