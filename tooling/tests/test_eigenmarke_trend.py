"""Eigenmarken-Trend im Aurora-Gold (30.10.2026, Entscheidung Florian).

`showcases/aurora_group/data/gold/generate_eigenmarke_trend.py` verschiebt in der Trendkategorie
ueber die letzten 12 Wochen Umsatz von der Eigenmarke zur Fremdmarke. Die Tests halten fest:
Kategoriesumme je Tag und Filiale bleibt auf den Cent, Eigenmarke faellt um r(w), ausserhalb von
Fenster und Kategorie aendert sich nichts, gleiche Eingabe gibt gleiche Ausgabe.
"""
from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "generate_eigenmarke_trend",
    REPO / "showcases" / "aurora_group" / "data" / "gold" / "generate_eigenmarke_trend.py")
tr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tr)

START = date(2024, 10, 9)


def _zeilen() -> pd.DataFrame:
    rows, i = [], 0
    for dk in (20241001, 20241009, 20241231):          # vor dem Fenster, Woche 1, Woche 12
        for org in (1, 2):
            for pk, ns in ((1, 100.0), (2, 300.0), (3, 50.0), (9, 70.0)):
                i += 1
                rows.append({"InvoiceLineID": f"L{i:03d}", "DateKey": dk, "OrgKey": org,
                             "ProductKey": pk, "Quantity": 2, "Net Sales Amount": ns,
                             "Cost of Goods Sold Amount": ns * 0.6, "Discount Amount": ns * 0.1})
    # Gruppe nur mit Eigenmarke: bleibt unveraendert
    rows.append({"InvoiceLineID": "L999", "DateKey": 20241231, "OrgKey": 3, "ProductKey": 1,
                 "Quantity": 1, "Net Sales Amount": 40.0, "Cost of Goods Sold Amount": 24.0,
                 "Discount Amount": 4.0})
    return pd.DataFrame(rows)


def test_category_sum_per_day_and_store_is_constant_and_own_brand_falls():
    df = _zeilen()
    out = tr.eigenmarke_trend(df, eigenmarke={1}, kategorie={1, 2, 3}, start=START, wochen=12,
                              rueckgang=0.05)
    kat = df["ProductKey"].isin({1, 2, 3})
    vor = df[kat].groupby(["DateKey", "OrgKey"])["Net Sales Amount"].sum().round(2)
    nach = out[kat].groupby(["DateKey", "OrgKey"])["Net Sales Amount"].sum().round(2)
    assert vor.equals(nach)
    def pl(d, dk):
        return d.loc[(d.DateKey == dk) & (d.OrgKey == 1) & (d.ProductKey == 1), "Net Sales Amount"].item()

    assert pl(out, 20241001) == 100.0                      # vor dem Fenster
    assert pl(out, 20241009) == round(100 * (1 - 0.05 / 12), 2)   # Woche 1
    assert pl(out, 20241231) == round(100 * (1 - 0.05), 2)        # Woche 12
    # andere Kategorie (ProductKey 9) und Gruppe ohne Fremdmarke unveraendert
    assert out.loc[out.ProductKey == 9, "Net Sales Amount"].tolist() == [70.0] * 6
    assert out.loc[out.InvoiceLineID == "L999", "Net Sales Amount"].item() == 40.0
    # Marge je Zeile prozentual gleich, Menge unveraendert, Reihenfolge gleich
    assert ((out["Cost of Goods Sold Amount"] / out["Net Sales Amount"]) - 0.6).abs().max() < 1e-3  # Cent-Rundung
    assert out["Quantity"].tolist() == df["Quantity"].tolist()
    assert out["InvoiceLineID"].tolist() == df["InvoiceLineID"].tolist()


def test_trend_is_deterministic_and_independent_of_row_order():
    df = _zeilen()
    a = tr.eigenmarke_trend(df, {1}, {1, 2, 3}, START)
    b = tr.eigenmarke_trend(df.sample(frac=1, random_state=7), {1}, {1, 2, 3}, START)
    assert a.equals(tr.eigenmarke_trend(df, {1}, {1, 2, 3}, START))
    assert b.set_index("InvoiceLineID").sort_index().equals(a.set_index("InvoiceLineID").sort_index())


def test_window_matches_the_last_twelve_weeks_of_the_data():
    assert tr.TREND_START == date(2024, 10, 9) and tr.TREND_WOCHEN == 12
    assert tr.woche(pd.Series([20241008, 20241009, 20241231])).tolist() == [0, 1, 12]
