"""WB-009: named staffing puts roster names against the canon hours and writes nothing."""
import copy
import json
from pathlib import Path

import pytest
import yaml

from tooling.superversion import preis_kanon_mandant as pkm
from tooling.superversion.project_package import alternative_impact as impact
from tooling.tests.reference_baseline import reference_baseline
from tooling.superversion.project_package import staffing
from tooling.tests.test_project_commercial_impact import _TENANT

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "tooling/generator/schemas"
PROJECT, DECISION = impact.REFERENCE_PROJECT, impact.REFERENCE_DECISION
#: Invented people. Nobody real.
ROSTER = {"personen": [
    {"name": "Person Alpha", "rolle": "engineer", "standort": "nearshore", "stunden_je_woche": 20, "verfuegbar_ab": "2026-10-05"},
    {"name": "Person Beta", "rolle": "engineer", "standort": "nearshore", "stunden_je_woche": 10},
    {"name": "Person Gamma", "rolle": "tester", "standort": "nearshore", "stunden_je_woche": 3},
]}


@pytest.fixture()
def tenant_dir(tmp_path, monkeypatch):
    directory = tmp_path / "tenant"
    directory.mkdir()
    (directory / pkm.DATEINAME).write_text(yaml.safe_dump(_TENANT, allow_unicode=True), encoding="utf-8")
    (directory / staffing.DATEINAME).write_text(yaml.safe_dump(ROSTER, allow_unicode=True), encoding="utf-8")
    monkeypatch.setenv(pkm.ENV_DIR, str(directory))
    return directory


def _tree(path: Path) -> dict:
    return {item.relative_to(path).as_posix(): item.read_bytes() for item in sorted(path.rglob("*")) if item.is_file()}


def _baseline(tmp_path, **options):
    return reference_baseline(tmp_path / "work", canon=True, **options)


def test_names_are_put_against_the_canon_hours_without_writing(tmp_path, tenant_dir):
    repository, revision = _baseline(tmp_path)
    before = _tree(tmp_path / "work")
    result = staffing.compare_staffing(repository, PROJECT, revision, DECISION, "dev_prod")
    assert _tree(tmp_path / "work") == before
    assert result["status"] == "evaluated" and result["persist"] is False and result["personal_data"] is True
    engineers = {row["rate_class"]: row for row in result["alternative"]["classes"]}["engineer_nearshore"]
    assert engineers["hours"] == 26.0 and engineers["weekly_capacity"] == 30.0 and engineers["weeks"] == round(26 / 30, 2)
    assert {p["name"]: p["hours"] for p in engineers["people"]} == {"Person Alpha": round(26 * 20 / 30, 2), "Person Beta": round(26 * 10 / 30, 2)}
    assert engineers["earliest_full_team"] == "2026-10-05"
    testers = {row["rate_class"]: row for row in result["baseline"]["classes"]}["tester_nearshore"]
    assert testers["weeks"] == 3.0
    assert result["delta"]["weeks_in_parallel"] == {"before": 3.0, "after": 2.0}


def test_a_rate_class_without_a_person_is_a_gap(tmp_path, tenant_dir):
    repository, revision = _baseline(tmp_path)
    result = staffing.compare_staffing(repository, PROJECT, revision, DECISION, "dev_prod")
    assert [gap["rate_class"] for gap in result["alternative"]["gaps"]] == ["architekt_onshore"]
    assert "architekt_onshore" not in {row["rate_class"] for row in result["alternative"]["classes"]}


def test_roster_findings_name_the_row_not_the_person(tmp_path, tenant_dir):
    roster = copy.deepcopy(ROSTER)
    roster["personen"][1].update(rolle="designer", stunden_je_woche=80)
    (tenant_dir / staffing.DATEINAME).write_text(yaml.safe_dump(roster), encoding="utf-8")
    repository, revision = _baseline(tmp_path)
    result = staffing.compare_staffing(repository, PROJECT, revision, DECISION, "dev_prod")
    assert result["status"] == "findings" and result["personal_data"] is False
    assert any("Row 2" in item for item in result["findings"])
    assert "Person Beta" not in json.dumps(result)


def test_without_roster_or_tenant_nothing_is_shown(tmp_path, tenant_dir, monkeypatch):
    repository, revision = _baseline(tmp_path)
    (tenant_dir / staffing.DATEINAME).unlink()
    result = staffing.compare_staffing(repository, PROJECT, revision, DECISION, "dev_prod")
    assert result["status"] == "not_checked" and "baseline" not in result
    monkeypatch.delenv(pkm.ENV_DIR)
    assert staffing.compare_staffing(repository, PROJECT, revision, DECISION, "dev_prod")["status"] == "not_checked"


def test_blocked_alternative_is_refused(tmp_path, tenant_dir):
    repository, revision = _baseline(tmp_path, baseline="dev_prod")
    with pytest.raises(ValueError, match="blocked"):
        staffing.compare_staffing(repository, PROJECT, revision, DECISION, "dev_test_prod")
