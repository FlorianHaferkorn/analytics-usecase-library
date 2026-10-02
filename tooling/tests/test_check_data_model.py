"""Guards for the data-model best-practice gate (tooling/validation/check_data_model.py).

Pure contract checks are tested hermetically with synthetic models; a smoke test asserts
the shipped ontology has zero hard findings (i.e. the model stays production-clean)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tooling" / "validation"))

import check_data_model as cdm


def _fact(name, grain="month", refs=None, keys=None, domain="d"):
    return {"domain": domain, "name": name, "grain": grain,
            "refs": refs or [], "keys": keys or [c for c, _ in (refs or [])]}


# --- MISSING-GRAIN ---------------------------------------------------------

def test_missing_grain_flagged():
    model = {"facts": [_fact("fact_a", grain=None)], "dims": []}
    out = cdm.check_grain(model)
    assert len(out) == 1 and "MISSING-GRAIN" in out[0]


def test_present_grain_clean():
    assert cdm.check_grain({"facts": [_fact("fact_a", grain="month")], "dims": []}) == []


# --- DANGLING-REF ----------------------------------------------------------

def test_dangling_ref_flagged():
    model = {"facts": [_fact("fact_a", refs=[("XKey", "dim_ghost")])],
             "dims": [{"domain": "d", "name": "dim_real", "key": "RealKey"}]}
    out = cdm.check_dangling_refs(model)
    assert len(out) == 1 and "dim_ghost" in out[0]


def test_resolvable_ref_clean():
    model = {"facts": [_fact("fact_a", refs=[("XKey", "dim_real")])],
             "dims": [{"domain": "d", "name": "dim_real", "key": "RealKey"}]}
    assert cdm.check_dangling_refs(model) == []


# --- NON-CONFORMED ---------------------------------------------------------

def test_nonconformed_dimension_flagged():
    # same dim name, different key column across two domains
    model = {"facts": [], "dims": [
        {"domain": "finance", "name": "dim_supplier", "key": "SupplierKey"},
        {"domain": "supply_chain", "name": "dim_supplier", "key": "VendorKey"}]}
    out = cdm.check_conformance(model)
    assert len(out) == 1 and "NON-CONFORMED" in out[0] and "dim_supplier" in out[0]


def test_conformed_dimension_clean():
    # same dim name, SAME key across domains (dim_date/dim_org pattern) → conformant
    model = {"facts": [], "dims": [
        {"domain": "a", "name": "dim_date", "key": "DateKey"},
        {"domain": "b", "name": "dim_date", "key": "DateKey"}]}
    assert cdm.check_conformance(model) == []


# --- parse ----------------------------------------------------------------

def test_parse_model_reads_facts_and_dims(tmp_path):
    (tmp_path / "x.yaml").write_text(
        "domain: x\n"
        "dimension:\n"
        "  - name: dim_thing\n"
        "    columns:\n"
        "      - {name: ThingKey, role: key}\n"
        "fact:\n"
        "  - name: fact_x\n"
        "    grain: month\n"
        "    columns:\n"
        "      - {name: ThingKey, ref: dim_thing}\n"
        "      - {name: Amount}\n", encoding="utf-8")
    model = cdm.parse_model(tmp_path)
    assert [d["name"] for d in model["dims"]] == ["dim_thing"]
    assert model["dims"][0]["key"] == "ThingKey"
    f = model["facts"][0]
    assert f["name"] == "fact_x" and f["grain"] == "month" and f["refs"] == [("ThingKey", "dim_thing")]


# --- integration smoke: the shipped ontology is production-clean ------------

# Meridian D-578 (29.09.2026): die Showdaten liegen nicht mehr in Git. Der Vertragsteil laeuft
# immer; der Gold-Teil (ORPHAN-FK) nur mit Daten, sonst „nicht gelaufen" im Skip-Grund.
from showcases.aurora_group.data import showdaten  # noqa: E402


def test_shipped_contracts_have_no_hard_findings():
    hard, _advisory = cdm.run(with_gold=False)
    assert hard == [], "data-model hard findings in the shipped contracts:\n" + "\n".join(hard)


@showdaten.pytest_markierung()
def test_shipped_model_has_no_hard_findings():
    hard, _advisory = cdm.run(with_gold=True)
    assert hard == [], "data-model hard findings in the shipped contracts:\n" + "\n".join(hard)


def test_missing_gold_is_not_run_not_green(tmp_path, monkeypatch, capsys):
    """Ohne Gold-Daten liefen ORPHAN-FK/DEGENERATE-KEY ueber nichts: Exit 2, nicht 0."""
    monkeypatch.setattr(cdm, "GOLD", tmp_path / "gold")
    monkeypatch.setattr(sys, "argv", ["check_data_model.py"])
    assert cdm.main() == 2
    assert "nicht gelaufen" in capsys.readouterr().out
    monkeypatch.setattr(sys, "argv", ["check_data_model.py", "--no-gold"])
    assert cdm.main() == 0
