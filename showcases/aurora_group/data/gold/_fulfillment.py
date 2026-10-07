"""fact_fulfillment fuer die Aurora-Showcase: fachlich konsistent und mit der SCM-002-Story (07.10.2026).

Vorher (bis 06.10.2026) zog `generate_supply_chain_gold.py` die drei Flags unabhaengig per
`random()`: gemessen auf dem Release `showdaten-aurora-2026-09-29c` (DuckDB/pandas ueber die
aktiven Delta-Dateien) wichen 19,9 % der 8.751 Zeilen von `OTIF Flag = On-Time Flag AND In-Full
Flag` ab; ~5 Auftraege je Tag ueber 5 Lanes liessen keinen Lane/DC/Woche-Slot an den
Volume-Guardrail von S-R2.2 (>= 100 Sendungen, KPI-SCM-015) heran, und OrgKey 1-5 waren Konzern,
Region, Land und zwei Filialen statt des versendenden DC.

Regeln hier (Felder, von `tooling/tests/test_fulfillment.py` geprueft):

* `OTIF Flag` ist immer `On-Time Flag & In-Full Flag`.
* `OrgKey` ist der DC der Lane (`dim_lane.Origin` -> `dim_org.OrgCode`); Lane/DC/Woche ist damit
  die Koernung von S-R2.2 (`lane_dc_week`).
* `HAUPTLANES` tragen je ISO-Woche >= 100 Sendungen (Guardrail), die uebrigen Lanes bleiben
  darunter und loesen S-R2.2 deshalb nie aus.
* On-Time sinkt nur in `BETROFFENE_LANES` (linearer Abfall ab `ab` bis `FACTS_END`), In-Full
  bleibt je Lane konstant: On-Time ist der Treiber des OTIF-Rueckgangs.
* Die betroffenen Lanes fahren ueberwiegend eine Produktkategorie (`kategorie`), so dass auch die
  Kategorie-Sicht zwei Kategorien mit Ausfaellen zeigt (SCM-002 big_idea).
* Expedite: verspaetete Sendungen werden mit `EXPEDITE_QUOTE_SPAET` per Premiumfracht nachgezogen;
  in betroffenen Lanes kommt vorbeugende Premiumfracht im Verhaeltnis zum Abfall dazu
  (KPI-SCM-010 steigt dort). Penalty nur bei OTIF-Verfehlung.
* Deterministisch: eigener Generator `np.random.default_rng([seed, STROM])`, kein globaler
  Zufallsstrom.

Die Funktionen sind rein (Dateizugriff nur in `lies_tabelle`); `generate_fulfillment_gold.py` schreibt die
Tabelle auf vorhandenes Gold, `generate_supply_chain_gold.py` ruft `erzeuge` im Gesamtlauf.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd

from _generator_utils import apply_combined_seasonality

STROM = 2026_10_07          # fester Teilstrom fuer diese Tabelle (zusammen mit RANDOM_SEED)
GUARDRAIL = 100             # S-R2.2 minimum_data.volume_guardrail.value (KPI-SCM-015)
STUFEN = (("L3", 0.90), ("L2", 0.94), ("L1", 0.97))  # S-R2.2 trigger.levels, On-Time % < Wert
PERSISTENZ = 2              # S-R2.2 trigger.evaluation.persistence.min_consecutive_periods


@dataclass(frozen=True)
class Abfall:
    """On-Time-Abfall einer Lane: linear von 0 am Tag `ab` auf `tiefe` am Ende des Zeitraums."""
    ab: str
    tiefe: float
    kategorie: str


# LaneKey -> Abfall. LaneKey 12 = DC-AT-01 -> ES (Road), 22 = DC-CH-02 -> NO (Sea) im dim_lane
# des Releases 2026-09-29c (gleicher Seed, gleiche Lanes; `dim_lane` bleibt unveraendert).
BETROFFENE_LANES: dict[int, Abfall] = {
    12: Abfall(ab="2023-07-01", tiefe=0.115, kategorie="Consumer Electronics"),
    22: Abfall(ab="2023-10-01", tiefe=0.065, kategorie="Home & Living"),
}
# Lanes mit Guardrail-Volumen (>= 100 Sendungen je Woche). Die betroffenen gehoeren dazu.
HAUPTLANES: tuple[int, ...] = (1, 2, 5, 7, 8, 12, 14, 17, 20, 22, 23, 26, 28, 32)

WOCHE_HAUPT = (160.0, 230.0)    # Sendungen je Woche (vor Saison), gleichverteilt je Lane
WOCHE_NEBEN = (20.0, 60.0)
ON_TIME_BASIS = (0.982, 0.992)  # je Lane
IN_FULL_BASIS = (0.982, 0.990)  # je Lane, ohne Trend
PEAK_ABSCHLAG = 0.004           # On-Time-Abschlag in November/Dezember (Spitzenlast)
KATEGORIE_MIX = {"Fashion": 0.5, "Home & Living": 0.3, "Consumer Electronics": 0.2}
ANTEIL_HAUPTKATEGORIE = 0.7     # Anteil der Kategorie einer betroffenen Lane an ihren Sendungen
PRODUKTE_JE_KATEGORIE = 20
EXPEDITE_QUOTE_SPAET = 0.6
EXPEDITE_VORBEUGEND = 0.5       # vorbeugende Premiumfracht = Faktor x aktueller Abfall


def lies_tabelle(pfad) -> pd.DataFrame:
    """Delta-Tabelle (aktive Dateien laut `_delta_log`) oder Parquet-Ordner als DataFrame."""
    from pathlib import Path
    pfad = Path(pfad)
    if (pfad / "_delta_log").exists():
        from deltalake import DeltaTable
        return DeltaTable(str(pfad)).to_pandas()
    return pd.read_parquet(pfad)


def _abfall(lane: int, tage: pd.DatetimeIndex, ende: datetime) -> np.ndarray:
    a = BETROFFENE_LANES.get(lane)
    if a is None:
        return np.zeros(len(tage))
    start = pd.Timestamp(a.ab)
    anteil = ((tage - start).days / max((pd.Timestamp(ende) - start).days, 1)).to_numpy(float)
    return a.tiefe * np.clip(anteil, 0.0, 1.0)


def produktpool(produkte: pd.DataFrame) -> dict[str, np.ndarray]:
    """Je Kategorie die ersten `PRODUKTE_JE_KATEGORIE` aktiven ProductKeys (aufsteigend)."""
    p = produkte
    if "Lifecycle Status" in p.columns:
        p = p[p["Lifecycle Status"] == "Active"]
    pool = {}
    for kat in KATEGORIE_MIX:
        keys = np.sort(p.loc[p["Category"] == kat, "ProductKey"].astype(int).to_numpy())
        if len(keys) == 0:
            raise ValueError(f"dim_product hat keine aktiven Produkte der Kategorie {kat!r}")
        pool[kat] = keys[:PRODUKTE_JE_KATEGORIE]
    return pool


def lane_dc(lanes: pd.DataFrame, org: pd.DataFrame) -> dict[int, int]:
    """LaneKey -> OrgKey des Ursprungs-DC; bricht ab, wenn ein Ursprung in dim_org fehlt."""
    code = dict(zip(org["OrgCode"], org["OrgKey"].astype(int)))
    weg = sorted(set(lanes["Origin"]) - set(code))
    if weg:
        raise ValueError(f"dim_lane.Origin ohne dim_org.OrgCode: {weg}")
    return {int(k): int(code[o]) for k, o in zip(lanes["LaneKey"], lanes["Origin"])}


def erzeuge(lanes: pd.DataFrame, org: pd.DataFrame, produkte: pd.DataFrame,
            tage: pd.DatetimeIndex, seed: int) -> pd.DataFrame:
    """fact_fulfillment (Koernung Sendung) fuer `tage`; gleiche Eingabe -> gleiche Ausgabe."""
    fehlt = sorted((set(BETROFFENE_LANES) | set(HAUPTLANES)) - set(lanes["LaneKey"].astype(int)))
    if fehlt:
        raise ValueError(f"LaneKeys fehlen in dim_lane: {fehlt}")
    rng = np.random.default_rng([seed, STROM])
    dc = lane_dc(lanes, org)
    pool = produktpool(produkte)
    kats = list(KATEGORIE_MIX)
    tage = pd.DatetimeIndex(tage)
    ende = tage.max()
    saison = np.array([apply_combined_seasonality(d, 1.0, 0.6, 0.4, seed) for d in tage])
    # Wochentagsprofil ist im Mittel ~1; Tagesmittel = Wochenvolumen / 7 x Saison.
    peak = np.isin(tage.month, (11, 12))
    datekey = tage.strftime("%Y%m%d").astype(int).to_numpy()

    teile = []
    for lane in sorted(dc):                      # feste Reihenfolge -> feste Ziehungen
        haupt = lane in HAUPTLANES
        woche = rng.uniform(*(WOCHE_HAUPT if haupt else WOCHE_NEBEN))
        ot_basis = rng.uniform(*ON_TIME_BASIS)
        if_basis = rng.uniform(*IN_FULL_BASIS)
        n = rng.poisson(woche / 7.0 * saison)
        abf = _abfall(lane, tage, ende)
        p_ot = ot_basis - abf - PEAK_ABSCHLAG * peak
        idx = np.repeat(np.arange(len(tage)), n)
        m = len(idx)
        if m == 0:
            continue
        on_time = rng.random(m) < p_ot[idx]
        in_full = rng.random(m) < if_basis
        korrekt = rng.random(m) < 0.98
        a = BETROFFENE_LANES.get(lane)
        if a is None:
            gewichte = np.array([KATEGORIE_MIX[k] for k in kats])
        else:
            rest = 1.0 - ANTEIL_HAUPTKATEGORIE
            andere = {k: v for k, v in KATEGORIE_MIX.items() if k != a.kategorie}
            s = sum(andere.values())
            gewichte = np.array([ANTEIL_HAUPTKATEGORIE if k == a.kategorie else rest * andere[k] / s
                                 for k in kats])
        kat_idx = rng.choice(len(kats), size=m, p=gewichte)
        prod = np.empty(m, dtype=np.int64)
        for i, k in enumerate(kats):
            sel = kat_idx == i
            prod[sel] = rng.choice(pool[k], size=int(sel.sum()))
        menge = np.maximum(10, (100 * saison[idx] * rng.uniform(0.7, 1.3, m)).astype(int))
        otif = on_time & in_full
        penalty = np.where(otif, 0.0, rng.uniform(100, 500, m))
        u_exp = rng.random(m)
        exp_spaet = ~on_time & (u_exp < EXPEDITE_QUOTE_SPAET)
        exp_vorb = on_time & (u_exp < EXPEDITE_VORBEUGEND * abf[idx])
        expedite = np.where(exp_spaet | exp_vorb, rng.uniform(200, 800, m), 0.0)
        teile.append(pd.DataFrame({
            "DateKey": datekey[idx],
            "OrgKey": np.full(m, dc[lane], dtype=np.int64),
            "ProductKey": prod,
            "LaneKey": np.full(m, lane, dtype=np.int64),
            "OTIF Flag": otif,
            "On-Time Flag": on_time,
            "In-Full Flag": in_full,
            "Order Correct Flag": korrekt,
            "Order Qty": menge.astype(float),
            "Penalty Amount": np.round(penalty, 2),
            "Expedite Cost": np.round(expedite, 2),
        }))
    out = pd.concat(teile, ignore_index=True)
    return out.sort_values(["DateKey", "LaneKey"], kind="stable").reset_index(drop=True)


def slots(df: pd.DataFrame) -> pd.DataFrame:
    """Lane/DC/ISO-Woche mit Sendungen, On-Time-Quote und S-R2.2-Stufe (mit Persistenz).

    `stufe_roh`: Stufe dieser Woche, nur wenn Sendungen >= GUARDRAIL. `stufe`: erreicht, wenn
    die Woche und die `PERSISTENZ - 1` Wochen davor (lueckenlos) mindestens diese Stufe tragen.
    """
    d = pd.to_datetime(df["DateKey"].astype(str), format="%Y%m%d")
    iso = d.dt.isocalendar()
    g = (df.assign(Jahr=iso["year"].to_numpy(), Woche=iso["week"].to_numpy())
         .groupby(["LaneKey", "OrgKey", "Jahr", "Woche"], sort=True)
         .agg(Sendungen=("On-Time Flag", "size"), OnTime=("On-Time Flag", "mean"))
         .reset_index())
    rang = {"": 0, "L1": 1, "L2": 2, "L3": 3}

    def roh(r) -> str:
        if r.Sendungen < GUARDRAIL:
            return ""
        for name, grenze in STUFEN:
            if r.OnTime < grenze:
                return name
        return ""

    g["stufe_roh"] = [roh(r) for r in g.itertuples()]
    g["montag"] = pd.to_datetime(
        g["Jahr"].astype(str) + "-W" + g["Woche"].astype(str).str.zfill(2) + "-1", format="%G-W%V-%u")
    stufe = []
    for _, grp in g.groupby(["LaneKey", "OrgKey"], sort=False):
        werte = grp["stufe_roh"].map(rang).to_numpy()
        montage = grp["montag"].to_numpy()
        for i in range(len(grp)):
            lo = i - PERSISTENZ + 1
            if lo < 0 or (montage[i] - montage[lo]) != np.timedelta64(7 * (PERSISTENZ - 1), "D"):
                stufe.append(0)
                continue
            stufe.append(int(werte[lo:i + 1].min()))
    inv = {v: k for k, v in rang.items()}
    g["stufe"] = [inv[s] for s in stufe]
    return g.drop(columns=["montag"])


def alten_zufallsstrom_vorspulen(rnd, tage: pd.DatetimeIndex, org_keys: list,
                                 product_keys: list, lane_keys: list, seed: int) -> None:
    """Verbraucht aus `rnd` genau die Ziehungen des alten fact_fulfillment-Blocks (bis 06.10.2026).

    Zweck: `fact_stockout` und `fact_forecast` ziehen danach aus demselben globalen Strom. Ohne
    dieses Vorspulen aenderte ein Gesamtlauf auch diese beiden Tabellen, obwohl sich nur
    fact_fulfillment fachlich aendert (gemessen 07.10.2026: der Generator reproduziert
    dim_lane, fact_cogs, fact_fulfillment, fact_stockout und fact_forecast des Releases 29c
    inhaltsgleich). Erzeugt keine Daten.
    """
    for d in tage:
        n = max(1, int(5 * apply_combined_seasonality(d, 1.0, 0.6, 0.4, seed)))
        for _ in range(n):
            rnd.choice(org_keys[:5])
            rnd.choice(product_keys[:15])
            rnd.choice(lane_keys[:5])
            otif = rnd.random() < 0.90
            on_time = rnd.random() < 0.92
            rnd.random()
            rnd.random()
            rnd.uniform(0.7, 1.3)
            if not otif:
                rnd.uniform(100, 500)
            if not on_time:
                rnd.uniform(200, 800)
