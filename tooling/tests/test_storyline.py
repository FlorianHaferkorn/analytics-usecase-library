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
