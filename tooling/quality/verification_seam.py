"""verification_seam.py — the ONE honesty contract shared by every quality-scoring seam.

Two subsystems score quality behind a pluggable seam so a bounded LLM can slot in later:
  • `tooling/storyline/score_insights.py` (`Scorer`/`DeterministicScorer`) — scores a candidate
    *finding* (one visual) to rank it and pick a page headline (generation-side).
  • `tooling/report_quality/judge.py` (`Judge`/`SpecHeuristicJudge`/`LLMJudge`) — scores a rubric
    *rule* over the spec/render to gate craft quality (QA-side).

They score DIFFERENT objects, so their score types (`InsightScore` vs `Verdict`) and method names
(`score` vs `evaluate`) stay distinct **by design** — collapsing them into one type would be a leaky
abstraction. What they MUST share — and what lives here as the single source of truth instead of being
re-stated in each docstring — is the honesty contract every such seam obeys:

  1. **Deterministic default.** A deterministic implementation must exist and ship; no seam depends on
     an LLM to function at all.
  2. **Abstain, never fabricate.** An LLM backend MAY slot in for the judgment dimensions, but when it
     cannot decide it MUST return `ABSTAIN` (None) rather than invent a verdict/score.
  3. **The gate stays deterministic.** The verification/grounding dimension — the one that decides
     whether a claim may be asserted at all — stays deterministic regardless of any LLM
     (ADR-0009 "UNCOMPUTED, never asserted"; ADR-0017 grounding gate). The LLM never moves the gate.

Both modules import `ABSTAIN` from here and cite this contract, so the rule has exactly one definition.
"""
from __future__ import annotations

from typing import Any

# The shared sentinel: "not decided — never fabricate." Both seams use None on the wire; naming it
# here makes the intent (abstention, not a zero score) explicit and single-sourced.
ABSTAIN: None = None


def is_abstain(score: Any) -> bool:
    """True when a seam abstained (score is ABSTAIN/None) — the never-fabricate path.

    Note the deliberate asymmetry: a real score of 0.0 is a *decision* ("fails the rule" /
    "no grounding"), NOT an abstention. Only None means undecided.
    """
    return score is None
