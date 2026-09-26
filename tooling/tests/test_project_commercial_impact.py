"""WB-009 first increment: the WB-008 decision delta through the mirrored price canon, rate-free."""
import copy
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from tooling.superversion import preis_kanon_mandant as pkm
from tooling.superversion.project_package import alternative_impact as impact
from tooling.superversion.project_package import commercial_impact as commercial

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "tooling/generator/schemas"
PROJECT, DECISION = impact.REFERENCE_PROJECT, impact.REFERENCE_DECISION
STATUS = {"status": "ANNAHME, ungeprueft", "herkunft": "Testwert"}

#: Invented values written outside the repository at test time. The distinctive rates and
#: prices are checked for absence in the output below.
_TENANT = {"mandanten": {"nagarro": {
    "name": "Testmandant", "waehrung": "EUR", "rundung_eur": 50,
    "marge_m": {"wert": 0.25, **STATUS}, "risikozuschlag_r": {"festpreis": 0.10, "tm": 0, **STATUS},
    "rollen": ["architekt", "engineer", "tester"], "standorte": ["onshore", "nearshore"],
    "satzklassen": {
        "architekt_onshore": {"rolle": "architekt", "standort": "onshore", "kostenband": "B", "kostensatz_eur_h": 123.45, **STATUS},
        "engineer_nearshore": {"rolle": "engineer", "standort": "nearshore", "kostenband": "C", "kostensatz_eur_h": 67.89, **STATUS},
        "tester_nearshore": {"rolle": "tester", "standort": "nearshore", "kostenband": "C", "kostensatz_eur_h": 54.32, **STATUS},
    },
    "verfuegbarkeit": {role: {"koepfe": 1, "fakturierbare_stunden_je_tag": 8, "fakturierbare_tage_je_woche": 4,
                              "arbeitstage_je_woche": 5, "arbeitswochen_je_jahr": 44} for role in ("architekt", "engineer", "tester")},
    "pakete": {
        "REF_LANES": {"name": "Umgebungsstrecken", "sales_code": "REF_LANES", "dod_paket": None, "tier": 2,
                      "kalkulation": {**STATUS, "mengentreiber": {"umgebungen": {"menge_default": 1, "einheit": "Umgebung"},
                                                                  "domaenen": {"menge_default": 1, "einheit": "Domaene"}},
                                      "beteiligung": {"architekt": 20, "engineer": 50, "tester": 30},
                                      "aufgaben": [{"name": "Zuschnitt", "klasse": "architekt_onshore", "stunden": 8},
                                                   {"name": "Strecke je Umgebung", "klasse": "engineer_nearshore", "stunden_je": 4, "treiber": "umgebungen"},
                                                   {"name": "Abnahme je Umgebung", "klasse": "tester_nearshore", "stunden_je": 3, "treiber": "umgebungen"}]},
                      "festpreis": {"grund_eur": 4321},
                      "lieferzeit": {"band_at": [3, 5], "je_einheit_at": {"umgebungen": 1}, "status": "ANNAHME, ungeprueft"}},
        "REF_SOURCES": {"name": "Quellvertraege", "sales_code": "REF_SOURCES", "dod_paket": None, "tier": 2,
                        "kalkulation": {**STATUS, "mengentreiber": {"quellobjekte": {"menge_default": 1, "einheit": "Objekt"}},
                                        "beteiligung": {"engineer": 100},
                                        "aufgaben": [{"name": "Vertrag je Objekt", "klasse": "engineer_nearshore", "stunden_je": 2, "treiber": "quellobjekte"}]},
                        "festpreis": {"grund_eur": 8765},
                        "lieferzeit": {"band_at": [4, 6], "status": "ANNAHME, ungeprueft"}},
    },
}}}


@pytest.fixture()
def tenant_dir(tmp_path, monkeypatch):
    directory = tmp_path / "tenant"
    directory.mkdir()
    (directory / pkm.DATEINAME).write_text(yaml.safe_dump(_TENANT, allow_unicode=True), encoding="utf-8")
    monkeypatch.setenv(pkm.ENV_DIR, str(directory))
    return directory


def _tree(path: Path) -> dict:
    return {item.relative_to(path).as_posix(): item.read_bytes() for item in sorted(path.rglob("*")) if item.is_file()}


def _baseline(tmp_path, **options):
    return impact.build_reference_baseline(tmp_path / "work", SCHEMAS, canon=True, **options)


