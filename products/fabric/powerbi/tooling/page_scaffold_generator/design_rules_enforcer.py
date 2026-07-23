"""
Design Rules Enforcer (R2.3, Cut C2)

Loads core/templates/page_templates/design_rules.yaml (R2.2) and enforces it
against a Bracket (pre-generation) and the generated page structure
(post-generation), producing "<RULE_ID>: <message>" strings suitable for
PageScaffoldGenerator.validate()'s existing error-list convention.

Only runs when ux_layout_rules.intent_rules_version == 2 -- brackets that
have not opted into the R2.1 intent layer are exempt (same gating as the
schema's own if/then), matching the transition-rule design established in
R2.1/R2.2. This module deliberately does NOT implement a generic rule
engine: design_rules.schema.json closes `check` to exactly four literal
values, and each has its own small, explicit function here.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

DEFAULT_DESIGN_RULES_PATH = (
    Path(__file__).resolve().parents[5] / "core" / "templates" / "page_templates" / "design_rules.yaml"
)


def load_design_rules(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load design_rules.yaml's rule list. Returns [] if the file is missing."""

    rules_path = path or DEFAULT_DESIGN_RULES_PATH
    if not rules_path.exists():
        logger.warning("design_rules.yaml not found at %s -- no design rules will be enforced.", rules_path)
        return []
    data = yaml.safe_load(rules_path.read_text(encoding="utf-8")) or {}
    return data.get("rules") or []


def _rules_by_check(rules: List[Dict[str, Any]], check: str) -> List[Dict[str, Any]]:
    return [r for r in rules if r.get("check") == check]


# ---------------------------------------------------------------------------
# Pre-generation checks (Bracket content only)
# ---------------------------------------------------------------------------


def check_single_unit_family_per_component(
    rule: Dict[str, Any],
    component_30s: List[Dict[str, Any]],
    kpi_id_to_calc_type: Dict[str, str],
) -> List[str]:
    """ONE_MESSAGE_PER_CHART: every kpi_id referenced by a component_30s entry that
    IS a known governed KPI must share its declared `unit`. KPI ids/measure names not
    found in the catalog (e.g. a raw measure name like "Plan GM Amount") are skipped,
    not treated as violations -- same "unknown, not a mismatch" posture as
    report_scorecard.scale_family."""

    violations: List[str] = []
    for entry in component_30s:
        unit = entry.get("unit")
        if not unit:
            continue
        kpi_id = entry.get("kpi_id")
        kpi_ids = entry.get("kpi_ids") or ([kpi_id] if kpi_id else [])
        if not isinstance(kpi_ids, list):
            kpi_ids = [kpi_ids]
        mismatched = []
        for kid in kpi_ids:
            if not isinstance(kid, str):
                continue
            calc_type = kpi_id_to_calc_type.get(kid)
            if calc_type and calc_type != unit:
                mismatched.append(f"{kid} (calc_type={calc_type})")
        if mismatched:
            slot = entry.get("slot_id", "?")
            violations.append(
                f"{rule['id']}: component_30s[slot_id={slot}] declares unit='{unit}' but "
                f"references KPI(s) with a different calc_type: {', '.join(mismatched)}"
            )
    return violations


def check_max_count(rule: Dict[str, Any], actual_count: int) -> List[str]:
    """MAX_EVIDENCE_COLUMNS / MAX_SEMANTIC_COLORS_PER_PAGE: generic count ceiling."""

    max_allowed = rule["parameters"]["max"]
    if actual_count > max_allowed:
        target = rule["parameters"].get("field") or rule["parameters"].get("target") or "items"
        return [f"{rule['id']}: {target} count is {actual_count}, exceeds max {max_allowed}"]
    return []


def check_bracket_rules(
    rules: List[Dict[str, Any]],
    bracket: Dict[str, Any],
    kpi_id_to_calc_type: Dict[str, str],
) -> List[str]:
    """Pre-generation checks: ONE_MESSAGE_PER_CHART, MAX_EVIDENCE_COLUMNS,
    MAX_SEMANTIC_COLORS_PER_PAGE. Only runs when intent_rules_version == 2."""

    ux = bracket.get("ux_layout_rules") or {}
    if ux.get("intent_rules_version") != 2:
        return []

    errors: List[str] = []

    p1 = ux.get("page_1_summary") or {}
    component_30s = p1.get("component_30s") or []
    if not isinstance(component_30s, list):
        component_30s = []

    for rule in _rules_by_check(rules, "single_unit_family_per_component"):
        errors.extend(check_single_unit_family_per_component(rule, component_30s, kpi_id_to_calc_type))

    p2 = ux.get("page_2_execution") or {}
    component_300s = p2.get("component_300s") or {}
    evidence_columns = component_300s.get("evidence_columns") or []
    for rule in _rules_by_check(rules, "max_count"):
        if rule["id"] == "MAX_EVIDENCE_COLUMNS":
            errors.extend(check_max_count(rule, len(evidence_columns)))
        elif rule["id"] == "MAX_SEMANTIC_COLORS_PER_PAGE":
            # Approximation: status_logic drives semantic color assignment
            # (Color_Semantics_Formatting.md "Signal Color Logic") -- count
            # status_logic-bearing components as a proxy for semantic colors in
            # play, since we validate the Bracket, not rendered pixels.
            status_logic_count = sum(
                1 for c in ([p1.get("component_3s")] + component_30s) if isinstance(c, dict) and c.get("status_logic")
            )
            errors.extend(check_max_count(rule, status_logic_count))

    return errors


