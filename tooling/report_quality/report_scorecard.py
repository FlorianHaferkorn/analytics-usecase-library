"""IBCS-pattern report scorecard: weighted points + knock-outs (R3.3).

Two independent mechanisms, combined per report:
  - Weighted points: every Tier 0 Violation (structural/content/dax-reference)
    deducts points by severity; score = max(0, 100 - deductions).
  - Knock-outs: Mixed-Scale (percent measures mixed with amount measures on
    one chart axis) and Unsorted Evidence (an evidence table with no default
    sort) fail the report regardless of point score -- IBCS "instant red".

A report PASSes when score >= THRESHOLD_PCT AND there are zero knock-outs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import authoring_metadata
from .content_validator import validate_report_content
from .dax_reference_validator import validate_report_measure_references
from .models import Severity, Violation
from .pbir import ParsedReport, iter_report_dirs, parse_report, visual_pointer
from .structural_validator import check_report

THRESHOLD_PCT = 70
MAX_SCORE = 100
POINT_WEIGHTS: dict[Severity, int] = {"critical": 15, "warning": 5, "info": 1}

KNOCKOUT_MIXED_SCALE = "scorecard:knockout-mixed-scale"
KNOCKOUT_UNSORTED_EVIDENCE = "scorecard:knockout-unsorted-evidence"
KNOCKOUT_CHECKS = {KNOCKOUT_MIXED_SCALE, KNOCKOUT_UNSORTED_EVIDENCE}

EVIDENCE_VISUAL_TYPES = {"tableEx", "matrix", "pivotTable"}

# Reports whose current PBIR content is verified (R1.x pilot) enough that a
# failing score/knock-out should actually fail CI. Everything else is scored
# and printed for visibility (DoD: "Score je Report im CI-Log") but does not
# gate the build yet -- 17/17 is R5.1's job (generator rollout), not R3.3's.
DEFAULT_ENFORCED_REPORTS = ["COM-002"]

_MEASURE_BLOCK_RE = re.compile(r"measure\s+'([^']+)'\s*=[^\r\n]*\r?\n(?P<body>(?:[ \t]+\S.*\r?\n?)*)")
_FORMAT_STRING_RE = re.compile(r'formatString:\s*"([^"]*)"')


def parse_measure_format_strings(dist_root: Path) -> dict[str, str]:
    """Map measure name -> formatString, parsed from every domain's _Measures.tmdl."""

    formats: dict[str, str] = {}
    model_root = dist_root.parent if dist_root.name.endswith(".Report") and dist_root.is_dir() else dist_root
    for tmdl in sorted(model_root.glob("*.SemanticModel/definition/tables/_Measures.tmdl")):
        text = tmdl.read_text(encoding="utf-8", errors="replace")
        for match in _MEASURE_BLOCK_RE.finditer(text):
            name = match.group(1).strip()
            fmt_match = _FORMAT_STRING_RE.search(match.group("body"))
            if fmt_match:
                formats.setdefault(name, fmt_match.group(1))
    return formats


def scale_family(format_string: str | None) -> str:
    """Coarse scale classification: 'percent' vs 'amount' vs 'unknown'."""

    if not format_string:
        return "unknown"
    return "percent" if "%" in format_string else "amount"


#  "Y"/"Y2" are the only role names across the authoring-metadata snapshot that
# represent a genuinely shared, rendered numeric axis (every chart type --
# bar/column/line/area/waterfall/scatter/map/gauge/donut/pie/funnel/ribbon --
# uses exactly these names). Card/table/matrix "Values"/"Data" roles show each
# measure independently (own tile/column) and are deliberately excluded --
# mixing units there is normal, not the IBCS mixed-scale antipattern.
_SHARED_AXIS_ROLE_NAMES = {"Y", "Y2"}


def _value_role_names(visual_type: str) -> set[str]:
    """Role names on visual_type that carry measures on a shared, rendered scale axis."""

    role_kinds = authoring_metadata.roles(visual_type)
    return {
        role
        for role, kind in role_kinds.items()
        if role in _SHARED_AXIS_ROLE_NAMES and kind in ("Measure", "GroupingOrMeasure")
    }


def detect_mixed_scale(report: ParsedReport, measure_formats: dict[str, str]) -> list[Violation]:
    """Knock-out: two-plus measures with differing scale families on one axis role."""

    violations: list[Violation] = []
    for page in report.pages.values():
        for visual_name, visual in page.visuals.items():
            visual_root = visual.get("visual", {})
            visual_type = visual_root.get("visualType")
            if not visual_type:
                continue
            value_roles = _value_role_names(visual_type)
            if not value_roles:
                continue
            query_state = (visual_root.get("query", {}) or {}).get("queryState", {}) or {}
            for role_name in value_roles:
                role = query_state.get(role_name)
                if not isinstance(role, dict):
                    continue
                measure_names = []
                for projection in role.get("projections", []) or []:
                    measure = (projection.get("field") or {}).get("Measure")
                    if isinstance(measure, dict) and isinstance(measure.get("Property"), str):
                        measure_names.append(measure["Property"])
                if len(measure_names) < 2:
                    continue
                families = {scale_family(measure_formats.get(name)) for name in measure_names}
                families.discard("unknown")
                if len(families) > 1:
                    violations.append(
                        Violation(
                            KNOCKOUT_MIXED_SCALE,
                            "critical",
                            visual_pointer(
                                report.report_dir, page, visual_name, f"visual/query/queryState/{role_name}"
                            ),
                            f"Mixed scale families on role '{role_name}': {sorted(families)}",
                            expected="single scale family per axis",
                            actual={"measures": measure_names, "families": sorted(families)},
                        )
                    )
    return violations


