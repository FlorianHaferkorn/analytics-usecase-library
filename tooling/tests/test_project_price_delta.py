"""WB-009: the private price delta sums what the mirrored core computes and writes nothing."""
import copy
import json
from pathlib import Path

import pytest
import yaml

from tooling.superversion import preis_kanon_mandant as pkm
from tooling.superversion.project_package import alternative_impact as impact
from tooling.superversion.project_package import price_delta
from tooling.tests.test_project_commercial_impact import _TENANT

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "tooling/generator/schemas"
PROJECT, DECISION = impact.REFERENCE_PROJECT, impact.REFERENCE_DECISION


def _write(directory: Path, tenant: dict) -> None:
    (directory / pkm.DATEINAME).write_text(yaml.safe_dump(tenant, allow_unicode=True), encoding="utf-8")


@pytest.fixture()
def tenant_dir(tmp_path, monkeypatch):
    directory = tmp_path / "tenant"
    directory.mkdir()
    _write(directory, _TENANT)
    monkeypatch.setenv(pkm.ENV_DIR, str(directory))
    return directory


def _tree(path: Path) -> dict:
    return {item.relative_to(path).as_posix(): item.read_bytes() for item in sorted(path.rglob("*")) if item.is_file()}


def _baseline(tmp_path, **options):
    return impact.build_reference_baseline(tmp_path / "work", SCHEMAS, canon=True, **options)


def _expected(tenant: dict, packages: dict[str, dict]) -> dict:
    core = pkm.rechenkern()
    totals = {"cost": 0.0, "price_calculated": 0.0, "price_rounded": 0.0, "list_price": 0.0}
    for package_ref, quantities in packages.items():
        sheet = core.kalkulation(tenant, core.paket(tenant, package_ref), quantities)
        totals["cost"] += sheet["selbstkosten"]
        totals["price_calculated"] += sheet["preis_kalkuliert"]
        totals["price_rounded"] += sheet["preis_gerundet"]
        totals["list_price"] += sheet["festpreis"] or 0.0
    return {key: round(value, 2) for key, value in totals.items()}


def test_delta_equals_the_core_per_side_and_nothing_is_written(tmp_path, tenant_dir):
    repository, revision = _baseline(tmp_path)
    before = _tree(tmp_path / "work")
    result = price_delta.compare_price(repository, PROJECT, revision, DECISION, "dev_prod")
    assert _tree(tmp_path / "work") == before
    assert result["status"] == "evaluated" and result["persist"] is False and result["price_values_embedded"] is True
    tenant = pkm.lade_mandant()
    by_side = {side: {row["package_ref"]: row["quantities"] for row in result[side]["packages"]} for side in ("baseline", "alternative")}
    assert by_side["baseline"]["REF_LANES"] == {"domaenen": 2.0, "umgebungen": 3.0}
    assert by_side["alternative"]["REF_LANES"] == {"domaenen": 2.0, "umgebungen": 2.0}
    for side in ("baseline", "alternative"):
        assert result[side]["totals"] == _expected(tenant, by_side[side])
        assert result[side]["unpriced"] == []
    for key in ("cost", "price_calculated", "price_rounded", "list_price"):
        assert result["delta"][key] == round(result["alternative"]["totals"][key] - result["baseline"]["totals"][key], 2)
    assert result["delta"]["cost"] < 0 and result["comparable"] is True


def test_output_is_deterministic_and_names_the_tenant_state(tmp_path, tenant_dir):
    repository, revision = _baseline(tmp_path)
    first = price_delta.compare_price(repository, PROJECT, revision, DECISION, "dev_prod")
    second = price_delta.compare_price(repository, PROJECT, revision, DECISION, "dev_prod")
    assert first == second
    from tooling.superversion.project_package.hashes import canonical_sha256
    assert first["tenant_fingerprint_sha256"] == canonical_sha256(pkm.lade_mandant())


def test_no_tenant_or_findings_return_no_money(tmp_path, tenant_dir, monkeypatch):
    repository, revision = _baseline(tmp_path)
    broken = copy.deepcopy(_TENANT)
    broken["mandanten"]["nagarro"]["satzklassen"]["tester_nearshore"]["kostensatz_eur_h"] = "<satz>"
    _write(tenant_dir, broken)
    result = price_delta.compare_price(repository, PROJECT, revision, DECISION, "dev_prod")
    assert result["status"] == "tenant_findings" and result["price_values_embedded"] is False and "delta" not in result
    no_auslastung = copy.deepcopy(_TENANT)
    del no_auslastung["mandanten"]["nagarro"]["auslastung"]
    _write(tenant_dir, no_auslastung)
    result = price_delta.compare_price(repository, PROJECT, revision, DECISION, "dev_prod")
    assert result["status"] == "tenant_findings" and any("auslastung" in item for item in result["findings"])
    monkeypatch.delenv(pkm.ENV_DIR)
    result = price_delta.compare_price(repository, PROJECT, revision, DECISION, "dev_prod")
    assert result["status"] == "not_checked" and "baseline" not in result


