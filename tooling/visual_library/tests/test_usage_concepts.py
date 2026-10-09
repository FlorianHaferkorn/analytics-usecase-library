"""Usage concepts as the second axis next to the notation profiles (ADR-0026, Meridian D-720).

Proves: the usage registry is well-formed and only names offered profiles; the bracket schema enum
is exactly the registry; `minimal` is not offered; `editorial` keeps the title descriptive (D-641);
the derived `monitoring` style greys data marks but keeps rated status colours, while `story` keeps
greying them (counter-check).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

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
