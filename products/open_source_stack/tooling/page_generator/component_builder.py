"""
Component Builder

Maps visual slot types from the governance layer to Evidence.dev
component markup (Markdown + Svelte components).

Mirrors Fabric's VisualBuilder / SlicerBuilder but emits Evidence
Markdown syntax instead of PBIP JSON.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# -- Slot type → Evidence component mapping --------------------------------

COMPONENT_MAP: Dict[str, str] = {
    "kpi_card":         "BigValue",
    "kpi_card_delta":   "BigValue",
    "trend_line":       "LineChart",
    "bar_chart":        "BarChart",
    "area_chart":       "AreaChart",
    "matrix":           "DataTable",
    "data_table":       "DataTable",
    "slicer_dropdown":  "Dropdown",
    "slicer_button":    "ButtonGroup",
    "smart_narrative":  "Value",
    "action_panel":     "Alert",
}


class ComponentBuilder:
    """Build Evidence Markdown component blocks from visual slot definitions."""

    def build_sql_block(
        self,
        query_name: str,
        table: str,
        measures: List[str],
        dimensions: Optional[List[str]] = None,
        filters: Optional[str] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> str:
        """Generate a named SQL code block for Evidence."""
        cols = ", ".join(dimensions or []) + (", " if dimensions else "")
        cols += ", ".join(measures)
        sql = f"SELECT\n  {cols}\nFROM {table}"
        if filters:
            sql += f"\nWHERE {filters}"
        if order_by:
            sql += f"\nORDER BY {order_by}"
        if limit:
            sql += f"\nLIMIT {limit}"
        return f"```sql {query_name}\n{sql}\n```"

    def build_component(
        self,
        slot_type: str,
        query_name: str,
        props: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate an Evidence component tag for a given slot type."""
        component = COMPONENT_MAP.get(slot_type)
        if component is None:
            return f"<!-- Unknown slot type: {slot_type} -->"

        tag_props = f'data={{{query_name}}}'
        if props:
            for k, v in props.items():
                if isinstance(v, str):
                    tag_props += f' {k}="{v}"'
                else:
                    tag_props += f" {k}={{{v}}}"

        return f"<{component} {tag_props} />"

    def build_kpi_card(
        self,
        query_name: str,
        value_col: str = "value",
        title: str = "",
        comparison_col: Optional[str] = None,
    ) -> str:
        """Build a BigValue KPI card."""
        props = {"value": value_col, "title": f'"{title}"'}
        if comparison_col:
            props["comparison"] = comparison_col
        return self.build_component("kpi_card", query_name, props)

    def build_chart(
        self,
        slot_type: str,
        query_name: str,
        x: str,
        y: str,
        series: Optional[str] = None,
        title: Optional[str] = None,
    ) -> str:
        """Build a chart component (LineChart, BarChart, AreaChart)."""
        props: Dict[str, Any] = {"x": x, "y": y}
        if series:
            props["series"] = series
        if title:
            props["title"] = f'"{title}"'
        return self.build_component(slot_type, query_name, props)

    def build_data_table(self, query_name: str) -> str:
        """Build a DataTable component."""
        return self.build_component("data_table", query_name)

    def build_slicer(
        self,
        slot_type: str,
        query_name: str,
        name: str,
        value_col: str,
        label_col: Optional[str] = None,
    ) -> str:
        """Build a filter/slicer component."""
        props: Dict[str, Any] = {"name": name, "value": value_col}
        if label_col:
            props["label"] = label_col
        return self.build_component(slot_type, query_name, props)