def _tm_tenant(tenant_dir, **kalkulation):
    tenant = copy.deepcopy(_TENANT)
    sources = tenant["mandanten"]["nagarro"]["pakete"]["REF_SOURCES"]
    sources["abrechnung"] = "tm"
    del sources["festpreis"]
    sources.setdefault("kalkulation", {}).update(kalkulation)
    _write(tenant_dir, tenant)
    return tenant


def test_time_and_material_is_a_band_from_the_core_not_a_total(tmp_path, tenant_dir):
    _tm_tenant(tenant_dir)
    repository, revision = _baseline(tmp_path)
    result = price_delta.compare_price(repository, PROJECT, revision, DECISION, "dev_prod")
    assert result["status"] == "evaluated" and result["comparable"] is True
    tenant, core = pkm.lade_mandant(), pkm.rechenkern()
    for side in ("baseline", "alternative"):
        assert result[side]["unpriced"] == []
        assert {row["package_ref"] for row in result[side]["packages"]} == {"REF_LANES"}
        (row,) = result[side]["time_and_material"]
        sheet = core.kalkulation(tenant, core.paket(tenant, "REF_SOURCES"), row["quantities"])
        assert row["work_package_ref"] == "wp_source_contracts"
        assert row["price_band"] == [round(v, 2) for v in sheet["preisband"]]
        assert row["price_band"][0] <= row["price_band"][1] and row["blended_rate"] > 0
        assert row["rate_mix_source"] == "Aufgabenstunden je Satzklasse (D-576)"
        assert result[side]["time_and_material_price_band"] == row["price_band"]
        assert result[side]["totals"] == _expected(tenant, {"REF_LANES": next(r["quantities"] for r in result[side]["packages"])})
    band = result["delta"]["time_and_material_price_band"]
    assert band == [round(result["alternative"]["time_and_material_price_band"][i] - result["baseline"]["time_and_material_price_band"][i], 2) for i in (0, 1)]


def test_time_and_material_mix_from_the_package_wins(tmp_path, tenant_dir):
    _tm_tenant(tenant_dir, satzklassen_anteil={"engineer_nearshore": 1.0})
    repository, revision = _baseline(tmp_path)
    result = price_delta.compare_price(repository, PROJECT, revision, DECISION, "dev_prod")
    (row,) = result["baseline"]["time_and_material"]
    assert row["rate_mix"] == {"engineer_nearshore": 1.0} and row["rate_mix_source"] == "Paket: satzklassen_anteil"
    assert row["blended_rate"] == pytest.approx(pkm.rechenkern().verkaufssatz(pkm.lade_mandant(), "engineer_nearshore"), abs=0.01)


def test_blocked_alternative_is_refused(tmp_path, tenant_dir):
    repository, revision = _baseline(tmp_path, baseline="dev_prod")
    with pytest.raises(ValueError, match="blocked"):
        price_delta.compare_price(repository, PROJECT, revision, DECISION, "dev_test_prod")


def test_rate_free_comparison_stays_rate_free(tmp_path, tenant_dir):
    """The money lives in this module only; the persistable comparison is unchanged."""
    from tooling.superversion.project_package import commercial_impact as commercial
    repository, revision = _baseline(tmp_path)
    text = json.dumps(commercial.compare_commercial(repository, PROJECT, revision, DECISION, "dev_prod"))
    for value in ("selbstkosten", "price_rounded", "list_price", "cost"):
        assert f'"{value}"' not in text


def test_cli_returns_json_errors(monkeypatch, capsys):
    import io
    import sys as _sys
    monkeypatch.setattr(_sys, "argv", ["x", "--repository", "r", "--schemas", "s"])
    monkeypatch.setattr(_sys, "stdin", io.StringIO(json.dumps({"project_ref": "p", "revision_hash": "HEAD", "decision_ref": "d", "option_ref": "o"})))
    assert price_delta.main() == 1
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False and out["status"] == 409
