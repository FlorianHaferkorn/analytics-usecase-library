#!/usr/bin/env python3
"""
judge.py — Boutique-Craft judge harness (K6 §9, the `check: judge` half)

The rubric splits into `check: structural` (machine-checkable from the spec/PBIR — wired
via boutique_scorecard.WIRED) and `check: judge` (needs assessment of a *rendered*
report). This harness is the addressable home for the judge rules. Its key move: a few
rules the rubric conservatively marked `judge` are in fact **decidable from the governed
spec without a render** — those get a deterministic heuristic here and count honestly; the
genuinely render-only rules get a pluggable LLM/human backend and, until that runs,
**abstain** (score=None) rather than fake a verdict.

Architecture:
    Judge (Protocol)          — evaluate(rule_id, ctx) -> Verdict
    SpecHeuristicJudge        — deterministic; scores the spec-decidable judge rules,
                                abstains on render-only rules (never invents a score)
    <LLM judge>               — future backend over a render + screenshot (opt-in;
                                needs a renderer + model, a maintainer/runtime concern)

A Verdict with score=None (abstain) leaves the rule `not_scored` in the scorecard — the
same honesty rule as the structural side: coverage only counts what was actually decided.

Usage (library): run_judges(load_rubric(), ctx, SpecHeuristicJudge())
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, Protocol

try:
    import yaml
except ImportError:  # pragma: no cover
    raise

REPO = Path(__file__).resolve().parents[2]
_RUBRIC = REPO / "core/templates/page_templates/tokens/boutique_craft_rubric.yaml"


@dataclass
class Verdict:
    rule_id: str
    score: Optional[float]   # 0.0 / 0.5 / 1.0, or None = abstain (not decided)
    method: str              # "spec_heuristic" | "llm" | "abstain"
    rationale: str


class Judge(Protocol):
    def evaluate(self, rule_id: str, ctx: "JudgeContext") -> Verdict: ...


@dataclass
class JudgeContext:
    """Everything a judge may read. Deterministic heuristics read the governed spec;
    a future LLM judge would additionally carry render/screenshot handles."""
    repo: Path = REPO

    def brackets(self) -> list[dict[str, Any]]:
        out = []
        for p in sorted(self.repo.glob("core/usecases/**/UseCase_Bracket.yaml")):
            out.append(yaml.safe_load(p.read_text(encoding="utf-8")) or {})
        return out

    def exhibits(self) -> list[dict[str, Any]]:
        """All component_30s exhibits across brackets (the 30-second evidence layer)."""
        out = []
        for b in self.brackets():
            page = (b.get("ux_layout_rules", {}) or {}).get("page_1_summary", {}) or {}
            for ex in page.get("component_30s") or []:
                if isinstance(ex, dict):
                    out.append({**ex, "_bracket": b.get("id", "?")})
        return out


def judge_rules(rubric: dict[str, Any]) -> list[dict[str, Any]]:
    """All `check: judge` rules from the rubric, flattened with their dimension."""
    out = []
    for dim in rubric["dimensions"]:
        for r in dim["rules"]:
            if r.get("check") == "judge":
                out.append({**r, "dimension": dim["id"]})
    return out


def load_rubric() -> dict[str, Any]:
    return yaml.safe_load(_RUBRIC.read_text(encoding="utf-8"))


# ── Deterministic spec-heuristics for the spec-decidable judge rules ─────────

def _bc_narr_03(ctx: JudgeContext) -> Verdict:
    """So-what chain: signal → reason → implication → action. Spec-decidable: every
    exhibit that states a `message` (signal/conclusion) must also carry a `so_what`
    (implication); the action leg is the governed `action_code_id`. An exhibit with a
    message but no so_what has a broken chain."""
    exhibits = [e for e in ctx.exhibits() if str(e.get("message", "")).strip()]
    if not exhibits:
        return Verdict("BC-NARR-03", None, "abstain", "no governed messages to assess")
    broken = [f"{e['_bracket']}/{e.get('slot_id', '?')}"
              for e in exhibits if not str(e.get("so_what", "")).strip()]
    if broken:
        return Verdict("BC-NARR-03", 0.0, "spec_heuristic",
                       f"{len(broken)} exhibit(s) state a message without a so-what: {broken[:5]}")
    return Verdict("BC-NARR-03", 1.0, "spec_heuristic",
                   f"all {len(exhibits)} message-bearing exhibits carry a so-what chain")


_HEURISTICS: dict[str, Callable[[JudgeContext], Verdict]] = {
    "BC-NARR-03": _bc_narr_03,
}


class SpecHeuristicJudge:
    """Scores judge rules that are decidable from the governed spec; abstains on the
    render-only ones (never invents a verdict)."""

    def evaluate(self, rule_id: str, ctx: JudgeContext) -> Verdict:
        fn = _HEURISTICS.get(rule_id)
        if fn is None:
            return Verdict(rule_id, None, "abstain", "needs a rendered report + judge (LLM/human)")
        return fn(ctx)


def run_judges(rubric: dict[str, Any], ctx: JudgeContext, judge: Judge) -> dict[str, Verdict]:
    """Evaluate every judge rule with `judge`. Abstentions (score=None) stay not_scored."""
    return {r["id"]: judge.evaluate(r["id"], ctx) for r in judge_rules(rubric)}
