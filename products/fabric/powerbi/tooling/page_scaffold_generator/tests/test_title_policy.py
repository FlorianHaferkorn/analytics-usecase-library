"""Title policy — the question leads, the message is never the title (A-34, IBCS UN 2.1/2.2)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from page_scaffold_generator.title_policy import EXPECTED_PREFIX, resolve_header, title_context_safe
import pytest

from page_scaffold_generator.title_block import (
    TITLE_BLOCK_HEIGHT, build_title_objects, textbox_paragraphs, title_block_height, wrapped_lines,
)
from tooling.reporting.title_policy import (
    EXPECTED_PREFIX as _PREFIX, LOCKED_VERDICT_RENDERS, VERDICT_RENDERS, TitleLines, frame_key_message, hybrid,
    ibcs_lines, single_line, title_contract, title_lines_from,
)

REPO_ROOT = Path(__file__).resolve().parents[6]
Q = "Is the coverage gap a volume problem or a conversion problem?"
M = "Win rate is dragging coverage below plan, not a shortage of open opportunities"


def test_static_default_question_leads_message_is_framed_subtitle():
    header, subtitle = resolve_header(Q, M)
    assert header == Q                                  # the always-true text leads (never lies)
    assert subtitle == EXPECTED_PREFIX + M              # message is a hypothesis to verify, framed


def test_value_verified_drops_the_frame_but_question_still_leads():
    # A-34 (D-641, UN 2.2): until 08.10.2026 the verified message became the header. Now it stays subtitle.
    header, subtitle = resolve_header(Q, M, value_verified=True)
    assert header == Q and subtitle == M


def test_dynamic_narrative_drops_the_frame_but_question_still_leads():
    header, subtitle = resolve_header(Q, M, dynamic_narrative=True)
    assert header == Q and subtitle == M


def test_message_is_never_the_header():
    for kwargs in ({}, {"value_verified": True}, {"dynamic_narrative": True},
                   {"value_verified": True, "dynamic_narrative": True}):
        for q in (Q, None):
            header, _ = resolve_header(q, M, **kwargs)
            assert header != M, (q, kwargs)


def test_missing_message_falls_back_to_question():
    assert resolve_header(Q, None) == (Q, None)
    assert resolve_header(Q, "   ") == (Q, None)


def test_missing_question_leaves_header_to_the_label():
    # no question → no header (the caller keeps its descriptive label); the message stays a subtitle
    assert resolve_header(None, M) == (None, EXPECTED_PREFIX + M)
    assert resolve_header(None, M, value_verified=True) == (None, M)


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


def test_measure_title_scalar_claim_is_backed_but_not_the_title():
    q = "Is EBITDA on plan?"
    m = "EBITDA margin is 1.8 pp below plan"
    assert resolve_header(q, m, dynamic_narrative=True) == (q, m)


def test_static_verified_statement_is_unframed_subtitle():
    # a static, verified statement is a STRING, not a live measure → no filter-context trap, so it drops
    # its frame even if it names a locus; it still does not lead (A-34).
    m = "Margin is concentrated in a few business units"
    assert resolve_header("Q?", m, value_verified=True) == ("Q?", m)


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
    # verified, live tool, context-safe scalar → the key-message slot above the title (UN 2.1), not the title
    scalar = "EBITDA margin is 1.8 pp below plan"
    c = title_contract(DESC, Q, scalar, verdict_verified=True, tool_live_compute=True)
    assert c["verdict_render"] == "key_message" and c["title"] == DESC
    assert c["key_message_position"] == "above_title"


def test_contract_never_returns_a_locked_render():
    # Sperre statement_title (D-641): kein Pfad des Vertrags setzt den Befund in den Titel.
    assert not LOCKED_VERDICT_RENDERS & set(VERDICT_RENDERS)
    for verdict in (V, "EBITDA margin is 1.8 pp below plan", None):
        for verified in (False, True):
            for live in (False, True):
                for safe in (None, True, False):
                    c = title_contract(DESC, Q, verdict, verdict_verified=verified, tool_live_compute=live,
                                       context_safe=safe)
                    assert c["verdict_render"] in VERDICT_RENDERS
                    assert c["verdict_render"] not in LOCKED_VERDICT_RENDERS


def test_contract_refuses_the_verdict_as_title():
    with pytest.raises(ValueError, match="D-641"):
        title_contract(V, Q, V, verdict_verified=True)
    # normalised: case and whitespace do not hide the statement title
    with pytest.raises(ValueError, match="D-641"):
        title_contract("  conversion LEAKS at   mid-stage ", Q, V, verdict_verified=True)


def test_contract_does_not_refuse_an_omitted_verdict():
    # Befund 6: unverified → omitted, shown nowhere → no statement title, no error
    c = title_contract(V, Q, V)
    assert c["verdict_render"] == "omit" and c["title"] == V


# --- title_lines {who, what, when} (IBCS UN 2.2) ------------------------------------------------

LINES = {"who": "Aurora Group", "what": "Gross margin", "unit": "%", "when": "Jan..Dec 2026, AC and PL"}


def test_contract_carries_title_lines():
    c = title_contract(None, Q, None, title_lines=LINES)
    # same form as TitleLines and the bracket field: measure and unit separate (Befund 7)
    assert c["title_lines"] == LINES
    # without a descriptor the measure line is the title
    assert c["title"] == "Gross margin in %"
    # with a descriptor the descriptor stays the title; the lines travel alongside
    assert title_contract(DESC, Q, None, title_lines=LINES)["title"] == DESC
    assert title_contract(DESC, Q, None)["title_lines"] is None


def test_title_lines_need_who_and_what():
    with pytest.raises(ValueError, match="UN 2.2"):
        title_lines_from({"who": "Aurora Group", "what": " "})
    with pytest.raises(ValueError, match="UN 2.2"):
        title_contract(DESC, Q, None, title_lines={"what": "Gross margin"})


def test_key_message_position_is_checked():
    assert title_contract(DESC, Q, None, key_message_position="right_of_title")["key_message_position"] == \
        "right_of_title"
    with pytest.raises(ValueError, match="position"):
        title_contract(DESC, Q, None, key_message_position="below_chart")
    with pytest.raises(ValueError, match="position"):
        ibcs_lines(title_lines_from(LINES), "GM fell", "below_chart")


def test_unverified_key_message_is_always_framed():
    # Befund 1: without a decision question the unverified big idea stood unframed in the header
    assert frame_key_message("GM is under pressure") == _PREFIX + "GM is under pressure"
    assert frame_key_message("GM is under pressure", "Is GM holding?") == \
        "Is GM holding?  \u00b7  " + _PREFIX + "GM is under pressure"
    assert frame_key_message("GM is under pressure", value_verified=True) == "GM is under pressure"
    assert frame_key_message(None) is None


def test_config_loader_frames_big_idea_without_question(monkeypatch):
    from page_scaffold_generator.config_loader import ConfigLoader
    loader = ConfigLoader(REPO_ROOT)
    orig = loader.load_use_case_bracket

    def ohne_frage(uc):
        b = orig(uc)
        b["ux_layout_rules"]["page_1_summary"].pop("decision_question", None)
        b["ux_layout_rules"]["page_1_summary"]["key_message_position"] = "above_title"
        return b
    monkeypatch.setattr(loader, "load_use_case_bracket", ohne_frage)
    cfg = loader.get_page_config("COM-002", "overview")
    assert cfg["big_idea_text"].startswith(_PREFIX)
    assert cfg["key_message_position"] == "above_title"


def test_config_loader_rejects_unknown_key_message_position(monkeypatch):
    from page_scaffold_generator.config_loader import ConfigLoader
    loader = ConfigLoader(REPO_ROOT)
    orig = loader.load_use_case_bracket

    def falsch(uc):
        b = orig(uc)
        b["ux_layout_rules"]["page_1_summary"]["key_message_position"] = "below_chart"
        return b
    monkeypatch.setattr(loader, "load_use_case_bracket", falsch)
    with pytest.raises(ValueError, match="position"):
        loader.get_page_config("COM-002", "overview")


def test_presentations_share_one_content():
    lines = title_lines_from(LINES)
    assert ibcs_lines(lines, "GM fell 12% vs plan") == [
        ("key_message", "GM fell 12% vs plan"), ("who", "Aurora Group"), ("what", "Gross margin in %"),
        ("when", "Jan..Dec 2026, AC and PL")]
    # right_of_title: the renderer places the key message beside the title, not in the sequence
    assert ibcs_lines(lines, "GM fell", "right_of_title")[0] == ("who", "Aurora Group")
    assert hybrid(lines, "GM fell") == {"strong": "Gross margin", "rest": "in %",
                                        "subtitle": "Aurora Group · Jan..Dec 2026, AC and PL",
                                        "key_message": "GM fell"}
    assert single_line(lines) == "Aurora Group | Gross margin in % | Jan..Dec 2026, AC and PL"
    assert single_line(TitleLines(who="Aurora Group", what="OTIF")) == "Aurora Group | OTIF"


# --- PBIR title block (page_builder) ------------------------------------------------------------

def test_title_block_puts_key_message_above_three_lines():
    objs = build_title_objects(title_lines_from(LINES), "Expected finding — GM is under pressure")
    paras = objs["general"][0]["properties"]["paragraphs"]
    assert [ "".join(r["value"] for r in p["textRuns"]) for p in paras] == [
        "Expected finding — GM is under pressure", "Aurora Group", "Gross margin in %",
        "Jan..Dec 2026, AC and PL"]
    # key message bold 14 pt; line 2: measure bold, "in <unit>" normal (UN 2.2)
    assert paras[0]["textRuns"][0]["textStyle"] == {"fontSize": "14pt", "fontWeight": "bold"}
    what = paras[2]["textRuns"]
    assert what[0]["textStyle"].get("fontWeight") == "bold" and "fontWeight" not in what[1]["textStyle"]
    with pytest.raises(ValueError, match="above_title"):
        build_title_objects(title_lines_from(LINES), "x", "right_of_title")


def test_page_builder_default_does_not_assert_statement_titles():
    from page_scaffold_generator.page_builder import PageBuilder
    assert PageBuilder().assert_statement_titles is False
    assert PageBuilder().title_lines is None


def _grid_page(builder, big_idea):
    blueprint = {"canvas": {"width": 1920, "height": 1080},
                 "slots": [{"slot_id": "KPI_Cards", "grid": [0, 0, 12, 2], "visual_type_hint": "cardVisual"}]}
    return builder.build_page_structure(slots={}, template="T1", grid_blueprint=blueprint,
                                        card_measure_names=["Gross Margin %"], big_idea_text=big_idea)


def test_page_builder_renders_title_block_and_moves_grid_below():
    from page_scaffold_generator.page_builder import PageBuilder
    plain = PageBuilder()
    with_lines = PageBuilder()
    with_lines.title_lines = title_lines_from(LINES)
    a = _grid_page(plain, "GM is under pressure")
    b = _grid_page(with_lines, "GM is under pressure")
    head_a = next(v for v in a["visuals"] if v["name"] == "Header")
    head_b = next(v for v in b["visuals"] if v["name"] == "Header")
    # without title_lines: the one-line Header as before (dist unchanged)
    assert "text" in head_a["visual"]["objects"]
    # with title_lines: key message above who / what / when, taller block
    assert textbox_paragraphs(head_b) == ["GM is under pressure", "Aurora Group", "Gross margin in %",
                                          "Jan..Dec 2026, AC and PL"]
    assert head_b["position"]["height"] == TITLE_BLOCK_HEIGHT
    kpi_a = next(v for v in a["visuals"] if v["name"] != "Header")
    kpi_b = next(v for v in b["visuals"] if v["name"] != "Header")
    assert kpi_b["position"]["y"] - kpi_a["position"]["y"] == TITLE_BLOCK_HEIGHT - head_a["position"]["height"]
    assert kpi_b["position"]["y"] >= head_b["position"]["y"] + TITLE_BLOCK_HEIGHT


def test_title_block_grows_with_long_key_message():
    # Befund 5: 300 characters of big idea plus question no longer fit 112 px
    lines = title_lines_from(LINES)
    long_msg = frame_key_message("Gross margin is under pressure because " + "price and mix " * 18,
                                 "Is our gross margin holding against price and mix pressure?")
    assert wrapped_lines(long_msg, 14) >= 2
    h = title_block_height(lines, long_msg)
    assert h > TITLE_BLOCK_HEIGHT
    assert title_block_height(lines, "GM fell") == TITLE_BLOCK_HEIGHT
    from page_scaffold_generator.page_builder import PageBuilder
    b = PageBuilder()
    b.title_lines = lines
    page = _grid_page(b, long_msg)
    head = next(v for v in page["visuals"] if v["name"] == "Header")
    kpi = next(v for v in page["visuals"] if v["name"] != "Header")
    assert head["position"]["height"] == h
    assert kpi["position"]["y"] >= head["position"]["y"] + h


def test_template_path_refuses_title_lines():
    # Befund 4: the legacy template path has no title block → loud error, not a silent drop
    from page_scaffold_generator.page_builder import PageBuilder
    b = PageBuilder()
    b.title_lines = title_lines_from(LINES)
    with pytest.raises(ValueError, match="grid path"):
        b.build_page_structure(slots={}, template="T1", card_measure_names=["Gross Margin %"])
    PageBuilder().build_page_structure(slots={}, template="T1", card_measure_names=["Gross Margin %"])


@pytest.mark.parametrize("height", [None, "112", True, 0, -5])
def test_apply_page_layout_falls_back_on_bad_header_height(tmp_path, height):
    # Befund 9: null / text / bool / non-positive height → fallback to ZONE0_HEADER_HEIGHT
    import json as _json
    from page_scaffold_generator.apply_page_layout import apply_layout_to_page
    from page_scaffold_generator.grid_calculator import ZONE0_HEADER_HEIGHT
    page = tmp_path / "P"
    for name, pos in (("Header", {"x": 32, "y": 32, "height": height, "width": 1856}),
                      ("KPI_Cards", {"x": 0, "y": 0, "height": 10, "width": 10})):
        (page / "visuals" / name).mkdir(parents=True)
        (page / "visuals" / name / "visual.json").write_text(
            _json.dumps({"name": name, "position": pos}), encoding="utf-8")
    blueprint = {"canvas": {"width": 1920, "height": 1080}, "slots": [{"slot_id": "KPI_Cards", "grid": [0, 0, 12, 2]}]}
    apply_layout_to_page(tmp_path, "P", blueprint)
    kpi = _json.loads((page / "visuals" / "KPI_Cards" / "visual.json").read_text(encoding="utf-8"))
    ref = tmp_path / "R"
    (ref / "visuals" / "Header").mkdir(parents=True)
    (ref / "visuals" / "KPI_Cards").mkdir(parents=True)
    (ref / "visuals" / "Header" / "visual.json").write_text(_json.dumps(
        {"name": "Header", "position": {"height": ZONE0_HEADER_HEIGHT}}), encoding="utf-8")
    (ref / "visuals" / "KPI_Cards" / "visual.json").write_text(_json.dumps(
        {"name": "KPI_Cards", "position": {"x": 0, "y": 0, "height": 10, "width": 10}}), encoding="utf-8")
    apply_layout_to_page(tmp_path, "R", blueprint)
    kpi_ref = _json.loads((ref / "visuals" / "KPI_Cards" / "visual.json").read_text(encoding="utf-8"))
    assert kpi["position"]["y"] == kpi_ref["position"]["y"]
