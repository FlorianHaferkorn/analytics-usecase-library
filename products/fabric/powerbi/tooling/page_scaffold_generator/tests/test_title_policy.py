"""Static-BI title policy — the question leads unless a guarantee backs the message."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from page_scaffold_generator.title_policy import EXPECTED_PREFIX, resolve_header, title_context_safe
from tooling.reporting.title_policy import title_contract

Q = "Is the coverage gap a volume problem or a conversion problem?"
M = "Win rate is dragging coverage below plan, not a shortage of open opportunities"


def test_static_default_question_leads_message_is_framed_subtitle():
    header, subtitle = resolve_header(Q, M)
    assert header == Q                                  # the always-true text leads (never lies)
    assert subtitle == EXPECTED_PREFIX + M              # message is a hypothesis to verify, framed


def test_value_verified_lets_message_lead_unframed():
    header, subtitle = resolve_header(Q, M, value_verified=True)
    assert header == M and subtitle is None             # a real computed value backs the assertion


def test_dynamic_narrative_lets_message_lead():
    header, subtitle = resolve_header(Q, M, dynamic_narrative=True)
    assert header == M and subtitle is None


def test_missing_message_falls_back_to_question():
    assert resolve_header(Q, None) == (Q, None)
    assert resolve_header(Q, "   ") == (Q, None)


def test_missing_question_uses_message_without_subtitle():
    # nothing guaranteed, but no question to lead → message is all we have; don't double-render it
    assert resolve_header(None, M) == (M, None)


def test_both_missing_yields_none():
    assert resolve_header(None, None) == (None, None)


# --- a) measure-driven title + verified filter-context guard --------------------------------------

def test_context_safe_rejects_topn_and_concentration_claims():
    # whole-subject scalar → safe as a dynamic measure title
    assert title_context_safe("EBITDA margin is below plan") is True
    assert title_context_safe("OTIF is 2.7 pp below target") is True
    # Top-N / locally-filtered / concentration claims → NOT computable in a title's filter context
    assert title_context_safe("Net Sales gaps are concentrated in a handful of regions") is False
    assert title_context_safe("Top 3 cost centres carry 68% of the gap") is False
    assert title_context_safe("The funnel leaks at the mid-stage") is False
    assert title_context_safe("Attrition is concentrated in the lowest-engagement segments") is False


def test_measure_title_concentration_claim_does_not_lead():
    q = "Where is the Plan gap concentrated?"
    m = "Net Sales gaps are concentrated in a handful of regions"
    # a LIVE measure title can't receive the visual-level/Top-N filter → concentration claim falls to
    # the question; only the dynamic (measure) path is guarded.
    header, subtitle = resolve_header(q, m, dynamic_narrative=True)
    assert header == q and subtitle == EXPECTED_PREFIX + m


def test_measure_title_scalar_claim_leads():
    q = "Is EBITDA on plan?"
    m = "EBITDA margin is 1.8 pp below plan"
    assert resolve_header(q, m, dynamic_narrative=True) == (m, None)


def test_static_verified_statement_leads_unguarded():
    # a static, authored/verified statement is a STRING, not a live measure → no filter-context trap;
    # it may lead even if it names a locus (preserves existing IBCS-authored report titles).
    m = "Margin is concentrated in a few business units"
    assert resolve_header("Q?", m, value_verified=True) == (m, None)


# --- uniform title contract (one logic, all tools) ------------------------------------------------

DESC, Q, V = "Stage Conversion %, last 12 months", "Where does conversion leak?", "Conversion leaks at mid-stage"


def test_contract_title_and_subtitle_are_uniform():
    # title = WHAT is shown; subtitle = the question — identical regardless of tool/verdict slot
    for kwargs in ({}, {"verdict_verified": True}, {"verdict_verified": True, "tool_live_compute": True}):
        c = title_contract(DESC, Q, V, **kwargs)
        assert c["title"] == DESC and c["subtitle"] == Q


def test_contract_verdict_render_by_capability():
    # not verified → the verdict is shown nowhere (never fabricated)
    assert title_contract(DESC, Q, V)["verdict_render"] == "omit"
    # verified, static tool (PBI) → KPI status/colour, not the title
    assert title_contract(DESC, Q, V, verdict_verified=True)["verdict_render"] == "kpi_status"
    # verified, live tool, but a Top-N/local claim → annotation, never the title
    assert title_contract(DESC, Q, V, verdict_verified=True, tool_live_compute=True)["verdict_render"] == "annotation"
    # verified, live tool, context-safe scalar → full IBCS: the verdict may lead as the title
    scalar = "EBITDA margin is 1.8 pp below plan"
    assert title_contract(DESC, Q, scalar, verdict_verified=True,
                          tool_live_compute=True)["verdict_render"] == "statement_title"
