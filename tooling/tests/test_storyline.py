"""Tests for the storyline layer — deriver + governance.

Guards: every visual answers a stated question, every page has a decision spine, the page-1→page-2
handoff holds, and the generated storyboard doc stays in sync with the deriver.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from tooling.validation.check_storyline import check_bracket, render_out_of_sync

REPO = Path(__file__).resolve().parents[2]


def test_every_visual_has_a_question():
    missing = []
    for b in sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml")):
        d = yaml.safe_load(b.read_text(encoding="utf-8")) or {}
        for pk in ("page_1_summary", "page_2_execution"):
            p = (d.get("ux_layout_rules", {}) or {}).get(pk, {}) or {}
            for c in (p.get("component_30s") or []):
                if not (c.get("question") or "").strip():
                    missing.append(f"{d.get('id')}/{pk}/{c.get('kpi_id')}")
    assert not missing, "component_30s visuals without a `question`: " + ", ".join(missing)


def test_storyline_structure_clean():
    violations = []
    for b in sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml")):
        violations += check_bracket(yaml.safe_load(b.read_text(encoding="utf-8")) or {})
    assert not violations, "storyline structure violations:\n" + "\n".join(violations)


def test_storyboard_doc_in_sync():
    stale = render_out_of_sync()
    assert stale is None, stale


def test_json_contract_validates_against_schema():
    """The structured storyline (--json) is the generator/LLM contract — it must validate."""
    import json
    import importlib.util
    try:
        import jsonschema
    except ImportError:
        return  # optional dep; schema still shipped
    spec = importlib.util.spec_from_file_location(
        "derive_storyline", REPO / "tooling/storyline/derive_storyline.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    kpi_domains, kpi_keys, action_related = mod._kpi_domains(), mod._kpi_keys(), mod._action_related()
    data = mod.storylines_json(mod.load_brackets(None), kpi_domains, kpi_keys, action_related)
    schema = json.loads((REPO / "tooling/storyline/storyline.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(data, schema)
    # every use case present, every visual carries its question (the whole point)
    assert len(data) >= 17
    for s in data:
        for p in s["pages"]:
            for v in p["visuals"]:
                assert v["question"], f"{s['use_case']} visual missing question"


def _deriver():
    """Load the deriver module by path (it is a script, not an installed package)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "derive_storyline", REPO / "tooling/storyline/derive_storyline.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_business_cases_do_not_shadow_their_action_codes():
    """A ``*_business_case.yaml`` carries the same ``id`` as its action code but no
    ``use_case_links``. Reading it as an action code silently replaced the real links with an
    empty list — and which of the two won was decided by ``rglob``'s filesystem order, so the
    render differed between a dev machine and the runner (measured 01.08.2026: locally green,
    ``use_case_storylines.md is stale`` on CI).

    This guards the *effect*, not the implementation: every action code that has a business-case
    sibling AND declares ``use_case_links`` must come back with those links intact."""
    related = _deriver()._action_related()
    shadowed = []
    for bc in sorted((REPO / "core/action_codes").rglob("*_business_case.yaml")):
        ac = bc.with_name(bc.name.replace("_business_case.yaml", ".yaml"))
        if not ac.exists():
            continue
        doc = yaml.safe_load(ac.read_text(encoding="utf-8")) or {}
        links = doc.get("use_case_links") or {}
        expected = list(links.get("core_use_cases", []) or []) + list(links.get("related_use_cases", []) or [])
        if expected and related.get(doc.get("id")) != expected:
            shadowed.append(f"{doc.get('id')}: expected {expected}, got {related.get(doc.get('id'))}")
    assert not shadowed, (
        "business-case files shadowed their action codes in _action_related():\n" + "\n".join(shadowed))


def test_action_related_is_independent_of_directory_order():
    """The deriver must not let the filesystem decide the result. Reading the same directory
    twice through a shuffled listing has to produce the identical mapping.

    Honest about its own strength: with the business-case files skipped, no two files share an
    ``id`` today, so removing ``sorted()`` alone does NOT turn this red (verified by mutation).
    It is a forward guard — it fires the moment a genuine id collision is introduced, which is
    exactly when the previous bug became invisible."""
    import random
    mod = _deriver()
    baseline = mod._action_related()
    real_rglob = Path.rglob

    def shuffled(self, pattern):
        items = list(real_rglob(self, pattern))
        random.Random(1234).shuffle(items)
        return iter(items)

    Path.rglob = shuffled
    try:
        assert mod._action_related() == baseline
    finally:
        Path.rglob = real_rglob
