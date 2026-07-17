#!/usr/bin/env python3
"""
check_usecase_quality.py — narrative & grounding quality of use cases (the base for reports/stories).

Use cases are the source the report/story generators read, so their narrative quality is the
ceiling on the deliverable's quality. This validator enforces three quality bars the boutique
rubric leaves to prose:

1. **Every page states a decision.** Each populated page (page_1_summary / page_2_execution) must
   carry a non-empty `decision_question` — a 3-30-300 page exists to answer a decision, not to show
   charts (BC-NARR: decision-first).

2. **Every 30-second message is a conclusion, not a chart label.** A `component_30s.message` must
   assert a finding ("On-time delivery is dragging OTIF below target"), not describe the visual
   ("On-time delivery rate trend over time"). Label-style messages — ending in "over time",
   "trended", "vs. target", or a bare "… trend" — are rejected. The decomposition-orientation
   pattern ("A, B and C — the three components") is allowed (it carries an em dash and pairs with a
   so_what). This operationalises BC-NARR-01 (the message IS the conclusion).

3. **Every use case is standards-grounded.** Its `Business_Factsheet.md` must carry a
   "### 3.1 Standards basis" section (generated from the KPIs' `standard_ref`) and that section must
   reference the use case's strategic KPI — so the story rests on referenced external standards
   (SCOR/IFRS/ISO…), not re-invented definitions.

Usage:
    python tooling/validation/check_usecase_quality.py            # advisory report
    python tooling/validation/check_usecase_quality.py --strict   # any violation = exit 1

Exit codes: 0 advisory (default) or --strict clean; 1 --strict with ≥1 violation.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: pyyaml not installed.", file=sys.stderr)
    sys.exit(1)

REPO = Path(__file__).resolve().parents[2]
UC_GLOB = "core/usecases/**/UseCase_Bracket.yaml"

# Label-style tail patterns: a message that merely names the visual. Checked on the message with a
# trailing period stripped, lower-cased. The em-dash decomposition-orientation line is exempt.
_LABEL_TAILS = ("over time", "trended", "vs. target", "vs target", "trend", "trend vs. target")


def is_label_message(message: str | None) -> bool:
    """True when the message describes the chart instead of stating a conclusion."""
    if not message or not message.strip():
        return True
    s = message.strip().rstrip(".").lower()
    if " — " in message or " – " in message:   # decomposition-orientation line: allowed
        return False
    if "trend over time" in s:
        return True
    return any(s.endswith(t) for t in _LABEL_TAILS)


def _pages(bracket: dict[str, Any]) -> list[tuple[str, dict]]:
    ux = bracket.get("ux_layout_rules", {}) or {}
    return [(k, ux.get(k)) for k in ("page_1_summary", "page_2_execution")
            if isinstance(ux.get(k), dict) and ux.get(k)]


def check_bracket(path: Path) -> list[str]:
    d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    ucid = d.get("id", path.parent.name)
    problems: list[str] = []

    for pk, page in _pages(d):
        if not (page.get("decision_question") or "").strip():
            problems.append(f"{ucid}/{pk}: missing decision_question")
        for c in (page.get("component_30s") or []):
            if is_label_message(c.get("message")):
                problems.append(
                    f"{ucid}/{pk}: label-style message (needs a conclusion): "
                    f"{c.get('message')!r}")

    # standards grounding in the factsheet
    fs = path.parent / "Business_Factsheet.md"
    strategic = (d.get("orchestration", {}) or {}).get("strategic_kpi_id")
    if fs.exists():
        text = fs.read_text(encoding="utf-8")
        if "### 3.1 Standards basis" not in text:
            problems.append(f"{ucid}: factsheet missing '### 3.1 Standards basis' section")
        elif strategic and strategic not in text:
            problems.append(
                f"{ucid}: Standards basis does not reference the strategic KPI '{strategic}'")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="Use-case narrative & standards-grounding quality")
    ap.add_argument("use_case_id", nargs="?", help="filter by ID substring")
    ap.add_argument("--strict", action="store_true", help="any violation = exit 1")
    args = ap.parse_args()

    brackets = sorted(REPO.glob(UC_GLOB))
    if args.use_case_id:
        brackets = [b for b in brackets if args.use_case_id.lower() in str(b).lower()]

    total = 0
    for b in brackets:
        for p in check_bracket(b):
            print(f"  ⚠ {p}")
            total += 1

    print(f"\ncheck_usecase_quality: {len(brackets)} use cases · {total} violation(s).")
    if args.strict and total:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
