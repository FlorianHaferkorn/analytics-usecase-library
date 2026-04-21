"""
Grafana Adapter — renders DashboardSpec to Grafana dashboard JSON.

Lives in products/oss/ because it encodes Grafana-specific knowledge
(panel types, grid layout units, data source references, query format).

Grafana output format:
    A single dashboard.json importable via:
    Grafana UI → Dashboards → Import, or
    POST /api/dashboards/import

Reference:
    https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/import-dashboards/
Grid translation (from OSS_Connector_Guide.md):
    Grafana uses a 24-column grid with variable row heights (grid units).
    Position (canvas fraction) → Grafana grid:
        x = round(pos.x * 24)
        y = round(pos.y * 40)       # 40 grid rows = full height
        w = max(1, round(pos.width * 24))
        h = max(3, round(pos.height * 40 * 1.3))   # 1.3x row multiplier
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

# IR VisualType → Grafana panel type strings
_VISUAL_TYPE_MAP: Dict[VisualType, List[str]] = {
    VisualType.KPI_CARD:        ["stat"],
    VisualType.TREND_LINE:      ["timeseries"],
    VisualType.BAR_CHART:       ["barchart"],
    VisualType.WATERFALL:       ["barchart"],   # Grafana has no native waterfall
    VisualType.SCATTER:         ["scatterplot", "xychart"],
    VisualType.MATRIX:          ["table"],
    VisualType.TABLE:           ["table"],
    VisualType.SLICER:          ["text"],
    VisualType.SMART_NARRATIVE: ["text"],
    VisualType.ACTION_PANEL:    ["text"],
    VisualType.TEXT_BOX:        ["text"],
}

# Semantic role → Grafana threshold color
_SEMANTIC_THRESHOLDS = {
    "negative": {"color": "#A4262C", "value": None},
    "warning":  {"color": "#C98A00", "value": 0},
    "positive": {"color": "#107C10", "value": 1},
}


def _pos_to_grafana_grid(pos) -> Dict[str, int]:
    return {
        "x": round(pos.x * 24),
        "y": round(pos.y * 40),
        "w": max(1, round(pos.width * 24)),
        "h": max(3, round(pos.height * 40 * 1.3)),
    }


def _build_panel(visual: VisualSpec, panel_id: int, panel_type: str,
                 datasource: str) -> Dict[str, Any]:
    """Build one Grafana panel dict."""
    g = _pos_to_grafana_grid(visual.position)
    binding = visual.binding

    # Targets (SQL queries) from measure bindings
    targets: List[Dict[str, Any]] = []
    measures = ([binding.measure] if binding.measure else []) + list(binding.measures or [])
    for i, m in enumerate(measures):
        targets.append({
            "datasource": {"type": "postgres", "uid": datasource},
            "rawSql": f'SELECT $__timeGroup("date", $__interval), SUM("{m}") FROM fact_table WHERE $__timeFilter("date") GROUP BY 1',
            "refId": chr(65 + i),  # A, B, C, ...
            "format": "time_series" if visual.visual_type == VisualType.TREND_LINE else "table",
        })

    if not targets:
        targets.append({
            "datasource": {"type": "postgres", "uid": datasource},
            "rawSql": "SELECT 1",
            "refId": "A",
            "format": "table",
        })

    # Panel-type-specific options
    options: Dict[str, Any] = {}
    field_config: Dict[str, Any] = {"defaults": {}, "overrides": []}

    if panel_type == "stat":
        options = {"reduceOptions": {"calcs": ["lastNotNull"]}, "orientation": "auto",
                   "colorMode": "background", "graphMode": "area"}
        field_config["defaults"]["thresholds"] = {
            "mode": "absolute",
            "steps": [
                _SEMANTIC_THRESHOLDS["negative"],
                _SEMANTIC_THRESHOLDS["warning"],
                _SEMANTIC_THRESHOLDS["positive"],
            ],
        }
    elif panel_type == "timeseries":
        options = {"legend": {"displayMode": "list", "placement": "bottom"}}
        field_config["defaults"]["color"] = {"mode": "palette-classic"}
    elif panel_type in ("barchart",):
        options = {"orientation": "horizontal"}
        field_config["defaults"]["color"] = {"mode": "palette-classic"}
    elif panel_type == "table":
        options = {"showHeader": True}
    elif panel_type == "text":
        options = {"content": visual.title or visual.id, "mode": "markdown"}
        targets = []  # text panels don't query data

    return {
        "id":          panel_id,
        "title":       visual.title or visual.id,
        "type":        panel_type,
        "datasource":  {"type": "postgres", "uid": datasource},
        "gridPos":     g,
        "targets":     targets,
        "options":     options,
        "fieldConfig": field_config,
        "transparent": False,
    }


class GrafanaAdapter(GeneratorAdapter):
    """
    Renders a DashboardSpec to a Grafana dashboard JSON export.

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
        """Deploy dashboard.json to a live Grafana instance via POST /api/dashboards/import."""
        import urllib.request
        token = (credentials or {}).get("token", "")
        if not token:
            raise ValueError("deploy() requires credentials={'token': '<api_key>'}")
        content = result.files.get("dashboard.json", b"")
        req = urllib.request.Request(
            f"{target_url.rstrip('/')}/api/dashboards/import",
            data=content,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status in (200, 201, 202)

    def render(self, spec: DashboardSpec) -> RenderResult:
        """
        Render DashboardSpec → Grafana dashboard JSON.

        Returns RenderResult with one file:
            "dashboard.json" → importable via Grafana UI or API
        """
        warnings: List[str] = []
        panels: List[Dict[str, Any]] = []
        panel_id = 1
        datasource = spec.semantic_model or f"{spec.domain.lower()}_datasource"

        for page in spec.pages:
            # Add a row panel as page separator
            row_title = "Overview (3s–30s)" if page.role == PageRole.OVERVIEW else "Detail (300s)"
            panels.append({
                "id": panel_id,
                "title": row_title,
                "type": "row",
                "gridPos": {"h": 1, "w": 24, "x": 0,
                            "y": 0 if page.role == PageRole.OVERVIEW else 20},
                "collapsed": False,
                "panels": [],
            })
            panel_id += 1

            for visual in page.visuals:
                panel_type = self.map_visual_type(visual.visual_type)
                if panel_type == visual.visual_type.value:
                    warnings.append(f"No Grafana mapping for '{visual.visual_type}' ({visual.id})")
                panel = _build_panel(visual, panel_id, panel_type, datasource)
                panels.append(panel)
                panel_id += 1

        uid = spec.use_case_id.lower().replace("-", "")[:40]
        dashboard = {
            "__inputs": [
                {"name": "DS_POSTGRES", "label": "Analytics Database",
                 "description": "", "type": "datasource", "pluginId": "postgres"}
            ],
            "__requires": [
                {"type": "grafana", "id": "grafana", "name": "Grafana", "version": "10.0.0"},
                {"type": "datasource", "id": "postgres", "name": "PostgreSQL", "version": "1.0.0"},
            ],
            "id":            None,
            "uid":           uid,
            "title":         spec.title,
            "description":   f"Generated from {spec.use_case_id} — {spec.domain}",
            "tags":          [spec.domain.lower(), spec.use_case_id.lower()],
            "schemaVersion": 38,
            "version":       1,
            "refresh":       "5m",
            "time":          {"from": "now-30d", "to": "now"},
            "timepicker":    {},
            "panels":        panels,
            "templating":    {"list": []},
            "annotations":   {"list": []},
        }

        payload = json.dumps({"dashboard": dashboard, "overwrite": False}, indent=2, ensure_ascii=False)
        return RenderResult(
            files={"dashboard.json": payload.encode("utf-8")},
            adapter=self.name,
            warnings=warnings,
        )
