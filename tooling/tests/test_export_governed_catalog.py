"""
test_export_governed_catalog.py — governed-truth export (KPI catalog + data contracts).

The exporter joins ALUCA's two governed-truth authorities into the portable
``meridian/governed-catalog/v1`` file the Meridian lineage drift check consumes:
measures from the KPI catalog, tables/columns from the data contracts (not just KPIs).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tooling.generator.export_governed_catalog import (
    build_governed_catalog, _load_measures, _load_tables,
)

REPO = Path(__file__).resolve().parents[2]


def test_build_catalog_has_both_authorities():
    cat = build_governed_catalog(REPO)
    assert cat["schema"] == "meridian/governed-catalog/v1"
    assert cat["measures"], "KPI catalog should yield measures"
    assert cat["tables"], "data contracts should yield tables"


def test_measures_carry_name_and_lineage():
    measures = _load_measures(REPO / "core" / "kpi_catalog" / "kpis")
    assert measures
    for m in measures:
        assert m["measure_name"]
        assert m["measure_name"] not in m["aliases"]          # measure_name excluded from aliases
    # lineage refs are non-empty table or table.column strings; at least some are table.column
    lineaged = [m for m in measures if m["lineage"]]
    all_refs = [ref for m in lineaged for ref in m["lineage"]]
    assert all_refs and all(ref.strip() for ref in all_refs)
    assert any("." in ref for ref in all_refs)                # table.column form is present


def test_tables_are_dimensions_and_facts_with_columns():
    tables = _load_tables(REPO / "core" / "data_contracts" / "domains")
    assert tables
    kinds = {t["kind"] for t in tables}
    assert kinds == {"dimension", "fact"}                     # both, not just KPIs
    fact_sales = [t for t in tables if t["name"] == "fact_sales"]
    assert fact_sales, "fact_sales should be present"
    assert "Net Sales Amount" in fact_sales[0]["columns"]
    assert fact_sales[0]["domain"] and fact_sales[0]["kind"] == "fact"


def test_deterministic_and_sorted():
    a = build_governed_catalog(REPO)
    b = build_governed_catalog(REPO)
    assert a == b
    assert [t["name"] for t in a["tables"]] == sorted(t["name"] for t in a["tables"])


def test_cli_writes_file(tmp_path):
    from tooling.generator.export_governed_catalog import main
    out = tmp_path / "gc.json"
    assert main(["--repo-root", str(REPO), "--out", str(out)]) == 0
    import json
    cat = json.loads(out.read_text(encoding="utf-8"))
    assert cat["measures"] and cat["tables"]


def test_tables_carry_showcase_and_column_specs():
    """A-23: additive fields — `columns` unchanged, `showcase` + `column_specs` alongside."""
    tables = _load_tables(REPO / "core" / "data_contracts" / "domains")
    allowed = {"name", "source_column", "type", "nullable", "ref", "unknown_member", "checks", "target_state"}
    for t in tables:
        assert isinstance(t["showcase"], bool)
        assert [s["name"] for s in t["column_specs"]] and sorted(s["name"] for s in t["column_specs"]) == t["columns"]
        for spec in t["column_specs"]:
            assert set(spec) <= allowed and "name" in spec
    by_name = {(t["domain"], t["name"]): t for t in tables}
    sales = by_name[("commercial_sales", "fact_sales")]
    assert sales["showcase"] is True
    promo_key = next(s for s in sales["column_specs"] if s["name"] == "PromoKey")
    assert promo_key == {"name": "PromoKey", "type": "int", "nullable": False, "ref": "dim_promo",
                         "unknown_member": -1}
    discount = next(s for s in sales["column_specs"] if s["name"] == "Discount Amount")
    assert discount["checks"] == [{"gte": 0, "when_present": True}]
    net = next(s for s in sales["column_specs"] if s["name"] == "Net Sales Amount")
    assert set(net) == {"name", "type"}                      # only keys the contract sets
    assert any(t["showcase"] is False for t in tables)       # e.g. fact_emissions
    assert any(s.get("target_state") for t in tables for s in t["column_specs"])
    units = next(s for s in sales["column_specs"] if s["name"] == "Sales Units")
    assert units["source_column"] == "Quantity"               # Modellname -> physische Gold-Spalte
    assert sales["domains"] == ["commercial_sales", "supply_chain"]


def test_one_entry_per_table_name():
    """Bus-Matrix (29.09.2026): a conformed table is defined once; references only add a domain.
    Measured before the change: 139 entries under 108 names, 8 names with differing specs.
    109 since 29.09.2026: fact_safety_incidents (incident grain) split off fact_safety."""
    tables = _load_tables(REPO / "core" / "data_contracts" / "domains")
    names = [t["name"] for t in tables]
    assert len(names) == len(set(names)) == 109
    by_name = {t["name"]: t for t in tables}
    for t in tables:
        assert t["domain"] in t["domains"] and t["domains"] == sorted(set(t["domains"]))
    assert len(by_name["dim_date"]["domains"]) == 12 and by_name["dim_date"]["domain"] == "commercial_sales"
    assert by_name["fact_nps"]["domain"] == "experience"
    assert by_name["fact_inventory"]["domain"] == "supply_chain"
    assert by_name["fact_safety"]["domain"] == "esg"
    assert by_name["fact_safety_incidents"]["domains"] == ["operations"]
    assert sum(len(t["domains"]) for t in tables) == 140       # Bus-Matrix: every use still listed (139 + fact_safety_incidents)


def test_conformed_reference_adds_domain_not_entry(tmp_path):
    (tmp_path / "a.yaml").write_text(
        "domain: a\n"
        "dimension:\n"
        "  - name: dim_x\n"
        "    columns:\n"
        "      - {name: XKey, type: int, role: key}\n"
        "      - {name: Label, type: text}\n",
        encoding="utf-8")
    (tmp_path / "b.yaml").write_text(
        "domain: b\n"
        "dimension:\n"
        "  - name: dim_x\n"
        "    conformed_from: a\n"
        "    uses_columns: [XKey]\n",
        encoding="utf-8")
    (t,) = _load_tables(tmp_path)
    assert (t["name"], t["domain"], t["domains"], t["columns"]) == ("dim_x", "a", ["a", "b"], ["Label", "XKey"])


def test_column_specs_from_synthetic_contract(tmp_path):
    (tmp_path / "d.yaml").write_text(
        "domain: d\n"
        "fact:\n"
        "  - name: fact_x\n"
        "    showcase: false\n"
        "    grain: row\n"
        "    columns:\n"
        "      - {name: A, type: int, agg: sum, description: x, checks: [{between: [0, 1]}]}\n"
        "      - {name: A, type: text}\n"
        "      - {name: B, type: int, ref: dim_y, nullable: false, unknown_member: -1, target_state: true}\n",
        encoding="utf-8")
    (t,) = _load_tables(tmp_path)
    assert t["showcase"] is False and t["columns"] == ["A", "B"]
    assert t["column_specs"] == [
        {"name": "A", "type": "int", "checks": [{"between": [0, 1]}]},       # first wins, extra keys dropped
        {"name": "B", "type": "int", "nullable": False, "ref": "dim_y", "unknown_member": -1, "target_state": True},
    ]
