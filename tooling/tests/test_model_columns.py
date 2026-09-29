"""Ableitungen der Modellspalten im Aurora-Gold (A-24, 29.09.2026).

`showcases/aurora_group/data/gold/_model_columns.py` ergaenzt die zehn Spalten, die die Semantic
Models lesen, aber kein Basis-Generator schreibt. Diese Tests halten die Regeln fest, die dort
behauptet werden: vorhandene Spalten bleiben unveraendert, gleiche Eingabe gibt gleiche Ausgabe,
Action Codes kommen aus den Brackets. Ob die Gold-Dateien die Spalten tragen, prueft
`test_gold_source.py::test_every_source_column_exists_in_gold_or_is_a_known_gap`.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "_model_columns", REPO / "showcases" / "aurora_group" / "data" / "gold" / "_model_columns.py")
mc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mc)


def test_fact_cost_splits_cogs_by_cost_type_without_touching_it():
    df = pd.DataFrame({"Cost Type": ["Direct Material", "Manufacturing Overhead", "Direct Labor"],
                       "COGS Amount": [100.0, 40.0, 25.0]})
    out = mc.fact_cost_spalten(df)
    assert out["COGS Amount"].tolist() == [100.0, 40.0, 25.0]
    assert out["Material Cost Amount"].tolist() == [100.0, 0.0, 0.0]
    assert out["Overhead Amount"].tolist() == [0.0, 40.0, 0.0]
    assert (out["Material Cost Amount"] + out["Overhead Amount"] <= out["COGS Amount"]).all()


def test_fact_inventory_takes_cogs_of_the_same_grain_and_refuses_gaps():
    keys = {"DateKey": [20240131, 20240131], "OrgKey": [1, 1], "ProductKey": [1, 2]}
    inv = pd.DataFrame({**keys, "Average Inventory Amount": [5.0, 6.0]})
    cogs = pd.DataFrame({**keys, "COGS Amount": [10.0, 20.0]})
    assert mc.fact_inventory_spalten(inv, cogs)["COGS Amount"].tolist() == [10.0, 20.0]
    with pytest.raises(ValueError, match="ohne Partner"):
        mc.fact_inventory_spalten(inv, cogs.iloc[:1])


def test_contract_price_only_on_contract_lines():
    df = pd.DataFrame({"On-Contract Amount": [50.0, 0.0], "Standard Unit Price Amount": [9.5, 9.5]})
    out = mc.fact_procurement_spalten(df)
    assert out["Contract Unit Price"].iloc[0] == 9.5 and pd.isna(out["Contract Unit Price"].iloc[1])


def test_reorder_flag_at_or_below_safety_stock():
    df = pd.DataFrame({"Stock Qty": [5, 10, 11], "Safety Stock Qty": [10, 10, 10]})
    assert mc.fact_inventory_snapshot_spalten(df)["Reorder Flag"].tolist() == [True, True, False]


def test_abc_xyz_by_revenue_and_demand_variation():
    monate = [202401, 202402, 202403, 202404]
    zeilen = []
    for pk, umsatz, mengen in [(1, 80.0, [10, 10, 10, 10]), (2, 15.0, [5, 15, 5, 15]),
                               (3, 4.0, [0, 20, 0, 0]), (4, 1.0, [1, 1, 1, 2])]:
        zeilen += [{"ProductKey": pk, "Monat": m, "Menge": q, "Umsatz": umsatz / 4}
                   for m, q in zip(monate, mengen)]
    dim = pd.DataFrame({"ProductKey": [1, 2, 3, 4, 5]})
    out = mc.dim_product_spalten(dim, pd.DataFrame(zeilen), monate).set_index("ProductKey")
    assert out["ABC_Class"].to_dict() == {1: "A", 2: "B", 3: "C", 4: "C", 5: "C"}
    assert out.loc[1, "XYZ_Class"] == "X" and out.loc[3, "XYZ_Class"] == "Z"
    assert out.loc[5, "XYZ_Class"] == "Z"                       # ohne Verkauf: nicht planbar


def test_customer_region_is_stable_and_one_of_the_bought_regions():
    kr = pd.DataFrame({"CustomerKey": [1, 1, 2], "Region": ["DACH", "CEE", "Nordics"], "Anzahl": [3, 1, 5]})
    dim = pd.DataFrame({"CustomerKey": [1, 2]})
    a = mc.dim_customer_spalten(dim, kr)
    assert a.equals(mc.dim_customer_spalten(dim, kr.sample(frac=1, random_state=1)))
    assert a.loc[a.CustomerKey == 2, "Region"].item() == "Nordics"
    assert a.loc[a.CustomerKey == 1, "Region"].item() in {"DACH", "CEE"}


def test_action_codes_come_from_the_brackets():
    codes = mc.aktionscodes_je_use_case()
    assert codes["SCM-001"][0][0] == "S-I1.1"
    df = pd.DataFrame({"ActionID": ["ACT1", "ACT2", "ACT3"], "UseCaseID": ["SCM-001", "OPS-001", "XD-001"]})
    out = mc.fact_action_log_spalten(df, codes)
    for uc, code, rolle in out[["UseCaseID", "Action Code", "Responsible Role"]].itertuples(index=False):
        assert (code, rolle) in codes[uc]
    assert out.equals(mc.fact_action_log_spalten(df, codes))