def test_decision_delta_changes_hours_bands_capacity_and_gaps_without_money(tmp_path, tenant_dir):
    repository, revision = _baseline(tmp_path)
    before = _tree(tmp_path / "work" / "repositories")
    result = commercial.compare_commercial(repository, PROJECT, revision, DECISION, "dev_prod")
    assert _tree(tmp_path / "work" / "repositories") == before
    assert result["status"] == "evaluated" and result["price_values_embedded"] is False
    assert result["baseline"]["hours_by_canon_role"] == {"architekt": 8.0, "engineer": 30.0, "tester": 9.0}
    assert result["alternative"]["hours_by_canon_role"] == {"architekt": 8.0, "engineer": 26.0, "tester": 6.0}
    assert result["delta"]["hours_by_canon_role"] == {"engineer": {"before": 30.0, "after": 26.0}, "tester": {"before": 9.0, "after": 6.0}}
    assert result["delta"]["hours_by_canon_class"]["tester_nearshore"] == {"before": 9.0, "after": 6.0}
    assert result["delta"]["window_workdays"] == {"before": {"parallel": 8.0, "serial": 14.0}, "after": {"parallel": 7.0, "serial": 13.0}}
    lanes = {row["work_package_ref"]: row for row in result["alternative"]["packages"]}["wp_environment_lanes"]
    assert lanes["quantities"] == {"domaenen": 2.0, "umgebungen": 2.0}
    assert lanes["quantity_provenance"]["umgebungen"] == "derived: selected_stage_count"
    assert lanes["delivery_band_workdays"] == [5.0, 7.0]
    assert result["delta"]["new_gaps"] == ["canon_role_without_plan_demand:tester"]
    assert "canon_role_without_plan_demand:architekt" in {gap["id"] for gap in result["baseline"]["gaps"]}


def test_numbers_come_from_the_mirrored_core(tmp_path, tenant_dir):
    repository, revision = _baseline(tmp_path)
    result = commercial.compare_commercial(repository, PROJECT, revision, DECISION, "dev_prod")
    tenant = pkm.lade_mandant()
    lanes = {row["work_package_ref"]: row for row in result["baseline"]["packages"]}["wp_environment_lanes"]
    quantities = {"umgebungen": 3.0, "domaenen": 2.0}
    assert lanes["hours_by_canon_role"] == pkm.stunden_je_rolle(tenant, "REF_LANES", quantities)
    assert tuple(lanes["delivery_band_workdays"]) == pkm.rechenkern().lieferzeit_band(pkm.rechenkern().paket(tenant, "REF_LANES"), quantities)
    assert lanes["person_days_by_role"] == [{key: row[key] for key in ("rolle", "beteiligung_pct", "tage_min", "tage_max", "herkunft")}
                                            for row in pkm.personentage(tenant, "REF_LANES", quantities)]


def test_no_rate_price_or_margin_leaves_the_adapter(tmp_path, tenant_dir):
    repository, revision = _baseline(tmp_path)
    text = json.dumps(commercial.compare_commercial(repository, PROJECT, revision, DECISION, "dev_prod"))
    for value in ("123.45", "67.89", "54.32", "4321", "8765", "kostensatz", "festpreis", "marge", "0.25"):
        assert value not in text
    commercial.assert_rate_free({"ok": [{"hours": 1}]})
    for bad in ({"preis": 1}, {"a": [{"kostensatz_eur_h": 1}]}, {"price_band": [1, 2]}, {"marge": 0.2}, {"price_values_embedded": True}):
        with pytest.raises(ValueError, match="rate or price|price_values_embedded"):
            commercial.assert_rate_free(bad)


def test_missing_tenant_directory_is_not_checked_never_zero(tmp_path, monkeypatch):
    monkeypatch.delenv(pkm.ENV_DIR, raising=False)
    repository, revision = _baseline(tmp_path)
    result = commercial.compare_commercial(repository, PROJECT, revision, DECISION, "dev_prod")
    assert result["status"] == "not_checked" and "baseline" not in result and "delta" not in result


def test_placeholder_values_are_findings_not_numbers(tmp_path, tenant_dir):
    tenant = copy.deepcopy(_TENANT)
    tenant["mandanten"]["nagarro"]["satzklassen"]["tester_nearshore"]["kostensatz_eur_h"] = "<satz>"
    (tenant_dir / pkm.DATEINAME).write_text(yaml.safe_dump(tenant, allow_unicode=True), encoding="utf-8")
    repository, revision = _baseline(tmp_path)
    result = commercial.compare_commercial(repository, PROJECT, revision, DECISION, "dev_prod")
    assert result["status"] == "tenant_findings" and any("Platzhalter" in item for item in result["findings"])
    assert "baseline" not in result


def test_blocked_alternative_is_refused(tmp_path, tenant_dir):
    repository, revision = _baseline(tmp_path, baseline="dev_prod")
    with pytest.raises(ValueError, match="blocked"):
        commercial.compare_commercial(repository, PROJECT, revision, DECISION, "dev_test_prod")


