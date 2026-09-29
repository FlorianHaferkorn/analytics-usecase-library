"""Ergaenzt auf dem vorhandenen Aurora-Gold die Spalten, die die Semantic Models lesen (A-24).

Schreibt **nur** die genannten Tabellen neu, und in ihnen nur die Modellspalten: jede vorhandene
Spalte wird aus der Delta-Tabelle gelesen und unveraendert (gleiche Zeilen, gleiche Reihenfolge,
gleicher Typ) zurueckgeschrieben; der Lauf bricht ab, wenn das nicht stimmt. Die Ableitungen stehen
in `_model_columns.py`. Danach VACUUM (Aufbewahrung 0) je geschriebener Tabelle, damit der
Arbeitsbaum nur die aktiven Dateien traegt.

Warum ein eigener Schritt statt Neulauf: dim_customer, dim_product, fact_action_log und
fact_inventory_snapshot schreibt der Backbone-Generator (`core/data_contracts/sources/synthetic/
generate_gold_layer_contract_v2.py`) zusammen mit allen uebrigen Tabellen; ein Neulauf wuerde
fact_sales & Co. mitziehen. Nach einem Backbone-Lauf diesen Schritt erneut ausfuehren
(`generate_aurora_gold.py --domain model_columns` tut es, `all` am Ende ebenfalls).

Run from repo root (braucht `deltalake`, `pyyaml`):
  python3 showcases/aurora_group/data/gold/generate_model_columns.py
  python3 showcases/aurora_group/data/gold/generate_model_columns.py --tabelle fact_cost,dim_product
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

GOLD = Path(__file__).resolve().parent
if str(GOLD) not in sys.path:
    sys.path.insert(0, str(GOLD))

import _model_columns as mc  # noqa: E402
from _generator_utils import FACTS_END, FACTS_START  # noqa: E402

DIMS = GOLD / "dimensions"
FACTS = GOLD / "facts"

# Tabelle -> (Ordner, neue Spalten)
TABELLEN = {
    "dim_customer": (DIMS / "dim_customer", ["Region"]),
    "dim_product": (DIMS / "dim_product", ["ABC_Class", "XYZ_Class"]),
    "fact_cost": (FACTS / "fact_cost", ["Material Cost Amount", "Overhead Amount"]),
    "fact_inventory": (FACTS / "fact_inventory", ["COGS Amount"]),
    "fact_procurement": (FACTS / "fact_procurement", ["Contract Unit Price"]),
    "fact_action_log": (FACTS / "fact_action_log", ["Action Code", "Responsible Role"]),
    "fact_inventory_snapshot": (FACTS / "fact_inventory_snapshot", ["Reorder Flag"]),
}


def _delta(pfad: Path):
    from deltalake import DeltaTable
    return DeltaTable(str(pfad))


def _lesen(pfad: Path) -> pd.DataFrame:
    return _delta(pfad).to_pandas()


def _fact_sales_dateien() -> list[str]:
    return sorted(_delta(FACTS / "fact_sales").file_uris())


def _produkt_monat() -> pd.DataFrame:
    """fact_sales je Datei gelesen (28,7 Mio. Zeilen nie ganz im Speicher)."""
    teile = []
    for f in _fact_sales_dateien():
        x = pq.read_table(f, columns=["DateKey", "ProductKey", "Quantity", "Net Sales Amount"]).to_pandas()
        x["Monat"] = x["DateKey"] // 100
        teile.append(x.groupby(["ProductKey", "Monat"], as_index=False)
                      .agg(Menge=("Quantity", "sum"), Umsatz=("Net Sales Amount", "sum")))
    return pd.concat(teile, ignore_index=True)


def _kauf_region() -> pd.DataFrame:
    org = _lesen(DIMS / "dim_org")[["OrgKey", "Region"]]
    teile = []
    for f in _fact_sales_dateien():
        x = pq.read_table(f, columns=["CustomerKey", "OrgKey"]).to_pandas()
        teile.append(x.groupby(["CustomerKey", "OrgKey"]).size().rename("Anzahl").reset_index())
    k = pd.concat(teile, ignore_index=True).merge(org, on="OrgKey", how="left")
    if k["Region"].isna().any():
        raise ValueError("fact_sales-Zeilen an einer Org ohne Region")
    return k.groupby(["CustomerKey", "Region"], as_index=False)["Anzahl"].sum()


def _monate() -> list[int]:
    return [int(d.strftime("%Y%m")) for d in pd.date_range(FACTS_START, FACTS_END, freq="MS")]


def ableiten(name: str, df: pd.DataFrame) -> pd.DataFrame:
    if name == "dim_customer":
        return mc.dim_customer_spalten(df, _kauf_region())
    if name == "dim_product":
        return mc.dim_product_spalten(df, _produkt_monat(), _monate())
    if name == "fact_cost":
        return mc.fact_cost_spalten(df)
    if name == "fact_inventory":
        return mc.fact_inventory_spalten(df, _lesen(FACTS / "fact_cogs"))
    if name == "fact_procurement":
        return mc.fact_procurement_spalten(df)
    if name == "fact_action_log":
        return mc.fact_action_log_spalten(df, mc.aktionscodes_je_use_case())
    if name == "fact_inventory_snapshot":
        return mc.fact_inventory_snapshot_spalten(df)
    raise KeyError(name)


def ergaenzen(name: str) -> None:
    from deltalake import write_deltalake

    pfad, neu = TABELLEN[name]
    dt = _delta(pfad)
    teile = list(dt.metadata().partition_columns)
    alt = dt.to_pyarrow_table()
    basis = alt.drop_columns([c for c in neu if c in alt.column_names])
    df = basis.to_pandas()
    erg = ableiten(name, df)
    if len(erg) != len(df):
        raise ValueError(f"{name}: Zeilenzahl {len(df)} -> {len(erg)}")
    for c in df.columns:  # vorhandene Spalten: gleiche Werte in gleicher Reihenfolge
        if not erg[c].reset_index(drop=True).equals(df[c].reset_index(drop=True)):
            raise ValueError(f"{name}: vorhandene Spalte {c!r} wuerde sich aendern")
    tabelle = basis
    for c in neu:
        tabelle = tabelle.append_column(c, pa.array(erg[c].tolist(), from_pandas=True))
    write_deltalake(str(pfad), tabelle, mode="overwrite", schema_mode="overwrite",
                    partition_by=teile or None)
    _delta(pfad).vacuum(retention_hours=0, enforce_retention_duration=False, dry_run=False)
    werte = {c: round(float(erg[c].sum()), 2)
             if pd.api.types.is_float_dtype(erg[c]) else erg[c].value_counts(dropna=False).head(6).to_dict()
             for c in neu}
    print(f"  {name:24s} {len(erg):>9,} Zeilen  + {neu}  {werte}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tabelle", default="all",
                    help=f"Komma-getrennt aus {sorted(TABELLEN)} oder 'all' (Standard).")
    args = ap.parse_args()
    wahl = sorted(TABELLEN) if args.tabelle == "all" else [t.strip() for t in args.tabelle.split(",")]
    unbekannt = sorted(set(wahl) - set(TABELLEN))
    if unbekannt:
        ap.error(f"unbekannte Tabelle(n): {unbekannt}")
    print("Modellspalten ergaenzen (A-24) …")
    for name in wahl:
        ergaenzen(name)


if __name__ == "__main__":
    main()
