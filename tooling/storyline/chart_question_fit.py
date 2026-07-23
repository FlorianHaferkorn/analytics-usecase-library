"""chart_question_fit.py — does the chosen visual type generically fit the question it answers?

In classic BI (Power BI) a visual is static and general-purpose: it cannot be tuned per question the
way a React/HTML or Databricks AI/BI chart can. So the minimum bar is that the visual type can
*generically* answer its `question` — e.g. "has X declined over 12 months?" needs a time series, not a
single card; "where does X concentrate?" needs a ranked/broken-down visual, not a bare trend line.
This catches the case where the chart simply cannot address its own question, before a report is built.

Deliberately conservative: it classifies the question into one or more intents by keyword, and only
flags a visual whose type answers *none* of the matched intents. An unclassifiable question is skipped
(no false positive). Semantic nuance ("is this the *right* cut?") stays a human/LLM judgment.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

# intent → visual types that can generically answer it
_ALLOWED = {
    "temporal": {"trend_line", "line", "line_chart", "area", "area_chart", "combo", "column_line",
                 "clustered_column", "column"},
    # NB: pie / donut / gauge / treemap are FORBIDDEN (BC-CHART-08 / check_forbidden_charts) — never listed here,
    # so the advisory can't suggest a banned visual as a valid fit.
    "ranking": {"bar_chart", "bar", "clustered_bar", "clustered_column", "column", "decomposition_tree",
                "matrix", "table", "stacked_bar", "hundred_percent_stacked_bar", "waterfall"},
    "composition": {"stacked_bar", "hundred_percent_stacked_bar", "stacked_bar_100pct", "waterfall",
                    "decomposition_tree", "bar_chart", "clustered_column"},
    # a trend/variance line with a plan/target reference, or a bridge, both answer "vs plan"
    "comparison": {"column", "clustered_column", "bar_chart", "bullet", "kpi_card", "card",
                   "trend_line", "line", "line_chart", "area", "area_chart", "waterfall", "combo"},
    "driver": {"waterfall", "decomposition_tree", "scatter", "clustered_column", "bar_chart",
               "trend_line", "line", "line_chart"},
}

_PATTERNS = {
    "temporal": r"\b(over time|trend|trending|declin\w*|ris\w+|grow\w*|shrink\w*|trajector\w*|"
                r"last \d+\s*(months?|quarters?|weeks?)|month|quarter|year[- ]over|yoy|lengthening|"
                r"slowing|climbing|falling|since)\b",
    "comparison": r"\b(vs\.?\s*plan|vs\.?\s*target|versus plan|versus target|on track|off track|"
                  r"above target|below target|to plan|against plan|gap)\b",
    "composition": r"\b(mix|breakdown|break down|share of|component|composition|made up|split|"
                   r"what'?s behind|proportion)\b",
    "driver": r"\b(driver|is .*the driver|explains?|because|caused by|dragging|behind the|"
              r"root cause|attribut\w*)\b",
    "ranking": r"\b(where|which|concentrat\w*|worst|biggest|top\s|leak\w*|hotspot|by (segment|region|"
               r"category|lane|team|supplier|rep|cost ?cent\w+)|first|drives? most)\b",
}


def classify_question(question: Optional[str]) -> set[str]:
    """Return the set of intents a question expresses (may be empty = unclassifiable)."""
    q = (question or "").lower()
    return {intent for intent, pat in _PATTERNS.items() if re.search(pat, q)}


def fits(question: Optional[str], visual_type: Optional[str]) -> Tuple[bool, str]:
    """Return (ok, reason). ok=True when the visual can answer >=1 matched intent, or the question
    is unclassifiable (skipped), or the visual type is unknown to us (don't guess)."""
    intents = classify_question(question)
    if not intents:
        return True, "question intent unclassifiable — skipped"
    vt = (visual_type or "").strip().lower()
    known = set().union(*_ALLOWED.values())
    if vt not in known:
        return True, f"visual_type '{vt}' not in the fit catalogue — skipped"
    for intent in intents:
        if vt in _ALLOWED[intent]:
            return True, f"'{vt}' fits intent '{intent}'"
    return (False,
            f"'{vt}' cannot generically answer a {'/'.join(sorted(intents))} question "
            f"(expected e.g. {', '.join(sorted(next(iter(_ALLOWED[i] for i in intents))))[:60]}…)")
