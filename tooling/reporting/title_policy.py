"""title_policy.py — honest visual-title policy for GENERATED static reports (BC-NARR-01 refined).

Why this exists
---------------
IBCS "say it in the title" (BC-NARR-01) is right when a human authors a report *after* seeing the
period's data — the statement title is then a true reading of the chart. A **generated** report is
different: at generation time we do **not** know the data, and a classic BI tool (Power BI) renders a
**static** visual whose title cannot recompute itself. So hard-coding a conclusion like
"Win rate is dragging coverage below plan" as the title risks the title **contradicting the chart** the
moment the data says otherwise — the title would lie.

The only text that is *always* true is the **question** the visual is built to answer. So:

  • The QUESTION is the default header — it guides the read and never lies, even when the chart shows
    "nothing unusual" (which is itself a valid finding: the user reads it and moves on).
  • The MESSAGE is a governed **expected finding** (a hypothesis to verify), not a per-refresh fact.
    It renders as a framed subtitle (``EXPECTED_PREFIX + message``), clearly a thing to check — not an
    asserted verdict.
  • Only when the finding is **value_verified** (a real computed snapshot backs it, ADR-0017 gate) OR a
    **dynamic narrative** measure recomputes the statement live (smart-narrative DAX / a dynamic tier)
    may the MESSAGE lead as the statement header — because then something *guarantees* it is true.

This keeps the deterministic static report honest and pushes the "spoon-fed conclusion" to exactly the
places that can stand behind it. It changes only *which governed string* becomes the title — it never
invents text.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

# Frames the governed message as a hypothesis-to-verify, not an asserted fact, in the static case.
EXPECTED_PREFIX = "Expected finding — "

# VERIFIED filter-context constraint (MS Learn "expression-based titles" + community): a Power BI
# dynamic title measure evaluates in the page/report/slicer/cross-filter context but does NOT reliably
# receive the visual's own visual-level / Top-N filters. So a measure-driven statement title may only
# assert a WHOLE-SUBJECT SCALAR (the KPI value + its variance vs target). A Top-N / locally-filtered /
# "where it concentrates" claim would silently miscompute in the title — those stay as the question (or
# live in the evidence area / a card with matching visual-level filters), never as a dynamic title.
_LOCAL_FILTER_CLAIM = re.compile(
    r"\b(top\s*\d+|a few|a handful|handful|concentrat\w+|in a few|couple of|mid-tier|"
    r"lowest[- ]\w+|highest[- ]\w+|worst\s+\w+|leak\w*\s+at|where\b)\b", re.I)


def title_context_safe(text: Optional[str]) -> bool:
    """True when a statement can be a dynamic measure-title — i.e. it is a whole-subject scalar claim,
    not a Top-N / locally-filtered one that the title's filter context can't compute (see above)."""
    t = (text or "").strip()
    if not t:
        return False
    return _LOCAL_FILTER_CLAIM.search(t) is None


def title_contract(descriptor: Optional[str], question: Optional[str], verdict: Optional[str],
                   *, verdict_verified: bool = False, tool_live_compute: bool = False,
                   context_safe: Optional[bool] = None) -> dict:
    """The ONE uniform title logic for EVERY viz tool. The logic is identical on Power BI, Databricks
    AI/BI, React — only the *render slot* of the verdict differs, never the rule. Three roles:

      • title    = ``descriptor`` — a true, data-independent statement of WHAT the visual shows
                   ("Stage Conversion %, last 12 months"). Same on every tool; can never lie.
      • subtitle = the governed ``question`` the visual answers — the interpretation aid.
      • verdict  = the governed message / Einordnung — a SEPARATE element, rendered only where the tool
                   can honestly support it, promoted toward an IBCS statement *as far as the tool allows*:
                     'statement_title' — verified AND context-safe AND live/scalar → the verdict may
                                          itself lead as the title (full IBCS);
                     'annotation'      — verified + live tool, not title-safe → callout at the mark;
                     'kpi_status'      — verified, static tool → KPI value + semantic colour;
                     'omit'            — not verified → shown nowhere (never fabricated; the user reads).

    Returns {title, subtitle, verdict, verdict_render}."""
    safe = title_context_safe(verdict) if context_safe is None else context_safe
    if not verdict or not verdict_verified:
        render = "omit"
    elif tool_live_compute and safe:
        render = "statement_title"
    elif tool_live_compute:
        render = "annotation"
    else:
        render = "kpi_status"
    return {"title": (descriptor or "").strip() or None,
            "subtitle": (question or "").strip() or None,
            "verdict": (verdict or "").strip() or None,
            "verdict_render": render}


def resolve_header(
    question: Optional[str],
    message: Optional[str],
    *,
    value_verified: bool = False,
    dynamic_narrative: bool = False,
) -> Tuple[Optional[str], Optional[str]]:
    """Return ``(header, subtitle)`` for a generated visual.

    - ``value_verified`` or ``dynamic_narrative`` true  → the message leads as the header (honest to
      assert), no subtitle.
    - otherwise, with both question and message → the **question** leads; the message becomes the
      framed *expected-finding* subtitle.
    - if only one of the two is present, it is used as the header with no subtitle.
    """
    q = (question or "").strip() or None
    m = (message or "").strip() or None

    # (a) IBCS statement title. Two ways a statement may lead:
    #  • dynamic_narrative — a LIVE measure computes the title → the filter-context trap applies, so it
    #    may lead ONLY if it is a context-safe whole-subject scalar (Top-N/local claim → falls to the
    #    question, since a measure title can't receive the visual-level/Top-N filter).
    #  • value_verified — a static, human-/value-verified statement rendered as a STRING (not a live
    #    measure) → no filter-context issue, so it may lead as-is (this is the authored IBCS title).
    if dynamic_narrative and m and title_context_safe(m):
        return m, None
    if value_verified and m:
        return m, None
    if q and m:
        return q, f"{EXPECTED_PREFIX}{m}"    # question leads; message = hypothesis to verify (static, honest)
    return (q or m), None                    # only one available
