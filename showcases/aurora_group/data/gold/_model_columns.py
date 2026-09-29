"""Spalten, die die Semantic Models lesen, die aber kein Basis-Generator erzeugt (A-24, 29.09.2026).

Entscheidung E8 (24.09.2026, `docs/plans/UMSETZUNGSPLAN_AGENTIC_LOOP.md`), Gruppen 3 und 4: das
Modell ist Vorgabe, der Gold-Generator ergaenzt die Spalten. Jede Funktion hier ist **rein und
deterministisch**: sie bekommt die fertige Tabelle (und, wo noetig, Nachbartabellen), haengt die
Spalte an und laesst jede vorhandene Spalte unveraendert. Sie verbraucht keinen globalen
Zufallsstrom -- ein Aufruf verschiebt also keine Werte, die ein Generator danach zieht.

Aufrufer:
  * `generate_finance_gold.py` (fact_cost), `generate_supply_chain_gold.py` (fact_inventory),
    `generate_gapfill_gold.py` (fact_procurement) vor dem Schreiben;
  * `generate_model_columns.py` fuer alle sieben Tabellen auf dem vorhandenen Gold -- auch fuer
    die Tabellen des Backbone-Generators (`core/data_contracts/sources/synthetic/
    generate_gold_layer_contract_v2.py`: dim_customer, dim_product, fact_action_log,
    fact_inventory_snapshot), der das ganze Gold neu schreibt und deshalb nicht erneut laeuft.

Was davon gemessen und was hergeleitet ist, steht je Funktion.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[4]

# --- ABC/XYZ-Schwellen -------------------------------------------------------------------------
# VORGELEGT, NICHT ENTSCHIEDEN (E8: "Schwellen werden vorgelegt"). ABC nach kumuliertem
# Nettoumsatzanteil (Pareto 80/95, Lehrbuchwert). XYZ nach **Rang** des Variationskoeffizienten
# der Monatsmenge: die absoluten Lehrbuchgrenzen (X <= 0,5, Y <= 1,0) liefern auf Aurora-Gold
# 4996 X, 0 Y, 0 Z (gemessen 29.09.2026, CoV 0,155-0,313), die Klasse waere also leer an Aussage.
ABC_GRENZEN = (0.80, 0.95)          # kumulierter Umsatzanteil bis A bzw. bis B
XYZ_RANGANTEILE = (0.50, 0.80)      # stabilste 50 % X, naechste 30 % Y, volatilste 20 % Z

# Kostenarten in fact_cost, die die Modellspalten tragen (Werte aus generate_finance_gold.py).
KOSTENART_MATERIAL = "Direct Material"
KOSTENART_GEMEINKOSTEN = "Manufacturing Overhead"


def _einheit(schluessel: str) -> float:
    """Stabile Zahl in [0, 1) aus einem Schluessel (SHA-256), unabhaengig von Reihenfolge und Seed."""
    return int(hashlib.sha256(schluessel.encode("utf-8")).hexdigest()[:15], 16) / float(16 ** 15)


# --- Finance ------------------------------------------------------------------------------------

def fact_cost_spalten(df: pd.DataFrame) -> pd.DataFrame:
    """`Material Cost Amount`/`Overhead Amount`: die Zeile traegt ihre COGS in genau einer
    Kostenart (`Cost Type`). Material = COGS der Zeilen mit Direct Material, Overhead = COGS der
    Zeilen mit Manufacturing Overhead, sonst 0. Damit gilt je Zeile Material + Overhead <= COGS
    und ueber jede Summe Material + Overhead + (Labor + Logistik) = COGS."""
    out = df.copy()
    cogs = out["COGS Amount"].astype("float64")
    art = out["Cost Type"].astype("object")
    out["Material Cost Amount"] = np.where(art == KOSTENART_MATERIAL, cogs, 0.0)
    out["Overhead Amount"] = np.where(art == KOSTENART_GEMEINKOSTEN, cogs, 0.0)
    return out


def fact_inventory_spalten(df: pd.DataFrame, fact_cogs: pd.DataFrame) -> pd.DataFrame:
    """`COGS Amount` (Finance-Sicht, fuer DIO): die COGS derselben Periode, Einheit und
    Produkt aus `fact_cogs`. Beide Tabellen schreibt `generate_supply_chain_gold.py` in derselben
    Koernung (Monatsende x OrgKey x ProductKey); fehlt ein Schluessel, bricht der Aufruf ab,
    statt eine Luecke still mit 0 zu fuellen."""
    keys = ["DateKey", "OrgKey", "ProductKey"]
    cogs = fact_cogs[keys + ["COGS Amount"]]
    if cogs.duplicated(keys).any():
        raise ValueError("fact_cogs ist auf DateKey/OrgKey/ProductKey nicht eindeutig")
    out = df.drop(columns=["COGS Amount"], errors="ignore")
    out = out.merge(cogs, on=keys, how="left", validate="many_to_one")
    fehlt = int(out["COGS Amount"].isna().sum())
    if fehlt:
        raise ValueError(f"{fehlt} Zeilen von fact_inventory ohne Partner in fact_cogs")
    return out


def dim_customer_spalten(df: pd.DataFrame, kauf_region: pd.DataFrame) -> pd.DataFrame:
    """`Region`: Heimatregion des Kunden. Aurora-Kunden tragen keine Adresse; die Region wird aus
    den eigenen Kaeufen gezogen -- je Kunde eine Region mit Wahrscheinlichkeit = sein Anteil der
    Kaufzeilen in Filialen dieser Region (`fact_sales` x `dim_org.Region`), Zufallszahl stabil aus
    der CustomerKey. Der Modus waere entartet: Kunden kaufen synthetisch ueberall, der Modus ergibt
    98,5 % DACH (gemessen 29.09.2026, 49.235 von 50.000).

    `kauf_region`: Spalten CustomerKey, Region, Anzahl (Kaufzeilen)."""
    kr = kauf_region.sort_values(["CustomerKey", "Region"]).copy()
    kr["anteil"] = kr["Anzahl"] / kr.groupby("CustomerKey")["Anzahl"].transform("sum")
    kr["kum"] = kr.groupby("CustomerKey")["anteil"].cumsum()
    u = kr["CustomerKey"].map(lambda k: _einheit(f"dim_customer.Region|{int(k)}"))
    wahl = kr[kr["kum"] > u].drop_duplicates("CustomerKey")[["CustomerKey", "Region"]]
    out = df.drop(columns=["Region"], errors="ignore").merge(wahl, on="CustomerKey", how="left")
    fehlt = int(out["Region"].isna().sum())
    if fehlt:
        raise ValueError(f"{fehlt} Kunden ohne Kaufzeile -- keine Region ableitbar")
    return out


# --- SupplyChain --------------------------------------------------------------------------------

def dim_product_spalten(df: pd.DataFrame, produkt_monat: pd.DataFrame, monate: list[int]) -> pd.DataFrame:
    """`ABC_Class`/`XYZ_Class` (E8 Gruppe 3: "aus Umsatz und Nachfrageschwankung").

    ABC: Nettoumsatz 2020-2024 je Produkt absteigend, kumulierter Anteil bis ABC_GRENZEN[0] = A,
    bis [1] = B, Rest C. XYZ: Variationskoeffizient (Standardabweichung/Mittel, Grundgesamtheit)
    der Monatsmenge ueber alle `monate` (Monate ohne Verkauf zaehlen als 0), aufsteigend gerankt,
    Anteile nach XYZ_RANGANTEILE. Produkte ohne Verkauf: C und Z (keine Nachfrage, nicht planbar).
    Gleichstaende loest die ProductKey auf.

    `produkt_monat`: Spalten ProductKey, Monat (YYYYMM), Menge, Umsatz."""
    pm = produkt_monat.groupby(["ProductKey", "Monat"], as_index=False)[["Menge", "Umsatz"]].sum()
    umsatz = pm.groupby("ProductKey")["Umsatz"].sum().reset_index()
    umsatz = umsatz.sort_values(["Umsatz", "ProductKey"], ascending=[False, True])
    # Klasse nach dem Anteil *vor* dem Produkt: das Produkt, das die Grenze ueberschreitet, zaehlt noch dazu.
    vorher = umsatz["Umsatz"].cumsum().shift(fill_value=0.0) / umsatz["Umsatz"].sum()
    umsatz["ABC_Class"] = np.select([vorher < ABC_GRENZEN[0], vorher < ABC_GRENZEN[1]], ["A", "B"], "C")

    breit = pm.pivot_table(index="ProductKey", columns="Monat", values="Menge", aggfunc="sum",
                           fill_value=0.0).reindex(columns=monate, fill_value=0.0)
    mittel = breit.mean(axis=1)
    cov = (breit.std(axis=1, ddof=0) / mittel).where(mittel > 0)
    xyz = cov.dropna().reset_index(name="cov").sort_values(["cov", "ProductKey"])
    rang = (np.arange(len(xyz)) + 1) / len(xyz)
    xyz["XYZ_Class"] = np.select([rang <= XYZ_RANGANTEILE[0], rang <= XYZ_RANGANTEILE[1]], ["X", "Y"], "Z")

    out = df.drop(columns=["ABC_Class", "XYZ_Class"], errors="ignore")
    out = out.merge(umsatz[["ProductKey", "ABC_Class"]], on="ProductKey", how="left")
    out = out.merge(xyz[["ProductKey", "XYZ_Class"]], on="ProductKey", how="left")
    out["ABC_Class"] = out["ABC_Class"].fillna("C")
    out["XYZ_Class"] = out["XYZ_Class"].fillna("Z")
    return out


def fact_procurement_spalten(df: pd.DataFrame) -> pd.DataFrame:
    """`Contract Unit Price`: der vereinbarte Stueckpreis der Lieferantenbeziehung. Im Generator
    ist das der Standardpreis je Lieferant (`Standard Unit Price Amount`, Basis der PPV). Er gilt
    nur fuer Vertragszeilen (`On-Contract Amount` > 0); eine Zeile ausserhalb des Vertrags hat
    keinen Vertragspreis und bleibt leer (NULL), statt einen Preis zu behaupten."""
    out = df.copy()
    auf_vertrag = out["On-Contract Amount"].astype("float64") > 0
    out["Contract Unit Price"] = out["Standard Unit Price Amount"].astype("float64").where(auf_vertrag)
    return out


# --- Operations ---------------------------------------------------------------------------------

def fact_inventory_snapshot_spalten(df: pd.DataFrame) -> pd.DataFrame:
    """`Reorder Flag`: Bestand hat den Sicherheitsbestand erreicht oder unterschritten
    (`Stock Qty` <= `Safety Stock Qty`). Einen Meldebestand mit Wiederbeschaffungszeit traegt
    Aurora-Gold nicht; der Sicherheitsbestand ist die einzige vorhandene Schwelle."""
    out = df.copy()
    out["Reorder Flag"] = out["Stock Qty"].astype("int64") <= out["Safety Stock Qty"].astype("int64")
    return out


# --- Experience ---------------------------------------------------------------------------------

def aktionscodes_je_use_case(repo: Path = REPO) -> dict[str, list[tuple[str, str]]]:
    """UseCaseID -> [(Action-Code-ID, owner_role)], aus `orchestration.action_code_ids` der
    UseCase_Bracket.yaml (SSOT) und `owner_role` der Action-Code-Datei. Referenziert, nicht neu
    definiert (Golden Thread)."""
    import yaml

    rollen: dict[str, str] = {}
    for f in sorted((repo / "core" / "action_codes").rglob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8"))
        if isinstance(d, dict) and d.get("id") and d.get("owner_role"):
            rollen[str(d["id"])] = str(d["owner_role"])
    out: dict[str, list[tuple[str, str]]] = {}
    for f in sorted((repo / "core" / "usecases").rglob("UseCase_Bracket.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        ids = (d.get("orchestration") or {}).get("action_code_ids") or []
        if d.get("id") and ids:
            fehlt = [i for i in ids if i not in rollen]
            if fehlt:
                raise ValueError(f"{d['id']}: Action Codes ohne Datei/owner_role: {fehlt}")
            out[str(d["id"])] = [(i, rollen[i]) for i in ids]
    return out


def fact_action_log_spalten(df: pd.DataFrame, codes: dict[str, list[tuple[str, str]]]) -> pd.DataFrame:
    """`Action Code`/`Responsible Role`: je Zeile einer der Action Codes, die der Use Case der
    Zeile in `orchestration.action_code_ids` fuehrt, gewaehlt stabil aus der ActionID;
    `Responsible Role` = `owner_role` dieses Action Codes."""
    out = df.drop(columns=["Action Code", "Responsible Role"], errors="ignore").copy()
    fehlt = sorted(set(out["UseCaseID"]) - set(codes))
    if fehlt:
        raise ValueError(f"UseCaseIDs ohne action_code_ids im Bracket: {fehlt}")

    def wahl(row) -> tuple[str, str]:
        liste = codes[row.UseCaseID]
        return liste[int(_einheit(f"fact_action_log|{row.ActionID}") * len(liste))]

    paare = [wahl(r) for r in out[["ActionID", "UseCaseID"]].itertuples(index=False)]
    out["Action Code"] = [p[0] for p in paare]
    out["Responsible Role"] = [p[1] for p in paare]
    return out
