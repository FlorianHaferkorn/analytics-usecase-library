"""llm_backend.py — concrete Anthropic backend for the LLM-judge seam (K6 §9).

Wires the pluggable `LLMJudge` (in `judge.py`) to a real model, so the render-only
boutique rules (BC-COLOR-01, BC-CHART-03/06, BC-NARR-05, …) can be scored over rendered
evidence instead of abstaining. Two pieces plug into `LLMJudge`:

  * `make_complete()`  -> `complete(prompt) -> str`  — an Anthropic-backed completion fn
  * `dir_render_provider(evidence_dir)` -> `render(rule_id) -> evidence`  — reads the
    rendered evidence the runbook's render step dropped on disk (per-rule file, else a
    shared report evidence file).

Design contract (honesty + opt-in, mirrors the rest of the tool infra):
  * The model id is **never hard-coded** — it is read from the `ANTHROPIC_MODEL` env var,
    so this pushed source stays model-agnostic. Set it in the shell before running.
  * Graceful-skip: with no `anthropic` SDK, no `ANTHROPIC_API_KEY`, or no `ANTHROPIC_MODEL`,
    `make_complete()` returns `None` and the `LLMJudge` abstains — it never fabricates a
    verdict. So importing/using this module without credentials changes no score.

Turnkey wiring (one call), used by the runbook:

    from tooling.report_quality.judge import CompositeJudge, SpecHeuristicJudge
    from tooling.report_quality.llm_backend import build_llm_judge
    from tooling.report_quality.boutique_scorecard import score

    judge = CompositeJudge([SpecHeuristicJudge(), build_llm_judge("build/render_evidence")])
    card = score(judge=judge)
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable, Optional

try:  # package context (pytest / -m) …
    from tooling.report_quality.judge import (
        CompositeJudge, LLMJudge, SpecHeuristicJudge,
    )
except ImportError:  # … or run from inside the package dir
    from judge import CompositeJudge, LLMJudge, SpecHeuristicJudge  # type: ignore


# Filenames the render step may drop per rule, tried in order; the last few are a shared
# report-level evidence file reused for every render-only rule.
_EVIDENCE_NAMES = ("{rid}.txt", "{rid}.md", "_report.txt", "_report.md", "_report.html")


def make_complete() -> Optional[Callable[[str], str]]:
    """Build an Anthropic-backed `complete(prompt)->str`, or `None` if not wired.

    Returns `None` (→ judge abstains) when the SDK is absent, `ANTHROPIC_API_KEY` is
    unset, or `ANTHROPIC_MODEL` is unset — so callers never need a key to import this.
    """
    model = os.environ.get("ANTHROPIC_MODEL")
    if not model or not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None

    client = anthropic.Anthropic()
    max_tokens = int(os.environ.get("ANTHROPIC_MAX_TOKENS", "2048"))

    def complete(prompt: str) -> str:
        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            getattr(b, "text", "") for b in msg.content
            if getattr(b, "type", None) == "text"
        )

    return complete


def dir_render_provider(evidence_dir: str | os.PathLike) -> Callable[[str], Optional[str]]:
    """`render(rule_id) -> evidence` reading rendered evidence from `evidence_dir`.

    Looks for a per-rule file first (`BC-COLOR-01.txt` …), then a shared report file
    (`_report.html` …). Missing evidence → `None`, so the `LLMJudge` abstains for that
    rule rather than judging on nothing.
    """
    base = Path(evidence_dir)

    def render(rule_id: str) -> Optional[str]:
        for pattern in _EVIDENCE_NAMES:
            p = base / pattern.format(rid=rule_id)
            if p.exists():
                text = p.read_text(encoding="utf-8").strip()
                if text:
                    return text
        # Fallback: no per-rule / _report file, so use every rendered *.html in the dir
        # as one suite-wide evidence blob. <script> is stripped (behaviour, not design
        # signal); CSS is kept (colour matters).
        htmls = sorted(base.glob("*.html"))
        if htmls:
            parts = []
            for h in htmls:
                body = re.sub(r"<script\b.*?</script>", "", h.read_text(encoding="utf-8"), flags=re.S)
                parts.append(f"<!-- {h.name} -->\n{body.strip()}")
            blob = "\n\n".join(parts).strip()
            if blob:
                return blob
        return None

    return render


def build_llm_judge(evidence_dir: str | os.PathLike, rubric: Optional[dict] = None) -> LLMJudge:
    """Assemble an `LLMJudge` from the env-configured model + on-disk render evidence."""
    return LLMJudge(complete=make_complete(),
                    render_provider=dir_render_provider(evidence_dir),
                    rubric=rubric)


def build_composite_judge(evidence_dir: str | os.PathLike, rubric: Optional[dict] = None) -> CompositeJudge:
    """Spec-heuristic first (cheap/deterministic), LLM only for what it can't decide."""
    return CompositeJudge([SpecHeuristicJudge(), build_llm_judge(evidence_dir, rubric)])
