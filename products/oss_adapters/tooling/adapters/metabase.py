"""
Metabase Adapter — renders DashboardSpec to Metabase dashboard JSON.

Lives in products/oss/ because it encodes Metabase-specific knowledge
(dashboard card types, series format, filter widget syntax).

Metabase output format:
    A single dashboard.json importable via:
    POST /api/dashboard/import
    Content: {"dashboards": [{...}]}

Reference:
    https://www.metabase.com/docs/latest/api/dashboard
Grid translation (from OSS_Connector_Guide.md):
    Metabase uses a 24-column × fixed-row layout.
    Position (canvas fraction) → Metabase grid:
        col   = round(pos.x * 24)
        row   = round(pos.y * 36)       # ~36 rows per page at std height
        size_x = max(1, round(pos.width * 24))
        size_y = max(2, round(pos.height * 20))
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from tooling.generator_core.adapters.base import GeneratorAdapter, RenderResult
from tooling.generator_core.ir.specs import (
    AdapterTarget,
    DashboardSpec,
    PageRole,
    VisualSpec,
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

# Semantic colors for conditional formatting
_SEMANTIC_COLORS = {
    "positive": "#107C10",
    "negative": "#A4262C",
    "warning":  "#C98A00",
}


def _pos_to_metabase_grid(pos) -> Dict[str, int]:
    return {
        "col":    round(pos.x * 24),
        "row":    round(pos.y * 36),
        "size_x": max(1, round(pos.width * 24)),
        "size_y": max(2, round(pos.height * 20)),
    }


def _build_card(visual: VisualSpec, card_id: int, display: str) -> Dict[str, Any]:
    """Build one Metabase dashboard card dict."""
    binding = visual.binding
    g = _pos_to_metabase_grid(visual.position)

    # Visualization settings
    viz_settings: Dict[str, Any] = {}
    if visual.visual_type == VisualType.KPI_CARD:
        viz_settings["scalar.switch_positive_negative"] = False
    elif visual.visual_type in (VisualType.BAR_CHART, VisualType.TREND_LINE):
        viz_settings["graph.colors"] = ["#0078D4"]
    elif visual.visual_type == VisualType.SMART_NARRATIVE:
        pass

    # Text cards (narrative, action panel) get text body directly
    if display == "text":
        return {
            "id": card_id,
            "dashboard_id": 1,
            "card": None,
            "parameter_mappings": [],
            "visualization_settings": {"text": visual.title or visual.id},
            "col":    g["col"],
            "row":    g["row"],
            "size_x": g["size_x"],
            "size_y": g["size_y"],
        }

    # Determine aggregation / breakout from binding
    aggregation = []
    if binding.measure:
        aggregation.append(["metric", binding.measure])
    for m in (binding.measures or []):
        aggregation.append(["metric", m])

    breakout = []
    if binding.category:
        col_name = binding.category.split(".")[-1]
        breakout.append(["field", col_name, None])

    dataset_query: Dict[str, Any] = {
        "type": "query",
        "query": {
            "aggregation": aggregation or [["count"]],
            "breakout": breakout,
        },
    }

    card: Dict[str, Any] = {
        "id":              card_id,
        "name":            visual.title or visual.id,
        "display":         display,
        "dataset_query":   dataset_query,
        "visualization_settings": viz_settings,
    }

    if visual.visual_type == VisualType.KPI_CARD and binding.measures:
        # Scalar card: show first measure
        card["display"] = "scalar"

    return {
        "id": card_id,
        "dashboard_id": 1,
        "card": card,
        "parameter_mappings": [],
        "visualization_settings": viz_settings,
        "col":    g["col"],
        "row":    g["row"],
        "size_x": g["size_x"],
        "size_y": g["size_y"],
    }


class MetabaseAdapter(GeneratorAdapter):
    """
    Renders a DashboardSpec to a Metabase dashboard JSON export.

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
        """Deploy dashboard.json to a live Metabase instance via POST /api/dashboard/import."""
        import urllib.request
        token = (credentials or {}).get("token", "")
        if not token:
            raise ValueError("deploy() requires credentials={'token': '<session_token>'}")
        content = result.files.get("dashboard.json", b"")
        req = urllib.request.Request(
            f"{target_url.rstrip('/')}/api/dashboard/import",
            data=content,
            headers={"Content-Type": "application/json", "X-Metabase-Session": token},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status in (200, 201, 202)

    def render(self, spec: DashboardSpec) -> RenderResult:
        """
        Render DashboardSpec → Metabase dashboard JSON.

        Returns RenderResult with one file:
            "dashboard.json" → importable via POST /api/dashboard/import
        """
        warnings: List[str] = []
        cards: List[Dict[str, Any]] = []
        card_id = 1

        for page in spec.pages:
            page_label = "Overview" if page.role == PageRole.OVERVIEW else "Detail"
            for visual in page.visuals:
                display = self.map_visual_type(visual.visual_type)
                if display == visual.visual_type.value:
                    warnings.append(f"No Metabase mapping for '{visual.visual_type}' ({visual.id})")
                card = _build_card(visual, card_id, display)
                cards.append(card)
                card_id += 1

        dashboard = {
            "name":        spec.title,
            "description": f"Generated from {spec.use_case_id} — {spec.domain}",
            "parameters":  [],
            "ordered_cards": cards,
        }

        payload = json.dumps({"dashboard": dashboard}, indent=2, ensure_ascii=False)
        return RenderResult(
            files={"dashboard.json": payload.encode("utf-8")},
            adapter=self.name,
            warnings=warnings,
        )

    def diff(self, spec_a: DashboardSpec, spec_b: DashboardSpec) -> List[str]:
        """Compare rendered Metabase card counts and display types in addition to IR-level changes."""
        changes = super().diff(spec_a, spec_b)

        result_a = self.render(spec_a)
        result_b = self.render(spec_b)
        dash_a = json.loads(result_a.files["dashboard.json"])["dashboard"]
        dash_b = json.loads(result_b.files["dashboard.json"])["dashboard"]
        cards_a = dash_a.get("ordered_cards", [])
        cards_b = dash_b.get("ordered_cards", [])

        if len(cards_a) != len(cards_b):
            changes.append(f"metabase: card count changed: {len(cards_a)} → {len(cards_b)}")

        def _card_display(c: Dict[str, Any]) -> str:
            inner = c.get("card")
            return inner.get("display", "text") if inner else "text"

        types_a = [_card_display(c) for c in cards_a]
        types_b = [_card_display(c) for c in cards_b]
        if types_a != types_b:
            changes.append(f"metabase: card display types changed: {types_a} → {types_b}")

        return changes
