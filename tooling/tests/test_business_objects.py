"""
test_business_objects.py — business-object layer (D-608, I-21 W4.6).

Guards, analogous to ``test_architecture_blueprint_schema.py``:
  - the schema is a valid JSON Schema (draft 2020-12);
  - the library layer ``core/business_objects/business_objects.yaml`` validates and passes the
    gates (Golden Thread, referential integrity, physical binding) — each gate with a counter-probe;
  - the file is exactly what the derivation writes (drift gate), ids stay stable, curated values
    survive a rewrite;
  - PARITY: the schema is a peer pair with Meridian ``meridian/core/schemas/business_object.schema.json``.
    Here: a pinned hash (LF-normalised) that must change together with the schema, plus a live
    byte comparison when a Meridian checkout is present ($MERIDIAN_ROOT or ../Freelancing).
    Meridian's ``scripts/check_aluca_mirror.py`` (PEER_PAIRS) compares from the other side.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tooling.generator import business_objects as bo

REPO = Path(__file__).resolve().parents[2]
MERIDIAN_REL = "meridian/core/schemas/business_object.schema.json"

#: sha256 of the LF-normalised schema. Change it only together with the Meridian peer file.
SCHEMA_SHA256 = "654e48c9765d77fa4d560d045d137e14454841a04730a6318a0143ed44fb2c23"


@pytest.fixture(scope="module")
def gates() -> tuple[set[str], dict[str, set[str]]]:
    return bo.catalog_kpi_ids(REPO), bo.physical_columns(REPO)


@pytest.fixture()
def doc() -> dict:
    d = bo.load(REPO)
    assert d is not None, f"{bo.DATA} missing"
    return copy.deepcopy(d)


def _check(doc, gates) -> list[str]:
    return bo.check(doc, *gates)


# ─── schema + parity ──────────────────────────────────────────────────────────

def test_schema_is_valid_jsonschema() -> None:
    Draft202012Validator.check_schema(json.loads(bo.SCHEMA.read_text(encoding="utf-8")))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_schema_hash_pin() -> None:
    assert _sha(bo.SCHEMA) == SCHEMA_SHA256, (
        "business_object.schema.json changed: it is a peer pair with Meridian "
        f"{MERIDIAN_REL} — change both files byte-identically, then update SCHEMA_SHA256")


def test_schema_byte_identical_with_meridian() -> None:
    env = os.environ.get("MERIDIAN_ROOT")
    root = Path(env).expanduser() if env else REPO.parent / "Freelancing"
    peer = root / MERIDIAN_REL
    if not peer.is_file():
        pytest.skip("no Meridian checkout with the peer schema — parity measured by the pin only")
    assert _sha(peer) == _sha(bo.SCHEMA)


# ─── the library layer passes every gate ──────────────────────────────────────

def test_library_layer_passes(doc, gates) -> None:
    assert _check(doc, gates) == []


@pytest.mark.parametrize("spoil", [
    lambda d: d["business_objects"][0].update(id="BO-COM-001"),
    lambda d: d["business_objects"][0].update(kind="event"),
    lambda d: d["business_objects"][0]["attributes"][0].update(personal_data=True),
    lambda d: d["business_objects"][0]["attributes"][0].update(personal_data_category="contact_data"),
    lambda d: d["business_objects"][0]["attributes"][0].update(type="text"),
    # pre-D-594 id syntax, deliberately not a mapped id (kpi_id_migration --check stays clean)
    lambda d: d["business_objects"][0].update(kpi_ids=["sales.example.amount"]),
    lambda d: d["business_objects"][0]["binding"].update(table="customers"),
])
def test_schema_counter_probes(doc, gates, spoil) -> None:
    spoil(doc)
    assert any(p.startswith("schema:") for p in _check(doc, gates))


def test_golden_thread_counter_probe(doc, gates) -> None:
    doc["business_objects"][0]["kpi_ids"].append("KPI-COM-999")
    assert any("KPI-COM-999 not in the catalog" in p for p in _check(doc, gates))


def test_relationship_target_counter_probe(doc, gates) -> None:
    src = next(o for o in doc["business_objects"] if o["relationships"])
    src["relationships"][0]["target"] = "BO-999"
    assert any("BO-999 does not exist" in p for p in _check(doc, gates))


def test_binding_counter_probe(doc, gates) -> None:
    doc["business_objects"][0]["attributes"][0]["column"] = "No Such Column"
    doc["business_objects"][1]["binding"]["table"] = "fact_no_such_table"
    found = "\n".join(_check(doc, gates))
    assert "'No Such Column' missing" in found and "fact_no_such_table" in found


# ─── second measurement: straight from the contracts and the catalog ─────────

def test_counts_against_the_sources(doc) -> None:
    import yaml

    defs, refs, lineage = {}, 0, {}
    for p in sorted((REPO / "core" / "data_contracts" / "domains").glob("*.yaml")):
        d = yaml.safe_load(p.read_text(encoding="utf-8"))
        for sec in ("dimension", "fact"):
            for t in d.get(sec) or []:
                if "conformed_from" not in t:
                    defs[t["name"]] = sec
                    refs += sum(1 for c in {c["name"]: c for c in t.get("columns") or []}.values()
                                if c.get("ref"))
    for p in (REPO / "core" / "kpi_catalog" / "kpis").glob("KPI-*.yaml"):
        k = yaml.safe_load(p.read_text(encoding="utf-8"))
        for lin in (k.get("technical") or {}).get("lineage") or []:
            lineage.setdefault(lin.split(".", 1)[0], set()).add(k["kpi_id"])
    objs = {o["binding"]["table"]: o for o in doc["business_objects"]}
    assert set(objs) == set(defs) and len(objs) == 109
    dims = {t for t, s in defs.items() if s == "dimension"}
    assert {t for t, o in objs.items() if o["kind"] == "master_data"} == dims
    assert sum(len(o["relationships"]) for o in objs.values()) == refs == 208
    for t, o in objs.items():
        assert set(o["kpi_ids"]) == lineage.get(t, set()), t
    # KPIs whose lineage names no governed table stay unbound — measured, not hidden
    bound = {k for o in objs.values() for k in o["kpi_ids"]}
    unbound = {k for t, ks in lineage.items() if t not in objs for k in ks} - bound
    assert unbound == {"KPI-FIN-008", "KPI-OPS-020"}      # fact_ar, fact_ops_changeover: no contract


def test_file_is_the_derivation(doc) -> None:
    assert bo.dump(bo.merge(bo.derive(REPO), doc)) == (REPO / bo.DATA).read_text(encoding="utf-8")
    assert bo.main(["--check"]) == 0


def test_gaps_are_counted(doc) -> None:
    g = bo.gaps(doc)
    attrs = sum(len(o["attributes"]) for o in doc["business_objects"])
    assert g["attribute.personal_data"] == attrs          # no source classifies personal data
    assert g["name.de"] == g["name.en"] == g["binding.layer"] == 109


# ─── stable ids, curated values ───────────────────────────────────────────────

def test_ids_stay_and_new_objects_get_the_next_number(doc, gates) -> None:
    existing = copy.deepcopy(doc)
    gone = existing["business_objects"].pop(0)
    shift = {o["id"]: f"BO-{int(o['id'][3:]) + 500:03d}" for o in existing["business_objects"]}
    for o in existing["business_objects"]:
        o["id"] = shift[o["id"]]
        for r in o["relationships"]:
            r["target"] = shift.get(r["target"], r["target"])
    new = bo.merge(bo.derive(REPO), existing)
    by_table = {o["binding"]["table"]: o["id"] for o in new["business_objects"]}
    for o in existing["business_objects"]:
        assert by_table[o["binding"]["table"]] == o["id"]
    assert by_table[gone["binding"]["table"]] == "BO-610"   # max 609 + 1
    assert _check(new, gates) == []


def test_curated_value_survives(doc) -> None:
    cust = next(o for o in doc["business_objects"] if o["binding"]["table"] == "dim_customer")
    cust["name"] = {"de": "Kunde", "en": "Customer"}
    cust["attributes"][2]["personal_data"] = True
    cust["attributes"][2]["personal_data_category"] = "identification_data"
    new = bo.merge(bo.derive(REPO), doc)
    got = next(o for o in new["business_objects"] if o["binding"]["table"] == "dim_customer")
    assert got["name"] == {"de": "Kunde", "en": "Customer"}
    assert got["attributes"][2]["personal_data_category"] == "identification_data"