# ---------------------------------------------------------------------------
# Post-generation checks (generated page structure)
# ---------------------------------------------------------------------------


def check_output_matches_declared_sort(
    rule: Dict[str, Any],
    sort_by: Optional[Dict[str, str]],
    generated_visual: Optional[Dict[str, Any]],
) -> List[str]:
    """MANDATORY_SORT_RENDERED: the generated Detail_Matrix's query.sortDefinition
    must be non-empty, isDefaultSort=true, and match the declared sort_by exactly."""

    if not sort_by:
        return []
    if generated_visual is None:
        return [f"{rule['id']}: sort_by declared but no Detail_Matrix visual was generated"]
    sort_def = (generated_visual.get("visual", {}).get("query", {}) or {}).get("sortDefinition")
    if not sort_def or not sort_def.get("sort") or not sort_def.get("isDefaultSort"):
        return [f"{rule['id']}: Detail_Matrix has no rendered sortDefinition (sort_by was declared: {sort_by})"]
    rendered_measure = sort_def["sort"][0].get("field", {}).get("Measure", {}).get("Property")
    if rendered_measure != sort_by.get("measure"):
        return [
            f"{rule['id']}: rendered sort measure '{rendered_measure}' does not match "
            f"declared sort_by.measure '{sort_by.get('measure')}'"
        ]
    return []


def check_header_text_equals_big_idea(
    rule: Dict[str, Any],
    big_idea: Optional[str],
    generated_visuals: List[Dict[str, Any]],
) -> List[str]:
    """BIG_IDEA_HEADER_ZONE: the Header textbox must render big_idea verbatim.

    `page_1_summary.big_idea` is the single rendered source of truth for this text. It is either
    hand-authored (the D4 fallback floor) or produced by the ADR-0017 Stage-2 generator
    `tooling/storyline/compose_narrative.py` — which proposes an updated Big Idea from the top verified
    finding and reports drift via `--check`, but never bypasses this field. So this verbatim rule stays
    authoritative for the render; the composer feeds the field, it does not compete with this check.
    """

    if not big_idea:
        return []
    header = next((v for v in generated_visuals if v.get("name") == "Header"), None)
    if header is None:
        return [f"{rule['id']}: page_1_summary.big_idea is set but no Header visual was generated"]
    text_objs = header.get("visual", {}).get("objects", {}).get("text") or []
    if not text_objs:
        return [f"{rule['id']}: Header visual has no text object"]
    rendered = text_objs[0].get("properties", {}).get("text", {}).get("expr", {}).get("Literal", {}).get("Value", "")
    # Rendered literal is a single-quoted PBIR string with '' as the escaped quote.
    rendered_unquoted = rendered[1:-1].replace("''", "'") if rendered.startswith("'") and rendered.endswith("'") else rendered
    if rendered_unquoted != big_idea:
        return [f"{rule['id']}: Header text does not match page_1_summary.big_idea verbatim"]
    return []


def check_output_rules(
    rules: List[Dict[str, Any]],
    bracket: Dict[str, Any],
    overview_visuals: Optional[List[Dict[str, Any]]] = None,
    detail_matrix_sort_by: Optional[Dict[str, str]] = None,
    detail_matrix_visual: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Post-generation checks: MANDATORY_SORT_RENDERED, BIG_IDEA_HEADER_ZONE. Only
    runs when intent_rules_version == 2. Callers pass whichever generated artifacts
    they have on hand (overview-page callers pass overview_visuals; detail-page
    callers pass detail_matrix_sort_by/detail_matrix_visual)."""

    ux = bracket.get("ux_layout_rules") or {}
    if ux.get("intent_rules_version") != 2:
        return []

    errors: List[str] = []

    if overview_visuals is not None:
        big_idea = (ux.get("page_1_summary") or {}).get("big_idea")
        for rule in _rules_by_check(rules, "header_text_equals_big_idea"):
            errors.extend(check_header_text_equals_big_idea(rule, big_idea, overview_visuals))

    if detail_matrix_sort_by is not None or detail_matrix_visual is not None:
        for rule in _rules_by_check(rules, "output_matches_declared_sort"):
            errors.extend(check_output_matches_declared_sort(rule, detail_matrix_sort_by, detail_matrix_visual))

    return errors
