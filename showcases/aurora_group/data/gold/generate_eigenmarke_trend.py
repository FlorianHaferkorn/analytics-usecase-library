"""Eigenmarken-Trend in Consumer Electronics: die letzten 12 Wochen des Datenstands (30.10.2026).

Entscheidung Florian 30.10.2026: die Showcase-Story „der Eigenmarkenanteil in einer Kategorie
sinkt seit 12 Wochen“ (Meridian-Mock, Action Code C-M2.3) entsteht im Generator, nicht in der
Auswahl der Eigenmarken-SKUs. Dieser Schritt verschiebt in `TREND_KATEGORIE` ab `TREND_START`
je Woche w (1..`TREND_WOCHEN`) den Anteil `TREND_RUECKGANG * w / TREND_WOCHEN` des
Eigenmarken-Umsatzes zur Fremdmarke:

* Eigenmarken-Zeilen: Faktor 1 - r(w).
* Fremdmarken-Zeilen derselben Kategorie, desselben Tags und derselben Filiale: gemeinsamer
  Faktor, der den frei gewordenen Umsatz aufnimmt. Die Kategoriesumme je Tag und Filiale bleibt
  damit gleich (Test). Gruppen ohne Fremdmarken-Zeile bleiben unveraendert.
* Skaliert werden die Zeilenbetraege `Net Sales Amount`, `Cost of Goods Sold Amount` und
  `Discount Amount` (Marge je Zeile bleibt prozentual gleich). Menge (Int64), Stueckpreise und
  Plan-/Vorjahreswerte bleiben: Plan und Vorjahr kennen die Verschiebung nicht. Der implizite
  Stueckpreis (`Net Sales Amount` / `Quantity`) weicht in den betroffenen Zeilen um bis zu
  `TREND_RUECKGANG` ab -- ANNAHME, ungeprueft, ob ein Modell-Measure das liest.

Rein und deterministisch (`eigenmarke_trend`); der Lauf schreibt nur die Partitionen ab
`TREND_START` neu und markiert den Commit (`COMMIT_MARKE`). Ein zweiter Lauf bricht ab, statt
den Rueckgang zu verdoppeln. Reihenfolge: nach `generate_model_columns.py --tabelle dim_product`
(braucht `Private Label Flag`). Das Flag kalibriert auf Jan-Sep 2024 und liegt damit vor dem
Trendfenster; ein erneuter Lauf von dim_product nach diesem Schritt aendert es nicht.

Run from repo root (braucht `deltalake`):
  python3 showcases/aurora_group/data/gold/generate_eigenmarke_trend.py
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

GOLD = Path(__file__).resolve().parent
FACT_SALES = GOLD / "facts" / "fact_sales"
DIM_PRODUCT = GOLD / "dimensions" / "dim_product"

TREND_KATEGORIE = "Consumer Electronics"
TREND_WOCHEN = 12
TREND_START = date(2024, 10, 9)          # 12 volle Wochen bis zum letzten Datentag 31.12.2024
# Rueckgang in der letzten Woche: 5 % des Eigenmarken-Umsatzes. Gewaehlt (30.10.2026, gemessen
# per Nachrechnung der C-M2.3-Logik auf den Daten), damit C-M2.3 L1 (-2 % gegen die Basis) im
# Dezember 2024 in CE feuert, L2 (-4 %) nicht. Keine Beobachtung, Showcase-Story.
TREND_RUECKGANG = 0.05
BETRAEGE = ("Net Sales Amount", "Cost of Goods Sold Amount", "Discount Amount")
COMMIT_MARKE = "aluca.eigenmarke_trend"


def woche(datekey: pd.Series, start: date = TREND_START) -> pd.Series:
    """Wochenindex 1..n ab `start` (0 davor)."""
    d = pd.to_datetime(datekey.astype("int64").astype(str), format="%Y%m%d")
    tage = (d - pd.Timestamp(start)).dt.days
    return np.where(tage >= 0, tage // 7 + 1, 0)


def eigenmarke_trend(df: pd.DataFrame, eigenmarke: set[int], kategorie: set[int],
                     start: date = TREND_START, wochen: int = TREND_WOCHEN,
                     rueckgang: float = TREND_RUECKGANG) -> pd.DataFrame:
    """fact_sales-Zeilen -> dieselben Zeilen mit verschobenen Betraegen (siehe Modulkopf).

    `eigenmarke`: ProductKeys mit Private Label Flag; `kategorie`: ProductKeys der Trendkategorie.
    Reihenfolge und alle uebrigen Spalten bleiben unveraendert."""
    out = df.copy()
    w = pd.Series(woche(out["DateKey"], start), index=out.index)
    im_fenster = out["ProductKey"].isin(kategorie) & (w >= 1) & (w <= wochen)
    if not im_fenster.any():
        return out
    pl = out["ProductKey"].isin(eigenmarke)
    r = (rueckgang * w / wochen).where(im_fenster, 0.0)
    ns = out["Net Sales Amount"].astype("float64")
    frei = (ns * r).where(im_fenster & pl, 0.0)
    marke = ns.where(im_fenster & ~pl, 0.0)
    gruppe = [out["DateKey"], out["OrgKey"]]
    frei_g = frei.groupby(gruppe).transform("sum")
    marke_g = marke.groupby(gruppe).transform("sum")
    hat_marke = marke_g != 0
    faktor = pd.Series(1.0, index=out.index)
    faktor = faktor.mask(im_fenster & pl & hat_marke, 1.0 - r)
    faktor = faktor.mask(im_fenster & ~pl & hat_marke, 1.0 + frei_g / marke_g.where(hat_marke, 1.0))
    betroffen = im_fenster & hat_marke
    for c in BETRAEGE:
        if c in out:
            out[c] = out[c].astype("float64")
            out.loc[betroffen, c] = (out.loc[betroffen, c] * faktor[betroffen]).round(2)
    # Rundung auf Cent: die Restdifferenz der Gruppe geht auf die groesste Fremdmarken-Zeile,
    # damit die Kategoriesumme je Tag und Filiale auf den Cent gleich bleibt.
    diff = (ns - out["Net Sales Amount"]).where(betroffen, 0.0)
    rest = diff.groupby(gruppe).transform("sum").round(2)
    kand = out.index[im_fenster & ~pl & hat_marke]
    if len(kand):
        k = out.loc[kand]
        groesste = k.assign(_ns=k["Net Sales Amount"]).sort_values(
            ["DateKey", "OrgKey", "_ns", "InvoiceLineID"], ascending=[True, True, False, True]
        ).drop_duplicates(["DateKey", "OrgKey"]).index
        out.loc[groesste, "Net Sales Amount"] = (out.loc[groesste, "Net Sales Amount"]
                                                 + rest.loc[groesste]).round(2)
    return out


def main() -> int:
    from deltalake import CommitProperties, DeltaTable, write_deltalake

    dt = DeltaTable(str(FACT_SALES))
    for h in dt.history():
        if COMMIT_MARKE in h or COMMIT_MARKE in str(h.get("userMetadata") or ""):
            print(f"Abbruch: {COMMIT_MARKE} ist schon angewandt (Version {h.get('version')})",
                  file=sys.stderr)
            return 1
    dim = DeltaTable(str(DIM_PRODUCT)).to_pandas()
    if "Private Label Flag" not in dim:
        print("Abbruch: dim_product ohne Private Label Flag -- erst generate_model_columns.py "
              "--tabelle dim_product", file=sys.stderr)
        return 1
    eigen = set(dim.loc[dim["Private Label Flag"].astype(bool), "ProductKey"].astype(int))
    kat = set(dim.loc[dim["Category"] == TREND_KATEGORIE, "ProductKey"].astype(int))
    teile = dt.metadata().partition_columns
    monate = sorted({(d.year, d.month) for d in
                     (TREND_START + timedelta(days=i) for i in range(TREND_WOCHEN * 7))})
    praedikat = " OR ".join(f'("Fiscal Year" = {y} AND "Fiscal Month" = {m})' for y, m in monate)
    alt = dt.to_pyarrow_table(filters=[[("Fiscal Year", "=", y), ("Fiscal Month", "=", m)]
                                       for y, m in monate])
    df = alt.to_pandas()
    neu = eigenmarke_trend(df, eigen, kat)
    import pyarrow as pa
    tabelle = pa.Table.from_pandas(neu, schema=alt.schema, preserve_index=False)
    write_deltalake(str(FACT_SALES), tabelle, mode="overwrite", predicate=praedikat,
                    partition_by=teile or None,
                    commit_properties=CommitProperties(custom_metadata={COMMIT_MARKE: "1"}))
    DeltaTable(str(FACT_SALES)).vacuum(retention_hours=0, enforce_retention_duration=False, dry_run=False)
    k = df["ProductKey"].isin(kat)
    print(f"  fact_sales {len(df):,} Zeilen in {len(monate)} Partitionen, davon {int(k.sum()):,} "
          f"{TREND_KATEGORIE}; Net Sales {df['Net Sales Amount'].sum():,.2f} -> "
          f"{neu['Net Sales Amount'].sum():,.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
