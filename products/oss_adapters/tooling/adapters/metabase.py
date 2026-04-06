"""
Metabase Adapter — renders DashboardSpec to Metabase dashboard JSON.

Lives in products/oss/ because it encodes Metabase-specific knowledge
(dashboard card types, series format, filter widget syntax). The
generator_core framework only knows the abstract GeneratorAdapter
interface — this is the concrete Metabase implementation.

Status: STUB — implement render() and visual_type_map() before use.

Metabase output format:
    A single dashboard.json that can be imported via the Metabase API:
    POST /api/dashboard/import
    Content: {"dashboards": [{...}]}

Reference:
    https://www.metabase.com/docs/latest/api/dashboard
"""

from __future__ import annotations

from typing import Dict, List

from tooling.generator_core.adapters.base import GeneratorAdapter, RenderResult
from tooling.generator_core.ir.specs import (
    AdapterTarget,
    DashboardSpec,
    VisualType,
)

# IR VisualType → Metabase display type strings
_VISUAL_TYPE_MAP: Dict[VisualType, List[str]] = {
    VisualType.KPI_CARD:        ["scalar"],
    VisualType.TREND_LINE:      ["line"],
    VisualType.BAR_CHART:       ["bar"],
    VisualType.WATERFALL:       ["waterfall"],
    VisualType.SCATTER:         ["scatter"],
    VisualType.MATRIX:          ["pivot"],
    VisualType.TABLE:           ["table"],
    VisualType.SLICER:          ["filter"],
    VisualType.SMART_NARRATIVE: ["text"],
    VisualType.ACTION_PANEL:    ["text"],
    VisualType.TEXT_BOX:        ["text"],
}


class MetabaseAdapter(GeneratorAdapter):
    """
    Renders a DashboardSpec to a Metabase dashboard JSON export.

    This is a Metabase-specific class. It knows about Metabase card types,
    series configuration, and filter widget syntax. Nothing here should ever
    be referenced by the Power BI generator.

    Output:
        dashboard.json — importable via POST /api/dashboard/import
    """

    @property
    def name(self) -> str:
        return "metabase"

    @property
    def target(self) -> AdapterTarget:
        return AdapterTarget.METABASE

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
        # TODO: Implement Metabase dashboard JSON rendering.
        # Reference: products/oss/tooling/adapters/metabase.py
        #
        # Steps:
        # 1. Create a Metabase dashboard skeleton (name, description, parameters)
        # 2. For each page/visual in spec, create a Metabase "card" with the
        #    correct display type from _VISUAL_TYPE_MAP
        # 3. Map Position (canvas fractions) to Metabase grid coordinates
        #    (Metabase uses a 24-column grid; row height is ~100px)
        # 4. Attach measure bindings as dataset_query (native SQL or MBQL)
        # 5. Return {"dashboard": {...}} as dashboard.json
        raise NotImplementedError(
            "MetabaseAdapter.render() is not yet implemented. "
            "See products/oss/tooling/adapters/metabase.py for the stub."
        )
