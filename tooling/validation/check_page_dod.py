#!/usr/bin/env python3
"""
check_page_dod.py — Page Definition of Done (DoD) Validator

Validates UseCase_Bracket.yaml files against the 10-item Page DoD
defined in core/templates/page_templates/governance/Page_DoD.md.

Usage:
    python tooling/validation/check_page_dod.py                  # all use cases
    python tooling/validation/check_page_dod.py FIN-001           # single use case by ID
    python tooling/validation/check_page_dod.py --exit-zero       # always exit 0 (CI warn mode)

Exit codes:
    0 — all checks pass (or --exit-zero)
    1 — one or more DoD items failed
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import yaml
except ImportError:
    if __name__ == "__main__":
        print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    raise

REPO = Path(__file__).resolve().parents[2]

# Canonical page type values accepted in page_type fields
_VALID_PAGE_TYPES = {
    "T1_Strategic_Overview",
    "T2_Tactical_Variance",
    "T3_Operational_Monitoring",
    "T4_Prescriptive_Recommendation",
}

# Short form → full form
_PAGE_TYPE_SHORT = {
    "T1": "T1_Strategic_Overview",
    "T2": "T2_Tactical_Variance",
    "T3": "T3_Operational_Monitoring",
    "T4": "T4_Prescriptive_Recommendation",
}

# Big Idea sentence templates per page type (regex pattern)
_BIG_IDEA_TEMPLATES: Dict[str, re.Pattern] = {
    "T1": re.compile(
        r".+\s+is\s+(on|off)\s+track.+", re.IGNORECASE
    ),
    "T2": re.compile(
        r".+\s+is\s+.+\s+vs\s+.+\s+—\s*.+", re.IGNORECASE
    ),
    "T3": re.compile(
        r"\d+\s+exception.+threshold.+", re.IGNORECASE
    ),
    "T4": re.compile(
        r".+(action|intervention|recommendation).+will\s+(recover|improve|reduce|increase).+", re.IGNORECASE
    ),
}

# Slots that are only valid on detail pages
_DETAIL_ONLY_SLOTS = {"Slicer_Pane", "Smart_Narrative", "Detail_Matrix", "ActionPanel"}

# Slots valid only on overview pages
_OVERVIEW_ONLY_SLOTS = {"Main_1", "Main_2", "Main_3", "Slicer_Date", "Slicer_Cat_1", "Slicer_Cat_2"}

# Slots allowed on both layers
_BOTH_LAYERS = {"KPI_Cards"}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _norm_page_type(raw: str) -> str:
    """Normalise short (T1) or full (T1_Strategic_Overview) page type string."""
    if raw in _VALID_PAGE_TYPES:
        return raw
    return _PAGE_TYPE_SHORT.get(raw, raw)


def _short_page_type(full: str) -> str:
    for short, long in _PAGE_TYPE_SHORT.items():
        if long == full:
            return short
    return full[:2] if len(full) >= 2 else full


def _load_yaml(path: Path) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ─── Individual DoD checks ────────────────────────────────────────────────────

CheckResult = Tuple[bool, str]  # (passed, message)


def check_dod_2_ux_layout(bracket: Dict) -> List[CheckResult]:
    """DoD 2: ux_layout_rules with page_1_summary and page_2_execution present."""
    results = []
    ux = bracket.get("ux_layout_rules") or {}
    if not ux:
        results.append((False, "ux_layout_rules is missing or empty"))
        return results
    if not ux.get("page_1_summary"):
        results.append((False, "ux_layout_rules.page_1_summary is missing"))
    else:
        results.append((True, "page_1_summary present"))
    if not ux.get("page_2_execution"):
        results.append((False, "ux_layout_rules.page_2_execution is missing"))
    else:
        results.append((True, "page_2_execution present"))
    return results


def check_dod_3_slot_page_types(bracket: Dict) -> List[CheckResult]:
    """DoD 3: Page types are valid (T1–T4) and declared for both pages."""
    results = []
    ux = bracket.get("ux_layout_rules") or {}
    for page_key, label in [("page_1_summary", "overview"), ("page_2_execution", "detail")]:
        page = ux.get(page_key) or {}
        raw_type = page.get("page_type", "")
        normed = _norm_page_type(raw_type)
        if normed in _VALID_PAGE_TYPES:
            results.append((True, f"{label}: page_type '{normed}' is valid"))
        elif raw_type:
            results.append((False, f"{label}: page_type '{raw_type}' is not a valid T1–T4 value"))
        else:
            results.append((False, f"{label}: page_type is missing"))
    return results


def check_dod_4_visual_governance(bracket: Dict) -> List[CheckResult]:
    """DoD 4: Activated slots use valid visual types (warn on disallowed)."""
    results = []
    ux = bracket.get("ux_layout_rules") or {}
    p1 = ux.get("page_1_summary") or {}
    c30 = p1.get("component_30s") or []
    _DISALLOWED_ABSTRACT = {"pie_chart", "donut_chart", "gauge", "radar_chart", "treemap"}
    for item in c30:
        if not isinstance(item, dict):
            continue
        vt = item.get("visual_type", "")
        if vt in _DISALLOWED_ABSTRACT:
            results.append((False, f"component_30s contains disallowed visual type: '{vt}'"))
        else:
            results.append((True, f"visual_type '{vt}' is not globally disallowed"))
    if not c30:
        results.append((True, "no component_30s to check (slot will use fallback)"))
    return results


def check_dod_5_layer_compliance(bracket: Dict) -> List[CheckResult]:
    """DoD 5: Overview page contains 3s/30s only; detail page contains 300s."""
    results = []
    ux = bracket.get("ux_layout_rules") or {}
    p1 = ux.get("page_1_summary") or {}
    p2 = ux.get("page_2_execution") or {}

    # Overview must have component_3s or component_30s (layer 3 or 30)
    has_3s = bool(p1.get("component_3s"))
    has_30s = bool(p1.get("component_30s"))
    if has_3s or has_30s:
        results.append((True, "overview page has 3s/30s layer content"))
    else:
        results.append((False, "overview page is missing component_3s and component_30s"))

    # Overview must NOT have component_300s
    if p1.get("component_300s"):
        results.append((False, "overview page (page_1_summary) should not contain component_300s"))

    # Detail must have component_300s
    has_300s = bool(p2.get("component_300s"))
    if has_300s:
        results.append((True, "detail page has 300s layer content"))
    else:
        results.append((False, "detail page (page_2_execution) is missing component_300s"))

    return results


def check_dod_6_slicer_rules(bracket: Dict) -> List[CheckResult]:
    """DoD 6: Slicer count ≤ 3 standard + optional 4th mode switch (from bracket config)."""
    results = []
    ux = bracket.get("ux_layout_rules") or {}
    p1 = ux.get("page_1_summary") or {}
    # Count declared categorical slicers from component keys (Slicer_Cat_1, _Cat_2 in 30s)
    c30 = p1.get("component_30s") or []
    slicer_count = sum(
        1 for item in (c30 if isinstance(c30, list) else [])
        if isinstance(item, dict) and "slicer" in str(item.get("visual_type", "")).lower()
    )
    # Slicer_Date is always present (+1), Slicer_Cat_1 and _Cat_2 are optional
    # We check declared categorical slots
    has_cat1 = bool(p1.get("slicer_cat_1") or any(
        isinstance(x, dict) and x.get("slot") == "Slicer_Cat_1" for x in c30
    ))
    has_cat2 = bool(p1.get("slicer_cat_2") or any(
        isinstance(x, dict) and x.get("slot") == "Slicer_Cat_2" for x in c30
    ))
    total = 1 + int(has_cat1) + int(has_cat2) + slicer_count  # Date + categoricals + additional
    if total <= 4:
        results.append((True, f"slicer count within limit (estimated ≤ {total})"))
    else:
        results.append((False, f"slicer count {total} exceeds limit of 4 (max 3 standard + 1 mode switch)"))
    return results


def check_dod_7_action_readiness(bracket: Dict) -> List[CheckResult]:
    """DoD 7: If action_panel enabled, page_type must be T4."""
    results = []
    ux = bracket.get("ux_layout_rules") or {}
    p2 = ux.get("page_2_execution") or {}
    c300 = p2.get("component_300s") or {}
    has_action_panel = bool(c300.get("action_panel")) if isinstance(c300, dict) else False

    if not has_action_panel:
        results.append((True, "action_panel not enabled — no T4 constraint"))
        return results

    raw_type = p2.get("page_type", "")
    normed = _norm_page_type(raw_type)
    if normed == "T4_Prescriptive_Recommendation":
        results.append((True, "action_panel enabled and page_type is T4 ✓"))
    else:
        results.append((False,
            f"action_panel is enabled but page_type is '{normed}' (must be T4_Prescriptive_Recommendation)"))

    # Action codes defined
    orch = bracket.get("orchestration") or {}
    ac_ids = orch.get("action_code_ids") or []
    if ac_ids:
        results.append((True, f"action_code_ids defined ({len(ac_ids)} codes)"))
    else:
        results.append((False, "action_panel enabled but orchestration.action_code_ids is empty"))

    return results


def check_dod_8_decision_clarity(bracket: Dict) -> List[CheckResult]:
    """DoD 8: decision_question field is non-empty."""
    results = []
    dq = bracket.get("decision_question") or ""
    if dq.strip():
        results.append((True, f"decision_question present ({len(dq)} chars)"))
    else:
        # Soft warning: field not yet in older brackets — warn, don't hard-fail
        results.append((None, "decision_question not set (add to UseCase_Bracket.yaml for full compliance)"))
    return results


def check_dod_9_decision_question_format(bracket: Dict) -> List[CheckResult]:
    """DoD 9: decision_question ≤ 120 chars, phrased as a question."""
    results = []
    dq = (bracket.get("decision_question") or "").strip()
    if not dq:
        return []  # already reported in DoD 8
    if len(dq) > 120:
        results.append((False, f"decision_question is {len(dq)} chars (max 120)"))
    else:
        results.append((True, f"decision_question length OK ({len(dq)} chars)"))
    if not dq.endswith("?"):
        results.append((None, "decision_question does not end with '?' — should be phrased as a business question"))
    else:
        results.append((True, "decision_question ends with '?'"))
    return results


def check_dod_10_big_idea(bracket: Dict) -> List[CheckResult]:
    """DoD 10: big_idea ≤ 300 chars, matches T1–T4 sentence template."""
    results = []
    bi = (bracket.get("big_idea") or "").strip()
    if not bi:
        results.append((None, "big_idea not set (add to UseCase_Bracket.yaml for full compliance)"))
        return results

    if len(bi) > 300:
        results.append((False, f"big_idea is {len(bi)} chars (max 300)"))
    else:
        results.append((True, f"big_idea length OK ({len(bi)} chars)"))

    # Determine page type for template check
    ux = bracket.get("ux_layout_rules") or {}
    p1 = ux.get("page_1_summary") or {}
    raw_type = p1.get("page_type", "")
    normed = _norm_page_type(raw_type)
    short = _short_page_type(normed)

    pattern = _BIG_IDEA_TEMPLATES.get(short)
    if pattern:
        if pattern.search(bi):
            results.append((True, f"big_idea matches {short} sentence template"))
        else:
            results.append((None,
                f"big_idea may not match the {short} template pattern — verify manually. "
                f"Value: '{bi[:80]}…'" if len(bi) > 80 else f"Value: '{bi}'"
            ))

    return results


def check_dod_11_primary_visual_annotation(bracket: Dict) -> List[CheckResult]:
    """DoD 11: Main_1 (primary visual) has at least one annotation, or annotation_waiver is set.

    Authority: Knaflic, Storytelling with Data (2015), p. 173.
    The check operates at the bracket YAML level:
      - If annotation_waiver: true is set in page_1_summary, the check passes with a note.
      - If a component_30s item targets Main_1 (explicitly or by position) and declares
        annotations, the check passes.
      - Otherwise a warning is emitted — the annotation must be verified in the actual
        visual (PBIP JSON) since it cannot be fully validated from YAML alone.
    """
    results = []
    ux = bracket.get("ux_layout_rules") or {}
    p1 = ux.get("page_1_summary") or {}

    # Waiver path
    if p1.get("annotation_waiver") is True:
        results.append((True, "annotation_waiver: true — DoD #11 waived for this use case"))
        return results

    c30 = p1.get("component_30s") or []
    if not c30:
        results.append((None,
            "DoD #11: no component_30s declared — cannot verify Main_1 annotation. "
            "Add annotations[] to the Main_1 component or set annotation_waiver: true if not applicable."
        ))
        return results

    # Identify the Main_1 component: explicit slot_id or first item (heuristic)
    main1 = None
    for item in c30:
        if isinstance(item, dict) and item.get("slot_id") == "Main_1":
            main1 = item
            break
    if main1 is None and c30 and isinstance(c30[0], dict):
        main1 = c30[0]  # first component_30s item is assigned Main_1 by the scaffold generator

    if main1 is None:
        results.append((None, "DoD #11: could not identify Main_1 component — verify annotation manually"))
        return results

    annotations = main1.get("annotations") or []
    if annotations:
        results.append((True,
            f"DoD #11: Main_1 has {len(annotations)} annotation(s) declared ✓"
        ))
    else:
        vt = main1.get("visual_type", "unknown")
        results.append((None,
            f"DoD #11: Main_1 ({vt}) has no annotations[] declared. "
            "Add at least one annotation marking the key finding (inflection, endpoint, "
            "threshold crossing), or set annotation_waiver: true if genuinely not applicable. "
            "Authority: Knaflic, Storytelling with Data (2015), p. 173."
        ))

    return results


# ─── Per-bracket runner ───────────────────────────────────────────────────────

CHECKS = [
    ("DoD 2 — Use case mapping",         check_dod_2_ux_layout),
    ("DoD 3 — Page type validity",       check_dod_3_slot_page_types),
    ("DoD 4 — Visual governance",        check_dod_4_visual_governance),
    ("DoD 5 — Layer compliance",         check_dod_5_layer_compliance),
    ("DoD 6 — Slicer rules",             check_dod_6_slicer_rules),
    ("DoD 7 — Action readiness",         check_dod_7_action_readiness),
    ("DoD 8 — Decision clarity",         check_dod_8_decision_clarity),
    ("DoD 9 — Decision question fmt",    check_dod_9_decision_question_format),
    ("DoD 10 — Big Idea",                check_dod_10_big_idea),
    ("DoD 11 — Primary visual annotation", check_dod_11_primary_visual_annotation),
]


def run_dod(bracket_path: Path) -> Tuple[int, int, int]:
    """Run all DoD checks for one UseCase_Bracket.yaml. Returns (passed, warned, failed)."""
    bracket = _load_yaml(bracket_path)
    use_case_id = bracket.get("id", bracket_path.parent.name)
    print(f"\n{'─' * 68}")
    print(f"  {use_case_id}  —  {bracket_path.relative_to(REPO)}")
    print(f"{'─' * 68}")

    passed = warned = failed = 0

    for check_name, check_fn in CHECKS:
        results = check_fn(bracket)
        for status, msg in results:
            if status is True:
                print(f"  ✓  {check_name}: {msg}")
                passed += 1
            elif status is False:
                print(f"  ✗  {check_name}: {msg}")
                failed += 1
            else:  # None = warning
                print(f"  ⚠  {check_name}: {msg}")
                warned += 1

    return passed, warned, failed


# ─── CLI entry point ──────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Page DoD validator for UseCase_Bracket.yaml files")
    parser.add_argument("use_case_id", nargs="?", help="Optional use case ID filter (e.g. FIN-001)")
    parser.add_argument("--exit-zero", action="store_true", help="Always exit 0 (warn mode for CI)")
    args = parser.parse_args()

    # Collect bracket files
    all_brackets = sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml"))
    if args.use_case_id:
        uid = args.use_case_id.upper()
        all_brackets = [b for b in all_brackets if uid in b.parts[-2].upper()]
        if not all_brackets:
            print(f"No UseCase_Bracket.yaml found matching '{args.use_case_id}'", file=sys.stderr)
            return 1 if not args.exit_zero else 0

    total_passed = total_warned = total_failed = 0

    for bracket_path in all_brackets:
        p, w, f = run_dod(bracket_path)
        total_passed += p
        total_warned += w
        total_failed += f

    print(f"\n{'═' * 68}")
    print(f"  DoD Summary: {total_passed} passed  /  {total_warned} warnings  /  {total_failed} failed")
    print(f"{'═' * 68}\n")

    if total_failed > 0:
        return 0 if args.exit_zero else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
