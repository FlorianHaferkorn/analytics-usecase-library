"""
action_panel.py — Dynamic ActionPanel visual generator.

Builds a PBIP visual.json for the ActionPanel slot that renders rows from
fact_action_outcome filtered to the current use case's action codes.

The panel uses a matrix visual bound to fact_action_outcome with:
  Rows:    action_code_id, severity_level, outcome_status
  Values:  Actions Executed Count, Action Outcome Rate %, Avg Time-to-Outcome Days

This replaces the hard-coded textbox ActionPanel from the old scaffold path.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from products.fabric.powerbi.tooling.schema_registry import VISUAL_SCHEMA as _VISUAL_SCHEMA


def _entity_ref(table: str, column: str) -> Dict[str, Any]:
    return {
        "Column": {
            "Expression": {"SourceRef": {"Entity": table}},
            "Property": column,
        }
    }


def _measure_ref(measure_name: str, table: str = "_Measures") -> Dict[str, Any]:
    return {
        "Measure": {
            "Expression": {"SourceRef": {"Entity": table}},
            "Property": measure_name,
        }
    }


def _projection(field_expr: Dict, query_ref: str, native_ref: str) -> Dict[str, Any]:
    return {
        "field": field_expr,
        "queryRef": query_ref,
        "nativeQueryRef": native_ref,
    }


def _build_action_panel_visual(
    slot_id: str,
    position_px: Dict[str, int],
    action_code_ids: Optional[List[str]] = None,
    use_case_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build PBIP visual.json for the ActionPanel slot.

    Uses a pivotTable (matrix) visual bound to fact_action_outcome.
    An optional action_code_ids list adds an inline filter so the panel
    shows only actions relevant to this use case.
    """
    # Row dimensions
    row_projections = [
        _projection(
            _entity_ref("fact_action_outcome", "action_code_id"),
            "fact_action_outcome.action_code_id",
            "action_code_id",
        ),
        _projection(
            _entity_ref("fact_action_outcome", "severity_level"),
            "fact_action_outcome.severity_level",
            "severity_level",
        ),
        _projection(
            _entity_ref("fact_action_outcome", "outcome_status"),
            "fact_action_outcome.outcome_status",
            "outcome_status",
        ),
    ]

    # Value measures
    outcome_measures = [
        "Actions Executed Count",
        "Action Outcome Rate %",
        "Avg Time-to-Outcome Days",
        "Action ROI %",
    ]
    value_projections = [
        _projection(
            _measure_ref(m),
            f"_Measures.{m}",
            m,
        )
        for m in outcome_measures
    ]

    query_state: Dict[str, Any] = {
        "Rows": {"projections": row_projections},
        "Values": {"projections": value_projections},
    }

    # Inline filter for this use case's action codes
    filters: List[Dict[str, Any]] = []
    if action_code_ids:
        filters.append({
            "expression": {
                "In": {
                    "Expressions": [
                        {"Column": {
                            "Expression": {"SourceRef": {"Entity": "fact_action_outcome"}},
                            "Property": "action_code_id",
                        }}
                    ],
                    "Values": [[{"Literal": {"Value": f"'{ac}'"}}] for ac in action_code_ids],
                }
            }
        })

    visual: Dict[str, Any] = {
        "$schema": _VISUAL_SCHEMA,
        "name": slot_id,
        "position": position_px,
        "visual": {
            "visualType": "pivotTable",
            "query": {
                "queryState": query_state,
                "sortDefinition": {"sort": [], "isDefaultSort": True},
            },
            "objects": {
                "general": [{"properties": {"outspace": {"expr": {"Literal": {"Value": "true"}}}}}]
            },
        },
    }
    if filters:
        visual["visual"]["filters"] = filters
    if use_case_id:
        visual["visual"]["title"] = {
            "display": f"Action Outcomes — {use_case_id}",
        }

    return visual


def build_action_panel_json(
    slot_id: str = "ActionPanel",
    canvas_w: int = 1280,
    canvas_h: int = 720,
    pos_x_frac: float = 0.78,
    pos_y_frac: float = 0.0,
    pos_w_frac: float = 0.22,
    pos_h_frac: float = 1.0,
    action_code_ids: Optional[List[str]] = None,
    use_case_id: Optional[str] = None,
) -> str:
    """Return PBIP visual.json string for the ActionPanel slot."""
    position_px = {
        "x": round(pos_x_frac * canvas_w),
        "y": round(pos_y_frac * canvas_h),
        "width":  round(pos_w_frac * canvas_w),
        "height": round(pos_h_frac * canvas_h),
    }
    visual = _build_action_panel_visual(
        slot_id=slot_id,
        position_px=position_px,
        action_code_ids=action_code_ids,
        use_case_id=use_case_id,
    )
    return json.dumps(visual, indent=2, ensure_ascii=False)
