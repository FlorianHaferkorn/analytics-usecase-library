#!/usr/bin/env python3
"""
check_usecase_quality.py — narrative & grounding quality of use cases (the base for reports/stories).

Use cases are the source the report/story generators read, so their narrative quality is the
ceiling on the deliverable's quality. This validator enforces three quality bars the boutique
rubric leaves to prose:

1. **Every page states a decision.** Each populated page (page_1_summary / page_2_execution) must
   carry a non-empty `decision_question` — a 3-30-300 page exists to answer a decision, not to show
   charts (BC-NARR: decision-first).

2. **Every 30-second message is a conclusion, not a chart label** (BC-NARR-01). This rule is *owned*
   by `check_exhibit_message.py` (the declared BC-NARR-01 validator); we do not re-implement it — we
   **reuse its `classify_message`** so there is a single heuristic for the rule. A message the owner
   classifies as a bare label is reported here too, keeping this a complete use-case-quality gate
   without a second silo.

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
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: pyyaml not installed.", file=sys.stderr)
    sys.exit(1)

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:                 # so `python tooling/validation/check_usecase_quality.py` can import the owner
    sys.path.insert(0, str(REPO))

# BC-NARR-01 lives in one place — reuse the owner's classifier, never a parallel heuristic.
from tooling.validation.check_exhibit_message import classify_message  # noqa: E402

UC_GLOB = "core/usecases/**/UseCase_Bracket.yaml"


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
            status, _ = classify_message(c.get("message"))   # BC-NARR-01 owner's classifier
            if status is False:                               # reads as a bare label
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
