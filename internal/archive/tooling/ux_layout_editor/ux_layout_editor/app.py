"""
Streamlit mockup editor: load UseCase_Bracket, show dropdowns per visual (slot-allowed types),
validate on save, write ux_layout_rules back to YAML.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st
import yaml

from draft_ux_layout import build_draft, find_bracket_path
from preview_charts import build_preview_chart
from validator import validate_ux_layout_rules

_EDITOR_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _EDITOR_DIR.parent.parent
_CONFIG_DIR = _EDITOR_DIR / "config"


def _load_yaml(path: Path) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _save_yaml(path: Path, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def list_use_case_ids(repo_root: Path) -> List[str]:
    base = repo_root / "core" / "usecases" / "core"
    if not base.exists():
        return []
    ids = []
    for d in base.iterdir():
        if d.is_dir() and d.name.count("-") >= 1:
            # e.g. COM-001_Sales_Performance -> COM-001
            ids.append(d.name.split("_", 1)[0])
    return sorted(ids)


def get_slot_order_and_allowed(repo_root: Path) -> tuple:
    slot_order = _load_yaml(_CONFIG_DIR / "slot_order_by_report.yaml")
    slot_visual = _load_yaml(_CONFIG_DIR / "slot_to_visual_allowed.yaml")
    return slot_order, slot_visual


def main() -> None:
    st.set_page_config(page_title="UX Layout Editor", layout="wide")

    repo_root = Path(st.sidebar.text_input("Repo root", value=str(_REPO_ROOT)))
    use_case_ids = list_use_case_ids(repo_root)
    selected_id = st.sidebar.selectbox(
        "Use case",
        options=use_case_ids or [""],
        format_func=lambda x: x or "(none)",
    )

    if not selected_id:
        st.info("Select a use case from the sidebar (repo root must contain core/usecases/core).")
        return

    bracket_path = find_bracket_path(repo_root, selected_id)
    if not bracket_path:
        st.error(f"Use case {selected_id} not found.")
        return

    bracket = _load_yaml(bracket_path)
    slot_order_config, slot_to_visual_config = get_slot_order_and_allowed(repo_root)
    slots_cfg = (slot_to_visual_config.get("slots") or {})
    structures = (slot_order_config.get("report_structures") or {})
    report_structure = (bracket.get("ux_layout_rules") or {}).get("report_structure") or "2-Page-Lead"
    slot_def = structures.get(report_structure) or {}
    slots_list: List[str] = slot_def.get("component_30s_slots") or ["Trend", "Variance"]

    # Current rules: from bracket or draft
    ux = bracket.get("ux_layout_rules")
    if not ux or not ux.get("page_1_summary"):
        draft = build_draft(bracket, slot_order_config, slot_to_visual_config)
        ux = draft
        st.sidebar.info("Draft loaded (no/incomplete ux_layout_rules). Edit and Save to apply.")

    if "ux_layout_rules" not in st.session_state:
        st.session_state["ux_layout_rules"] = dict(ux)

    rules = st.session_state["ux_layout_rules"]
    p1 = rules.get("page_1_summary") or {}
    c3s = p1.get("component_3s") or {}
    c30s = p1.get("component_30s") or []

    st.subheader(f"UX Layout: {selected_id}")

    # component_3s
    slot_name_3s = "KPI_Summary"
    allowed_3s = (slots_cfg.get(slot_name_3s) or {}).get("allowed_visual_types") or ["kpi_card"]
    current_3s = c3s.get("visual_type") or allowed_3s[0]
    kpi_id_3s = c3s.get("kpi_id") or ""
    st.text_input("KPI Card (3s) — KPI ID", value=kpi_id_3s, key="c3s_kpi_id", disabled=True)
    idx_3s = allowed_3s.index(current_3s) if current_3s in allowed_3s else 0
    new_3s = st.selectbox(
        "Visual type (3s)",
        options=allowed_3s,
        index=idx_3s,
        key="c3s_visual",
    )
    if new_3s != current_3s:
        rules.setdefault("page_1_summary", {}).setdefault("component_3s", {})["visual_type"] = new_3s
        rules["page_1_summary"]["component_3s"]["kpi_id"] = kpi_id_3s
        st.session_state["ux_layout_rules"] = rules

    st.markdown("---")
    st.markdown("**Diagnostic charts (30s)**")

    for i in range(max(len(c30s), len(slots_list))):
        slot_name = slots_list[i] if i < len(slots_list) else "Trend"
        slot_cfg = slots_cfg.get(slot_name) or {}
        allowed = slot_cfg.get("allowed_visual_types") or ["bar_chart"]
        item = c30s[i] if i < len(c30s) else {}
        current_vt = item.get("visual_type") or slot_cfg.get("default") or allowed[0]
        kpi_id = item.get("kpi_id") or ""
        kpi_ids = item.get("kpi_ids") or []
        label = f"Chart {i + 1} ({slot_name})"
        st.text_input(
            f"{label} — KPI(s)",
            value=kpi_id or ", ".join(kpi_ids) if kpi_ids else "",
            key=f"c30s_kpi_{i}",
            disabled=True,
        )
        idx = allowed.index(current_vt) if current_vt in allowed else 0
        new_vt = st.selectbox(
            f"Visual type — {label}",
            options=allowed,
            index=idx,
            key=f"c30s_visual_{i}",
        )
        # Persist selection into rules
        while len(rules.get("page_1_summary", {}).get("component_30s", [])) <= i:
            rules.setdefault("page_1_summary", {}).setdefault("component_30s", []).append({})
        entry = rules["page_1_summary"]["component_30s"][i]
        entry["visual_type"] = new_vt
        if kpi_id:
            entry["kpi_id"] = kpi_id
            if "kpi_ids" in entry:
                del entry["kpi_ids"]
        elif kpi_ids:
            entry["kpi_ids"] = kpi_ids
            if "kpi_id" in entry:
                del entry["kpi_id"]
        st.session_state["ux_layout_rules"] = rules

    st.markdown("---")
    st.markdown("**Live Preview**")
    p1_preview = rules.get("page_1_summary") or {}
    c3s_preview = p1_preview.get("component_3s") or {}
    c30s_preview = p1_preview.get("component_30s") or []
    kpi_label = c3s_preview.get("kpi_id") or "North Star KPI"
    st.metric(label=kpi_label, value="—", delta=None)
    for i, item in enumerate(c30s_preview):
        vt = item.get("visual_type") or "bar_chart"
        kpi_id = item.get("kpi_id") or ""
        kpi_ids = item.get("kpi_ids") or []
        title = kpi_id or (", ".join(kpi_ids)[:50] + ("..." if len(", ".join(kpi_ids)) > 50 else "") if kpi_ids else f"Chart {i + 1}")
        fig = build_preview_chart(vt, kpi_id=kpi_id or None, kpi_ids=kpi_ids or None, title=title)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("**Page 2 (Execution)** — evidence_grain, evidence_columns, action_panel, payload_mode are read-only here.")

    if st.button("Save to UseCase_Bracket.yaml"):
        to_save = dict(st.session_state["ux_layout_rules"])
        ok, errs = validate_ux_layout_rules(
            to_save,
            report_structure=to_save.get("report_structure", "2-Page-Lead"),
            slot_order_config=slot_order_config,
            slot_to_visual_allowed=slot_to_visual_config,
        )
        if not ok:
            for e in errs:
                st.error(e)
        else:
            full_bracket = _load_yaml(bracket_path)
            full_bracket["ux_layout_rules"] = to_save
            _save_yaml(bracket_path, full_bracket)
            st.success(f"Saved to {bracket_path}")

    st.sidebar.markdown("---")
    st.sidebar.caption("Live Preview mit echten Chart-Typen siehst du unten.")


if __name__ == "__main__":
    main()
