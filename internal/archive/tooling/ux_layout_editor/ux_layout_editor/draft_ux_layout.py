"""
Rule-based draft of ux_layout_rules from orchestration, slot order, and visual mapping.
Reads UseCase_Bracket.yaml; derives component_3s and component_30s; optionally applies.
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Allow running from repo root or from tooling/ux_layout_editor
_EDITOR_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _EDITOR_DIR.parent.parent
_CONFIG_DIR = _EDITOR_DIR / "config"

sys.path.insert(0, str(_EDITOR_DIR))
from validator import validate_ux_layout_rules  # noqa: E402


def _load_yaml(path: Path) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _save_yaml(path: Path, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def find_bracket_path(repo_root: Path, use_case_id: str) -> Optional[Path]:
    """Resolve use-case ID (e.g. COM-001) to UseCase_Bracket.yaml path under core/usecases/core."""
    base = repo_root / "core" / "usecases" / "core"
    if not base.exists():
        return None
    for d in base.iterdir():
        if d.is_dir() and d.name.startswith(use_case_id + "_"):
            bracket = d / "UseCase_Bracket.yaml"
            if bracket.exists():
                return bracket
    return None


def build_draft(
    bracket: Dict[str, Any],
    slot_order_config: Dict[str, Any],
    slot_to_visual_config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build ux_layout_rules draft from bracket orchestration and configs.
    Preserves existing page_2_execution if present and valid; otherwise uses defaults.
    """
    existing = bracket.get("ux_layout_rules") or {}
    report_structure = existing.get("report_structure") or "2-Page-Lead"
    structures = slot_order_config.get("report_structures") or {}
    slot_def = structures.get(report_structure) or {}
    slots_list: List[str] = slot_def.get("component_30s_slots") or ["Trend", "Variance"]
    slots_cfg = (slot_to_visual_config.get("slots") or {})

    orch = bracket.get("orchestration") or {}
    strategic = orch.get("strategic_kpi_id") or ""
    influencing: List[str] = orch.get("influencing_kpi_ids") or []

    # component_3s: strategic KPI + kpi_card
    kpi_summary_cfg = slots_cfg.get("KPI_Summary") or {}
    default_3s_vt = (kpi_summary_cfg.get("allowed_visual_types") or ["kpi_card"])[0]
    component_3s = {
        "kpi_id": strategic,
        "visual_type": existing.get("page_1_summary", {}).get("component_3s", {}).get("visual_type") or default_3s_vt,
    }

    # component_30s: one entry per slot; default visual per slot; KPI(s) from influencing
    p1_existing = existing.get("page_1_summary") or {}
    c30s_existing = p1_existing.get("component_30s") or []
    component_30s: List[Dict[str, Any]] = []
    for i, slot_name in enumerate(slots_list):
        slot_cfg = slots_cfg.get(slot_name) or {}
        default_vt = slot_cfg.get("default") or (slot_cfg.get("allowed_visual_types") or ["bar_chart"])[0]
        existing_item = c30s_existing[i] if i < len(c30s_existing) else {}
        kpi_id = existing_item.get("kpi_id")
        kpi_ids = existing_item.get("kpi_ids")
        if not kpi_id and not kpi_ids:
            if i == 0 and influencing:
                kpi_id = influencing[0]
            elif i == 1 and len(influencing) > 1:
                kpi_ids = influencing[1:4]  # up to 3 KPIs for composite
            elif influencing:
                kpi_id = influencing[min(i, len(influencing) - 1)]
        visual_type = existing_item.get("visual_type") or default_vt
        allowed = slot_cfg.get("allowed_visual_types") or []
        if allowed and visual_type not in allowed:
            visual_type = slot_cfg.get("default") or allowed[0]
        item: Dict[str, Any] = {"visual_type": visual_type}
        if kpi_ids is not None:
            item["kpi_ids"] = kpi_ids
        if kpi_id is not None:
            item["kpi_id"] = kpi_id
        component_30s.append(item)

    page_1_summary = {
        "title": p1_existing.get("title") or "Summary & Insights",
        "component_3s": component_3s,
        "component_30s": component_30s,
    }

    # page_2_execution: keep existing component_300s if valid, else minimal defaults
    p2_existing = existing.get("page_2_execution") or {}
    c300_existing = p2_existing.get("component_300s") or {}
    component_300s = {
        "evidence_grain": c300_existing.get("evidence_grain") or "invoice_line",
        "evidence_columns": c300_existing.get("evidence_columns") or ["entity", "period"],
        "action_panel": c300_existing.get("action_panel") if "action_panel" in c300_existing else True,
        "payload_mode": c300_existing.get("payload_mode") or "full",
    }
    page_2_execution = {
        "title": p2_existing.get("title") or "Execution",
        "component_300s": component_300s,
    }

    return {
        "report_structure": report_structure,
        "page_1_summary": page_1_summary,
        "page_2_execution": page_2_execution,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Draft ux_layout_rules from orchestration and slot config.")
    parser.add_argument("--use-case", required=True, help="Use case ID (e.g. COM-001)")
    parser.add_argument("--apply", action="store_true", help="Write draft into UseCase_Bracket.yaml after validation")
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT, help="Repository root")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    bracket_path = find_bracket_path(repo_root, args.use_case)
    if not bracket_path:
        print(f"Use case {args.use_case} not found under core/usecases/core.", file=sys.stderr)
        return 1

    bracket = _load_yaml(bracket_path)
    slot_order_config = _load_yaml(_CONFIG_DIR / "slot_order_by_report.yaml")
    slot_to_visual_config = _load_yaml(_CONFIG_DIR / "slot_to_visual_allowed.yaml")

    draft = build_draft(bracket, slot_order_config, slot_to_visual_config)
    ok, errs = validate_ux_layout_rules(
        draft,
        report_structure=draft.get("report_structure", "2-Page-Lead"),
        slot_order_config=slot_order_config,
        slot_to_visual_allowed=slot_to_visual_config,
    )
    if not ok:
        print("Validation failed:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        if args.apply:
            return 1

    if args.apply:
        bracket["ux_layout_rules"] = draft
        _save_yaml(bracket_path, bracket)
        print(f"Applied ux_layout_rules to {bracket_path}")
        return 0

    print(yaml.dump(draft, default_flow_style=False, allow_unicode=True, sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
