#!/usr/bin/env python3
"""
boutique_scorecard.py — Boutique-Craft rubric scorecard (K6 §9)

Operationalises the Boutique-Craft rubric (KONZEPT §9): it runs every *wired*
structural validator, maps each result onto the rubric's weighted dimensions, and
reports the achieved score, knock-out status, and — honestly — how much of the rubric
is auto-scorable today. The remaining rules are `check: judge` (LLM/human over a
render) or not-yet-wired; they are reported as `not_scored`, never silently passed.

Rubric formula (tokens/boutique_craft_rubric.yaml): each rule scores 0.0/0.5/1.0;
dimension_score = weighted mean of its rule scores; total = Σ(dimension_score ×
dimension.weight). A report PASSES iff total ≥ pass_score_pct AND 0 knock-out
violations. This scorecard computes that over the SCORED subset and states coverage.

Wiring (rule_id → validator invocation, exit 0 = pass):
    BC-NARR-01  → check_exhibit_message.py   (title is a statement, not a label)
    BC-CHART-01 → check_mixed_scale.py       (no mixed scale on one axis) [knock-out]
    BC-NARR-04  → check_kpi_context.py --strict (hero KPI carries context)
    BC-CHART-10 → check_evidence_sort.py --strict (evidence worst-first + Top-N) [knock-out]
    BC-BRAND-01 → check_custom_theme.py --strict (composed custom theme)          [knock-out]
    BC-CHART-08 → check_forbidden_charts.py --strict (no pie/donut/gauge/treemap)

Usage:
    python tooling/report_quality/boutique_scorecard.py            # print scorecard
    python tooling/report_quality/boutique_scorecard.py --json out.json
    python tooling/report_quality/boutique_scorecard.py --strict   # exit 1 if a scored knock-out fails

Exit codes:
    0 — no scored knock-out failed (advisory), unless --strict and a scored knock-out failed
    1 — --strict and ≥1 scored knock-out violation
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    if __name__ == "__main__":
        print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    raise

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:          # allow `python tooling/report_quality/boutique_scorecard.py`
    sys.path.insert(0, str(REPO))
_RUBRIC = REPO / "core/templates/page_templates/tokens/boutique_craft_rubric.yaml"
_VALID = REPO / "tooling/validation"

def wired(rubric: Optional[dict[str, Any]] = None) -> dict[str, tuple[str, list[str]]]:
    """rule_id → (script, extra args), **gelesen aus der Rubrik**. Exit 0 == bestanden.

    Bis zum 03.08.2026 stand diese Tabelle hier als Literal — und damit die Bindung
    „welcher Checker entscheidet diese Regel" an einem anderen Ort als die Regel selbst.
    Gemessen an dem Tag: die Rubrik deklarierte 20 Regeln als `check: structural`, die
    Tabelle kannte 13. Die Differenz war nirgends sichtbar; sie sah aus wie ein
    Inhaltsproblem („die Rubrik ist eben noch nicht fertig") und war eine Drift zwischen
    zwei Listen. Dieselbe Klasse wie die Rasterkopie im Compiler (§13) und die zwei
    Pflichtslot-Mengen in `RequiredSlots` (§12): zwei Stellen mit einer Meinung ueber
    dieselbe Sache.

    Jetzt traegt jede Regel ihre Bindung selbst (`validator: {script, args}`), und diese
    Funktion liest sie. Eine neue Verdrahtung ist damit eine Zeile in der Rubrik, keine
    zweite Pflege — und eine Regel, die `structural` behauptet, ohne einen Validator zu
    nennen, ist maschinell auffindbar statt bloss unauffaellig.
    """
    rubric = rubric or load_rubric()
    out: dict[str, tuple[str, list[str]]] = {}
    for dim in rubric.get("dimensions") or []:
        for r in dim.get("rules") or []:
            v = r.get("validator")
            if not v:
                continue
            if not v.get("script"):
                raise ValueError(f"{r['id']}: `validator` ohne `script` — eine leere "
                                 f"Bindung saehe aus wie 'nicht verdrahtet' und waere "
                                 f"doch eine Zusage.")
            out[str(r["id"])] = (str(v["script"]), list(v.get("args") or []))
    return out


def _run_validator(script: str, args: list[str]) -> bool:
    """True iff the validator exits 0 (rule passes)."""
    proc = subprocess.run(
        [sys.executable, str(_VALID / script), *args],
        capture_output=True, text=True, cwd=str(REPO),
        encoding="utf-8", errors="replace")
    return proc.returncode == 0


def load_rubric() -> dict[str, Any]:
    return yaml.safe_load(_RUBRIC.read_text(encoding="utf-8"))


def score(run_validator=_run_validator, rubric: Optional[dict] = None,
          judge: Optional[Any] = None) -> dict[str, Any]:
    """Compute the scorecard. `run_validator` is injectable for testing.

    `judge` (a report_quality.judge.Judge) optionally scores the `check: judge` rules;
    verdicts that abstain (score=None) stay not_scored. Default None → structural only.

    Returns a dict with per-rule scores, dimension rollups, coverage, knock-out
    status, and the achieved score over the scored subset.
    """
    rubric = rubric or load_rubric()
    pass_pct = rubric["scoring"]["pass_score_pct"]
    WIRED = wired(rubric)

    verdicts = {}
    if judge is not None:
        from tooling.report_quality.judge import JudgeContext, run_judges  # noqa: PLC0415
        verdicts = run_judges(rubric, JudgeContext(), judge)

    # global_weight per rule normalises all rules to sum 100 (rule.weight within its
    # dimension × dimension.weight), matching the rubric's dimension-weighted formula.
    rules_out: list[dict[str, Any]] = []
    knockouts: list[dict[str, Any]] = []
    achieved = scored_possible = 0.0

    for dim in rubric["dimensions"]:
        dim_rule_weight = sum(r["weight"] for r in dim["rules"]) or 1
        for r in dim["rules"]:
            gweight = r["weight"] / dim_rule_weight * dim["weight"]
            rid = r["id"]
            entry = {"id": rid, "dimension": dim["id"], "severity": r["severity"],
                     "global_weight": round(gweight, 3), "status": "not_scored",
                     "score": None, "method": None}
            if rid in WIRED:
                passed = run_validator(*WIRED[rid])
                punkt = 1.0 if passed else 0.0
                methode = "structural"
                # `check: both` — der Validator deckt die strukturelle Haelfte, ein Judge
                # die semantische. Konservativ das Minimum: eine Regel gilt nicht als
                # erfuellt, weil eine ihrer beiden Haelften geprueft wurde. Vorher gewann
                # der Validator immer und das Judge-Urteil wurde still verworfen.
                if r.get("check") == "both" and (v := verdicts.get(rid)) and v.score is not None:
                    punkt = min(punkt, v.score)
                    methode = f"structural+{v.method}"
                entry["score"] = punkt
                entry["status"] = ("pass" if punkt >= 1.0
                                   else "partial" if punkt > 0 else "fail")
                entry["method"] = methode
                achieved += punkt * gweight
                scored_possible += gweight
            elif rid in verdicts and verdicts[rid].score is not None:
                v = verdicts[rid]
                entry["score"] = v.score
                entry["status"] = "pass" if v.score >= 1.0 else ("partial" if v.score > 0 else "fail")
                entry["method"] = v.method
                achieved += v.score * gweight
                scored_possible += gweight
            if r["severity"] == "knock_out":
                knockouts.append({"id": rid, "status": entry["status"], "score": entry["score"]})
            rules_out.append(entry)

    scored_knockouts = [k for k in knockouts if k["score"] is not None]
    failed_knockouts = [k for k in scored_knockouts if k["score"] == 0.0]
    structural_pct = (achieved / scored_possible * 100) if scored_possible else 0.0

    return {
        "rubric_version": rubric.get("rubric_version"),
        "pass_score_pct": pass_pct,
        "coverage_pct": round(scored_possible, 1),          # % of the 100-pt rubric auto-scored
        "structural_score_pct": round(structural_pct, 1),   # achieved / scored (of scored subset)
        "scored_rules": sum(1 for r in rules_out if r["score"] is not None),
        "total_rules": len(rules_out),
        "knockouts_total": len(knockouts),
        "knockouts_scored": len(scored_knockouts),
        "knockouts_failed": [k["id"] for k in failed_knockouts],
        "certifiable": scored_possible >= 100 and structural_pct >= pass_pct and not failed_knockouts,
        "rules": rules_out,
    }


def _print(card: dict[str, Any]) -> None:
    print("\n── Boutique-Craft Scorecard (rubric "
          f"{card['rubric_version']}) ─────────────────────")
    print(f"  Auto-scored:    {card['scored_rules']}/{card['total_rules']} rules "
          f"= {card['coverage_pct']}/100 pts of the rubric (rest: judge / not-yet-wired)")
    print(f"  Structural score: {card['structural_score_pct']}% of the scored subset "
          f"(pass bar {card['pass_score_pct']}%)")
    print(f"  Knock-outs:     {card['knockouts_scored']}/{card['knockouts_total']} scored; "
          f"failed: {card['knockouts_failed'] or 'none'}")
    for r in card["rules"]:
        if r["score"] is not None:
            mark = "✓" if r["score"] == 1.0 else ("~" if r["score"] > 0 else "✗")
            ko = " [knock-out]" if r["severity"] == "knock_out" else ""
            via = f" ({r['method']})" if r.get("method") and r["method"] != "structural" else ""
            print(f"    {mark} {r['id']:14} ({r['dimension']}){ko}{via}")
    if card["certifiable"]:
        print("  → PASS (full rubric certifiable).")
    else:
        print("  → Not yet fully certifiable — coverage < 100 pts (judge rules pending, K6/M6).")


def main() -> int:
    parser = argparse.ArgumentParser(description="Boutique-Craft rubric scorecard")
    parser.add_argument("--json", metavar="PATH", help="Write the scorecard as JSON")
    parser.add_argument("--strict", action="store_true", help="Exit 1 if a scored knock-out fails")
    parser.add_argument("--render-evidence", metavar="DIR", help=(
        "Directory of rendered evidence; if set (and ANTHROPIC_MODEL/_API_KEY are "
        "present) the render-only judge rules are scored by the LLM backend. Without "
        "credentials the composite still only scores the spec-heuristic rules."))
    args = parser.parse_args()

    if args.render_evidence:
        from tooling.report_quality.llm_backend import build_composite_judge  # noqa: PLC0415
        judge = build_composite_judge(args.render_evidence)
    else:
        from tooling.report_quality.judge import SpecHeuristicJudge  # noqa: PLC0415
        judge = SpecHeuristicJudge()
    card = score(judge=judge)
    _print(card)
    if args.json:
        Path(args.json).write_text(json.dumps(card, indent=2), encoding="utf-8", newline="\n")
        print(f"  (written: {args.json})")
    if args.strict and card["knockouts_failed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
