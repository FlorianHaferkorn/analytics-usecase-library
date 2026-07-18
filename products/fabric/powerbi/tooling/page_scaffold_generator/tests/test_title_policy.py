"""Static-BI title policy — the question leads unless a guarantee backs the message."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from page_scaffold_generator.title_policy import EXPECTED_PREFIX, resolve_header

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