def detect_unsorted_evidence(report: ParsedReport) -> list[Violation]:
    """Knock-out: an evidence table (tableEx/matrix/pivotTable) with no default sort."""

    violations: list[Violation] = []
    for page in report.pages.values():
        for visual_name, visual in page.visuals.items():
            visual_root = visual.get("visual", {})
            if visual_root.get("visualType") not in EVIDENCE_VISUAL_TYPES:
                continue
            sort_def = (visual_root.get("query", {}) or {}).get("sortDefinition") or {}
            sort_list = sort_def.get("sort") or []
            if not sort_list or not sort_def.get("isDefaultSort"):
                violations.append(
                    Violation(
                        KNOCKOUT_UNSORTED_EVIDENCE,
                        "critical",
                        visual_pointer(report.report_dir, page, visual_name, "visual/query/sortDefinition"),
                        "Evidence table has no default sort (query.sortDefinition.sort + isDefaultSort)",
                        expected="non-empty sort with isDefaultSort=true",
                        actual=sort_def or None,
                    )
                )
    return violations


def score_from_violations(violations: list[Violation]) -> int:
    """Pure weighted-point scoring. No filesystem access -- unit-testable in isolation."""

    deductions = sum(POINT_WEIGHTS.get(v.severity, 0) for v in violations if v.check not in KNOCKOUT_CHECKS)
    return max(0, MAX_SCORE - deductions)


def passes(score: int, knockouts: list[Violation]) -> bool:
    return score >= THRESHOLD_PCT and not knockouts


@dataclass
class ScorecardResult:
    report_name: str
    score: int
    passed: bool
    knockouts: list[Violation] = field(default_factory=list)
    point_violations: list[Violation] = field(default_factory=list)


def compute_scorecard(report_dir: Path, measure_formats: dict[str, str]) -> ScorecardResult:
    report = parse_report(report_dir)

    point_violations: list[Violation] = []
    point_violations.extend(check_report(report_dir))
    point_violations.extend(validate_report_content(report_dir))
    point_violations.extend(validate_report_measure_references(report_dir))

    knockouts: list[Violation] = []
    knockouts.extend(detect_mixed_scale(report, measure_formats))
    knockouts.extend(detect_unsorted_evidence(report))

    score = score_from_violations(point_violations)
    return ScorecardResult(
        report_name=report_dir.name,
        score=score,
        passed=passes(score, knockouts),
        knockouts=knockouts,
        point_violations=point_violations,
    )


def _result_to_dict(result: ScorecardResult) -> dict:
    return {
        "report": result.report_name,
        "score": result.score,
        "threshold": THRESHOLD_PCT,
        "passed": result.passed,
        "knockouts": [k.__dict__ for k in result.knockouts],
        "point_violation_count": len(result.point_violations),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dist-root", default="products/fabric/powerbi/dist")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    parser.add_argument(
        "--enforce",
        nargs="*",
        default=DEFAULT_ENFORCED_REPORTS,
        metavar="SUBSTRING",
        help="Report-name substrings that fail the gate (exit 1) on FAIL. "
        "Other reports are scored/printed but do not fail the build (pending R5.1 rollout).",
    )
    parser.add_argument("--write-results", metavar="PATH", help="Write JSON results to this path.")
    args = parser.parse_args(argv)

    dist_root = Path(args.dist_root)
    if not dist_root.exists():
        print(f"Dist root not found: {dist_root}", file=sys.stderr)
        return 2

    report_dirs = iter_report_dirs(dist_root)
    if not report_dirs:
        print(f"No .Report directories found under: {dist_root}", file=sys.stderr)
        return 2

    measure_formats = parse_measure_format_strings(dist_root)
    results = [compute_scorecard(report_dir, measure_formats) for report_dir in report_dirs]

    if args.json:
        print(json.dumps([_result_to_dict(r) for r in results], indent=2, ensure_ascii=False))
    else:
        for result in results:
            status = "PASS" if result.passed else "FAIL"
            print(f"{status} {result.report_name}: {result.score}% (threshold {THRESHOLD_PCT}%), {len(result.knockouts)} knock-out(s)")
            for k in result.knockouts:
                print(f"    KNOCKOUT {k}")

    if args.write_results:
        results_path = Path(args.write_results)
        results_path.parent.mkdir(parents=True, exist_ok=True)
        results_path.write_text(
            json.dumps([_result_to_dict(r) for r in results], indent=2, ensure_ascii=False), encoding="utf-8"
        )

    enforced_fail = False
    for result in results:
        if not result.passed and any(token in result.report_name for token in args.enforce):
            enforced_fail = True
            if not args.json:
                print(f"GATE-FAIL {result.report_name} is enforced and did not pass.")

    return 1 if enforced_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