def test_unknown_canon_package_and_unmapped_work_package_are_gaps(tmp_path, tenant_dir):
    tenant = copy.deepcopy(_TENANT)
    del tenant["mandanten"]["nagarro"]["pakete"]["REF_SOURCES"]
    (tenant_dir / pkm.DATEINAME).write_text(yaml.safe_dump(tenant, allow_unicode=True), encoding="utf-8")
    repository, revision = _baseline(tmp_path)
    result = commercial.compare_commercial(repository, PROJECT, revision, DECISION, "dev_prod")
    assert "unknown_canon_package:wp_source_contracts" in {gap["id"] for gap in result["baseline"]["gaps"]}
    plain, plain_revision = impact.build_reference_baseline(tmp_path / "plain", SCHEMAS)
    result = commercial.compare_commercial(plain, PROJECT, plain_revision, DECISION, "dev_prod")
    ids = {gap["id"] for gap in result["baseline"]["gaps"]}
    assert "unmapped_work_package:wp_environment_lanes" in ids and "unmapped_plan_role:fabric_engineer" in ids
    assert result["baseline"]["hours_by_canon_role"] == {}


def test_plan_schema_accepts_rate_free_canon_links_only():
    schema = json.loads((SCHEMAS / "project_plan.schema.json").read_text(encoding="utf-8"))
    plan = impact._reference_plan("dev_test_prod", False, canon=True)
    assert not list(Draft202012Validator(schema).iter_errors(plan))
    for mutation in ({"value": 2, "provenance": "assumption", "derived_from": "selected_stage_count"},
                     {"value": 2, "provenance": "unknown"}, {"derived_from": "customer_rate"}, {"rate_eur": 90}):
        broken = copy.deepcopy(plan)
        broken["work_packages"][0]["canon"]["quantities"]["umgebungen"] = mutation
        assert list(Draft202012Validator(schema).iter_errors(broken)), mutation


def test_proposal_assumptions_are_rate_free_and_name_the_open_points(tmp_path, tenant_dir):
    repository, revision = _baseline(tmp_path)
    result = commercial.compare_commercial(repository, PROJECT, revision, DECISION, "dev_prod")
    text = commercial.render_proposal_assumptions(result, "alternative")
    assert text == commercial.render_proposal_assumptions(result, "alternative")
    assert "## Proposal assumptions (dev prod)" in text
    assert "- Quantity umgebungen: 2 (derived: selected_stage_count)" in text
    assert "- Delivery band: 5–7 workdays" in text
    assert "tester" in text and "no plan role that maps to it is demanded" in text
    for value in ("123.45", "67.89", "54.32", "4321", "8765", "engineer_nearshore", "kostensatz", "marge"):
        assert value not in text
    baseline = commercial.render_proposal_assumptions(result, "baseline")
    assert "- Quantity umgebungen: 3 (derived: selected_stage_count)" in baseline and "accepted baseline" in baseline


def test_proposal_assumptions_need_an_evaluated_result():
    with pytest.raises(ValueError, match="evaluated"):
        commercial.render_proposal_assumptions({"status": "not_checked"})


def test_released_revision_gets_a_rate_free_proposal_document(tmp_path, tenant_dir):
    repository, revision = _baseline(tmp_path)
    output = commercial.build_proposal_output(repository, PROJECT, revision)
    files = {row["path"]: row["content"] for row in output["files"]}
    assert set(files) == {"proposal-assumptions.md", "output-manifest.json"}
    assert "- Quantity umgebungen: 3 (derived: selected_stage_count)" in files["proposal-assumptions.md"]
    manifest = json.loads(files["output-manifest.json"])
    assert manifest["price_values_embedded"] is False and manifest["revision_hash"] == revision
    for value in ("123.45", "67.89", "54.32", "4321", "8765", "kostensatz"):
        assert value not in json.dumps(files)


def test_generation_runner_offers_the_document_only_on_request(tmp_path, tenant_dir):
    from tooling.superversion.project_package.automation import run_automation, read_automation
    repository, revision = _baseline(tmp_path)
    targets = {row["id"]: row for row in read_automation(repository, PROJECT, revision)["targets"]}
    assert targets["proposal_assumptions"]["status"] == "ready"
    run = run_automation(repository, PROJECT, revision, actor="synthetic_fixture_not_a_customer", confirm_generation=True,
                         targets=["proposal_assumptions"])
    assert run["report"]["targets"] == ["proposal_assumptions"]
    assert "proposal_assumptions/proposal-assumptions.md" in {row["path"] for row in run["files"]}


def test_proposal_document_refuses_without_canon_or_links(tmp_path, monkeypatch):
    monkeypatch.delenv(pkm.ENV_DIR, raising=False)
    repository, revision = _baseline(tmp_path)
    with pytest.raises(ValueError, match="not configured"):
        commercial.build_proposal_output(repository, PROJECT, revision)
    plain, plain_revision = impact.build_reference_baseline(tmp_path / "plain", SCHEMAS)
    with pytest.raises(ValueError, match="No work package links"):
        commercial.build_proposal_output(plain, PROJECT, plain_revision)
