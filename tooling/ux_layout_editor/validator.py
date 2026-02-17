"""
Validator for ux_layout_rules: ensures (slot, visual_type) combinations
are allowed and required fields are present. Used by draft generator and Streamlit app.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# Default config paths relative to this package
_CONFIG_DIR = Path(__file__).resolve().parent / "config"
_SLOT_ORDER_PATH = _CONFIG_DIR / "slot_order_by_report.yaml"
_SLOT_VISUAL_PATH = _CONFIG_DIR / "slot_to_visual_allowed.yaml"


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _get_slot_order_config() -> Dict[str, Any]:
    return _load_yaml(_SLOT_ORDER_PATH)


def _get_slot_to_visual_config() -> Dict[str, Any]:
    return _load_yaml(_SLOT_VISUAL_PATH)


def validate_ux_layout_rules(
    ux_layout_rules: Dict[str, Any],
    report_structure: str = "2-Page-Lead",
    slot_order_config: Optional[Dict[str, Any]] = None,
    slot_to_visual_allowed: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, List[str]]:
    """
    Validate ux_layout_rules against slot order and visual whitelist.

    Returns:
        (success, list of error messages)
    """
    errors: List[str] = []

    if slot_order_config is None:
        slot_order_config = _get_slot_order_config()
    if slot_to_visual_allowed is None:
        slot_to_visual_allowed = _get_slot_to_visual_config()

    if not ux_layout_rules:
        return False, ["ux_layout_rules is empty"]

    # Required top-level keys
    for key in ("report_structure", "page_1_summary", "page_2_execution"):
        if key not in ux_layout_rules:
            errors.append(f"Missing required key: {key}")

    rs = ux_layout_rules.get("report_structure") or report_structure
    structures = slot_order_config.get("report_structures") or {}
    slot_order_def = structures.get(rs)
    slots_list = slot_order_def.get("component_30s_slots", []) if slot_order_def else []

    slots_config = (slot_to_visual_allowed.get("slots") or {})

    # component_3s
    p1 = ux_layout_rules.get("page_1_summary")
    if isinstance(p1, dict):
        c3s = p1.get("component_3s")
        if isinstance(c3s, dict):
            vt = c3s.get("visual_type")
            kpi_slot = slots_config.get("KPI_Summary", {})
            allowed = kpi_slot.get("allowed_visual_types") or ["kpi_card"]
            if vt and vt not in allowed:
                errors.append(f"component_3s.visual_type '{vt}' not in allowed for KPI_Summary: {allowed}")
            if not c3s.get("kpi_id"):
                errors.append("component_3s.kpi_id is required")
        else:
            errors.append("page_1_summary.component_3s must be an object with kpi_id and visual_type")

        # component_30s
        c30s = p1.get("component_30s")
        if isinstance(c30s, list):
            for i, item in enumerate(c30s):
                if not isinstance(item, dict):
                    errors.append(f"component_30s[{i}] must be an object")
                    continue
                vt = item.get("visual_type")
                if not vt:
                    errors.append(f"component_30s[{i}].visual_type is required")
                    continue
                slot_name = slots_list[i] if i < len(slots_list) else None
                if slot_name:
                    slot_cfg = slots_config.get(slot_name, {})
                    allowed = slot_cfg.get("allowed_visual_types") or []
                    if allowed and vt not in allowed:
                        errors.append(
                            f"component_30s[{i}].visual_type '{vt}' not allowed for slot '{slot_name}'. Allowed: {allowed}"
                        )
                if not item.get("kpi_id") and not item.get("kpi_ids"):
                    errors.append(f"component_30s[{i}] must have kpi_id or kpi_ids")
        else:
            errors.append("page_1_summary.component_30s must be an array")

    # page_2_execution.component_300s
    p2 = ux_layout_rules.get("page_2_execution")
    if isinstance(p2, dict):
        c300 = p2.get("component_300s")
        if isinstance(c300, dict):
            for key in ("evidence_grain", "evidence_columns", "action_panel", "payload_mode"):
                if key not in c300:
                    errors.append(f"page_2_execution.component_300s.{key} is required")
            grain = c300.get("evidence_grain")
            if grain == "transaction_line":
                errors.append("evidence_grain 'transaction_line' is forbidden (use a governed grain)")
            if c300.get("payload_mode") and c300["payload_mode"] not in ("full", "summary", "minimal"):
                errors.append("payload_mode must be one of: full, summary, minimal")
        else:
            errors.append("page_2_execution.component_300s must be an object")

    return len(errors) == 0, errors
