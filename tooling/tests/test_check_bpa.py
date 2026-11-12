"""ALUCA-BPA: eigene Tabular-Editor-Regeln, ihr Python-Laeufer und der Pin des offiziellen Satzes.

Jede eigene Regel hat zwei Fixture-Modelle unter ``fixtures/bpa_custom/<ID>/``: ``verstoesst``
muss die Regel ausloesen, ``besteht`` darf es nicht (Negativkontrolle in beide Richtungen).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from tooling.validation import check_bpa

REPO = Path(__file__).resolve().parents[2]
RULES = REPO / check_bpa.RULES_REL
PIN = REPO / check_bpa.PIN_REL
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "bpa_custom"
WORKFLOW = REPO / ".github" / "workflows" / "tabular-bpa.yml"

RULE_DATA = json.loads(RULES.read_text(encoding="utf-8"))
RULE_IDS = [r["ID"] for r in RULE_DATA]


def _run(dist: Path, *extra: str, tmp_path: Path) -> tuple[int, dict]:
    out = tmp_path / "bpa.json"
    code = check_bpa.main(["--repo-root", str(REPO), "--dist", str(dist), "--json", str(out), *extra])
    return code, (json.loads(out.read_text(encoding="utf-8")) if out.exists() else {})


def test_rules_file_is_blank_tabular_editor_array():
    assert isinstance(RULE_DATA, list) and len(RULE_DATA) == 16
    required = {"ID", "Name", "Category", "Description", "Severity", "Scope", "Expression"}
    for rule in RULE_DATA:
        assert required <= rule.keys(), rule["ID"]
        assert rule["Severity"] in (1, 2, 3)
        assert rule["ID"].startswith("ALUCA_")
    assert len(set(RULE_IDS)) == len(RULE_IDS)


def test_every_rule_is_evaluable_in_python():
    rules = check_bpa.load_rules(RULES)
    assert [r.id for r in rules if r.node is None] == []


def test_custom_ids_do_not_collide_with_pinned_official_set():
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    assert pin["rule_count"] == len(pin["rule_ids"]) == 71
    assert not set(RULE_IDS) & set(pin["rule_ids"])


def test_pin_is_commit_url_and_hash():
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    assert re.fullmatch(r"[0-9a-f]{40}", pin["commit"])
    assert re.fullmatch(r"[0-9a-f]{64}", pin["sha256"])
    assert pin["raw_url"] == (f"https://raw.githubusercontent.com/{pin['repo']}/{pin['commit']}/"
                              f"{pin['path']}")


def test_windows_workflow_uses_the_pin_and_the_custom_rules():
    """Peer-Test: der Windows-Lauf laedt genau den gepinnten Satz und prueft den Hash."""
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    wf = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert wf["env"]["BPA_RULES_REF"] == pin["commit"]
    assert wf["env"]["BPA_RULES_SHA256"] == pin["sha256"]
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "sha256sum -c" in text
    assert str(check_bpa.RULES_REL).replace("\\", "/") in text


def test_every_rule_has_both_fixtures_and_no_orphans():
    assert sorted(p.name for p in FIXTURES.iterdir() if p.is_dir()) == sorted(RULE_IDS)
    for rid in RULE_IDS:
        for kind in ("verstoesst", "besteht"):
            assert len(check_bpa.discover_models(FIXTURES / rid / kind)) == 1, (rid, kind)


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_rule_fires_on_violation(rule_id, tmp_path):
    code, data = _run(FIXTURES / rule_id / "verstoesst", tmp_path=tmp_path)
    assert code == 0
    assert len(data["models"]) == 1
    assert next(r for r in data["rules"] if r["id"] == rule_id)["findings"] >= 1


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_rule_silent_on_compliant_model(rule_id, tmp_path):
    code, data = _run(FIXTURES / rule_id / "besteht", tmp_path=tmp_path)
    assert code == 0
    assert len(data["models"]) == 1
    # Die Zusage gilt nur, wenn das Modell Objekte im Geltungsbereich der Regel hat.
    scopes = {s.strip() for s in next(r for r in RULE_DATA if r["ID"] == rule_id)["Scope"].split(",")}
    assert sum(n for k, n in data["models"][0]["objects"].items() if k in scopes) >= 1
    assert next(r for r in data["rules"] if r["id"] == rule_id)["findings"] == 0


def test_no_models_is_not_run_not_green(tmp_path):
    code, _ = _run(tmp_path, tmp_path=tmp_path)
    assert code == check_bpa.EXIT_NOT_RUN


def test_strict_fails_only_on_severity_3(tmp_path):
    error_rule = FIXTURES / "ALUCA_M_TABLE_LITERAL_NEEDS_LET" / "verstoesst"
    warn_rule = FIXTURES / "ALUCA_DAX_IF_NESTING" / "verstoesst"
    assert _run(error_rule, "--strict", tmp_path=tmp_path)[0] == check_bpa.EXIT_STRICT
    assert _run(warn_rule, "--strict", tmp_path=tmp_path)[0] == check_bpa.EXIT_OK


def test_unknown_expression_form_is_windows_only_not_guessed(tmp_path):
    rules = tmp_path / "rules.json"
    rules.write_text(json.dumps([
        {"ID": "X_UNBEKANNT", "Name": "x", "Category": "x", "Description": "x", "Severity": 2,
         "Scope": "Measure", "Expression": "Model.AllMeasures.Any(Name == \"x\")"},
        {"ID": "X_INLINE_FLAG", "Name": "x", "Category": "x", "Description": "x", "Severity": 2,
         "Scope": "Measure", "Expression": "RegEx.IsMatch(Expression, \"a(?i)b\")"},
    ]), encoding="utf-8")
    loaded = check_bpa.load_rules(rules)
    assert [r.node for r in loaded] == [None, None]
    assert all(r.unsupported for r in loaded)
    code = check_bpa.main(["--dist", str(FIXTURES / "ALUCA_DAX_ISERROR" / "verstoesst"),
                           "--rules", str(rules)])
    assert code == check_bpa.EXIT_OK


def test_dotnet_literal_and_operators():
    obj = {"_kind": "Partition", "SourceType": "M", "Query": 'x = "a"', "IsHidden": False}
    assert check_bpa.compile_expression('SourceType.ToString() = "M" and not IsHidden')(obj)
    assert check_bpa.compile_expression('Query.Contains("""a""")')(obj)
    assert check_bpa.compile_expression('RegEx.IsMatch(Query, "\\s=\\s")')(obj)
    assert not check_bpa.compile_expression('SourceType <> "M" or IsHidden')(obj)


def test_lineage_tags_follow_indentation():
    content = ("table t\n\tlineageTag: T1\n\n\tmeasure 'a b' = 1\n\t\tlineageTag: M1\n\n"
               "\tcolumn c\n\t\tdataType: int64\n\n\tpartition t = m\n\t\tsource = x\n")
    tags = check_bpa.lineage_tags(content)
    assert tags == {("table", "t"): "T1", ("measure", "a b"): "M1"}


def test_dist_models_are_all_checked(tmp_path):
    dist = REPO / check_bpa.DIST_REL
    expected = check_bpa.discover_models(dist)
    if not expected:
        pytest.skip("keine dist-Modelle im Checkout")
    code, data = _run(dist, tmp_path=tmp_path)
    assert code == 0
    assert len(data["models"]) == len(expected)
    assert all(m["objects"]["Measure"] > 0 for m in data["models"])
