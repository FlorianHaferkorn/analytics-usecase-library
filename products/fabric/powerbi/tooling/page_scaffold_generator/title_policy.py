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
