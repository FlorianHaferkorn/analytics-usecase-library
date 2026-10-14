"""Usage concepts as the second axis next to the notation profiles (ADR-0026, Meridian D-720).

Proves: the usage registry is well-formed and only names offered profiles; the bracket schema enum
is exactly the registry; `minimal` is not offered; `editorial` keeps the title descriptive (D-641);
the derived `monitoring` style greys data marks but keeps rated status colours, while `story` keeps
greying them (counter-check); in `monitoring` a colour condition depends on the direction, never on the
sign alone — a good deviation stays grey (ADR-0026 §6, 09.10.2026).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import render  # noqa: E402

SCHEMA = REPO_ROOT / "tooling" / "generator" / "schemas" / "usecase_bracket.schema.json"
GREY = "#8C8C8C"
BAD = "#A4262C"
POS = "#107C10"


def _concepts() -> dict:
    return render.usage_concepts()["concepts"]


def test_exactly_one_default_and_it_is_the_registry_default():
    reg = render.usage_concepts()
    defaults = [c for c, d in reg["concepts"].items() if d.get("is_default")]
    assert defaults == [reg["default"]] == ["entscheidung"]


def test_every_concept_names_only_offered_registered_profiles():
    offered = set(render.offered_profiles())
    for cid, c in _concepts().items():
        assert c.get("profiles"), f"{cid}: no profile allowed"
        unknown = set(c["profiles"]) - offered
        assert not unknown, f"{cid}: names profiles that are not offered/registered: {sorted(unknown)}"
        assert c.get("page_structure") and c.get("source"), f"{cid}: page_structure and source are required"


def test_bracket_schema_enum_is_the_registry():
    s = json.loads(SCHEMA.read_text(encoding="utf-8"))
    enum = s["properties"]["ux_layout_rules"]["properties"]["usage_concept"]["enum"]
    assert sorted(enum) == sorted(_concepts())


def test_minimal_is_registered_but_not_offered():
    assert "minimal" in render.all_profiles()
    assert "minimal" not in render.offered_profiles()
    assert all("minimal" not in c["profiles"] for c in _concepts().values())


def test_combination_exclusions_hold():
    assert render.usage_allows("entscheidung", "house_default")
    assert render.usage_allows("monitoring", "monitoring")
    assert not render.usage_allows("monitoring", "story"), "accent principle clashes with alarm colours"
    assert not render.usage_allows("narrativ", "fluent")
    assert not render.usage_allows("explorativ", "story")


def test_editorial_title_is_descriptive_per_d641():
    rule = render.profile_def("editorial")["rules"]["titles"]
    assert "states the finding" not in rule
    assert "descriptive" in rule and "key message" in rule


def test_monitoring_is_a_marked_derivation():
    d = render.profile_def("monitoring")
    assert d["kind"] == "style" and d["base_notation"] == "house_default"
    assert d.get("basis") == "derivation" and d.get("status") == "experimental"
    assert any(str(s).startswith("derivation:") and "ISA-101" in s for s in d["source"])


def _spec() -> dict:
    return {"layer": [
        {"mark": {"type": "bar", "color": "#605E5C"},
         "encoding": {"color": {"condition": [{"test": "datum.bad", "value": BAD}], "value": POS}}},
        {"mark": "text", "encoding": {"color": {"value": "#201F1E"}}},
    ]}


def test_status_focus_keeps_rated_colours_and_greys_the_rest():
    out = render.with_focus(_spec(), GREY, keep_conditions=True)
    bar, text = out["layer"]
    assert bar["mark"]["color"] == GREY
    assert bar["encoding"]["color"]["condition"][0]["value"] == BAD, "a breached threshold must keep its colour"
    assert bar["encoding"]["color"]["value"] == GREY, "the normal state is grey"
    assert text["encoding"]["color"]["value"] == "#201F1E", "labels keep the text colour"


def test_counter_check_story_focus_greys_rated_colours():
    out = render.with_focus(_spec(), GREY)
    assert out["layer"][0]["encoding"]["color"]["condition"][0]["value"] == GREY


def test_focus_is_true_or_status_only():
    """Steward review 09.10.2026: any other truthy `focus` (typo 'Status', 'yes') silently greyed the rated
    conditions and switched off the accent. Only absent/False, True (story) or 'status' (monitoring) are valid."""
    bad = {p: render.profile_def(p).get("focus") for p in render.all_profiles()
           if render.profile_def(p).get("focus") not in (None, False, True, "status")}
    assert bad == {}


def test_unknown_profile_is_an_error_not_an_exclusion():
    """Steward review 09.10.2026: a misspelled profile read as 'combination excluded'."""
    import pytest
    with pytest.raises(KeyError):
        render.usage_allows("monitoring", "Monitoring")
    assert render.usage_allows("monitoring", "monitoring") in (True, False)


# ── ADR-0026 §6 (Florian 09.10.2026): monitoring colours only a breach, by direction ─────────────────────────

class _Datum(dict):
    """A Vega `datum` for Python eval: `datum['f']` and `datum.f` both read the value."""
    __getattr__ = dict.__getitem__


def _colour(channel: dict, datum: dict) -> str:
    """The colour a Vega-Lite colour channel gives one datum (condition tests are Python-evaluable here)."""
    conds = channel.get("condition") or []
    for c in conds if isinstance(conds, list) else [conds]:
        if eval(c["test"], {}, {"datum": _Datum(datum)}):  # noqa: S307 - our own template expressions
            return c["value"]
    return channel["value"]


def _colour_channels(spec) -> "list[dict]":
    out = []

    def walk(n):
        if isinstance(n, dict):
            if "mark" in n and render._mark_kind(n) != "text":
                for ch in ("color", "fill", "stroke"):
                    v = (n.get("encoding") or {}).get(ch)
                    if isinstance(v, dict) and "condition" in v:
                        out.append(v)
            for k, v in n.items():
                if k != "config":
                    walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
    walk(spec)
    return out


def _monitoring_idioms() -> "list[str]":
    out = []
    for idiom in sorted(p.stem for p in render.LIB.glob("*.yaml") if not p.stem.startswith("_") and p.stem != "index"):
        try:
            render.render_target(idiom, "html_vegalite", "monitoring")
        except KeyError:
            continue        # no Vega-Lite track under house_default (native/SVG idioms)
        out.append(idiom)
    return out


def _tests(idiom: str, profile: str, polarity: str) -> "list[str]":
    spec = json.loads(render.render_target(idiom, "html_vegalite", profile,
                                           params={"polarity": polarity, "target_val": "44.1"})[0])
    return [c["condition"]["test"] if isinstance(c["condition"], dict) else c["condition"][0]["test"]
            for c in _colour_channels(spec)]


def test_monitoring_colours_only_by_direction():
    """Every colour condition of every idiom under `monitoring` depends on the direction (`polarity`): a test that
    reads the same for higher- and lower-is-better colours by sign. Counter-check: under `house_default` the same
    idioms still colour by sign (deviation_bar, lollipop, waterfall_variance …), so the test would be red without
    `status_breach`."""
    idioms = _monitoring_idioms()
    assert len(idioms) >= 10
    by_sign = []
    for idiom in idioms:
        hoch, tief = _tests(idiom, "monitoring", "1"), _tests(idiom, "monitoring", "-1")
        assert len(hoch) == len(tief)
        assert all(a != b for a, b in zip(hoch, tief)), (idiom, hoch)
        house = _tests(idiom, "house_default", "1"), _tests(idiom, "house_default", "-1")
        if any(a == b for a, b in zip(*house)):
            by_sign.append(idiom)
    assert {"deviation_bar", "lollipop", "multi_tier_column", "variance_pin", "waterfall_pvm",
            "waterfall_variance"} <= set(by_sign), by_sign


@pytest.mark.parametrize("polarity, gut, schlecht", [("1", 5.0, -5.0), ("-1", -5.0, 5.0)])
def test_good_deviation_stays_grey_bad_one_is_red(polarity, gut, schlecht):
    """deviation_bar under `monitoring`: the adverse deviation in the measure's direction is red, the good one grey —
    also for lower-is-better, where a negative deviation is good."""
    spec = json.loads(render.render_target("deviation_bar", "html_vegalite", "monitoring",
                                           params={"polarity": polarity})[0])
    (ch,) = _colour_channels(spec)
    field = render.load_entry("deviation_bar")["canonical_params"]["field"]
    assert _colour(ch, {field: gut}) == GREY, "a good deviation stays grey"
    assert _colour(ch, {field: schlecht}) == BAD, "a breach keeps the status colour"
    assert _colour(ch, {field: 0.0}) == GREY


def test_counter_check_sign_colouring_marks_a_good_deviation_red():
    """Gegenprobe: the house template under the old monitoring rule (`with_focus(keep_conditions=True)` without
    `status_breach`) colours a good deviation of a lower-is-better measure red — exactly what ADR-0026 §6 forbids."""
    spec = json.loads(render.render_target("deviation_bar", "html_vegalite", "house_default",
                                           params={"polarity": "-1"})[0])
    alt = render.with_focus(spec, GREY, keep_conditions=True)
    (ch,) = _colour_channels(alt)
    field = render.load_entry("deviation_bar")["canonical_params"]["field"]
    assert _colour(ch, {field: -5.0}) == BAD


def test_lollipop_below_target_is_good_when_lower_is_better():
    spec = json.loads(render.render_target("lollipop", "html_vegalite", "monitoring",
                                           params={"polarity": "-1", "target_val": "40"})[0])
    (ch,) = _colour_channels(spec)
    field = render.load_entry("lollipop")["canonical_params"]["field"]
    assert _colour(ch, {field: 35.0}) == GREY and _colour(ch, {field: 45.0}) == BAD


def test_direction_reads_polarity_then_direction_then_default():
    assert render.polarity_of({"polarity": "-1"}) == "-1"
    assert render.polarity_of({"direction": "lower_is_better"}) == "-1"
    assert render.polarity_of({"direction": "higher_is_better"}) == "1" == render.polarity_of({})
