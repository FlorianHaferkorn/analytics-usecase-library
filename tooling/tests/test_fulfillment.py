"""fact_fulfillment der Aurora-Showcase (07.10.2026): Regeln aus `_fulfillment.py`.

Vorher zog der Generator OTIF, On-Time und In-Full unabhaengig per `random()` (gemessen auf dem
Release 2026-09-29c: 19,9 % der Zeilen mit OTIF != On-Time AND In-Full) bei ~5 Sendungen je Tag;
kein Lane/DC/Woche-Slot erreichte den S-R2.2-Guardrail. Diese Tests halten die Eigenschaften
fest, die die SCM-002-Story tragen. Die Unit-Tests bauen ihre Dimensionen selbst; der letzte
Test liest die echten Showdaten-Dimensionen (Skip mit Grund, wenn nicht geholt).
"""
from __future__ import annotations

import importlib.util
import random
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
GOLD = REPO / "showcases" / "aurora_group" / "data" / "gold"
if str(GOLD) not in sys.path:
    sys.path.insert(0, str(GOLD))
import _fulfillment as ff  # noqa: E402 -- nach sys.path (wie die Generatoren)

from _generator_utils import apply_combined_seasonality  # noqa: E402

_sd_spec = importlib.util.spec_from_file_location(
    "showdaten", REPO / "showcases" / "aurora_group" / "data" / "showdaten.py")
showdaten = importlib.util.module_from_spec(_sd_spec)
_sd_spec.loader.exec_module(showdaten)

SEED = 12345
TAGE = pd.date_range("2020-01-01", "2024-12-31", freq="D")
DCS = ["DC-DE-01", "DC-DE-02", "DC-AT-01", "DC-AT-02", "DC-CH-01", "DC-CH-02", "DC-NL-01", "DC-BE-01"]


def _dims() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    lanes = pd.DataFrame({"LaneKey": range(1, 33),
                          "Origin": [DCS[i % len(DCS)] for i in range(32)],
                          "Destination": "DE", "Mode": "Road"})
    org = pd.DataFrame({"OrgKey": [100 + i for i in range(len(DCS))] + [1],
                        "OrgCode": DCS + ["AURORA-GROUP"]})
    kats = ["Fashion"] * 30 + ["Home & Living"] * 30 + ["Consumer Electronics"] * 30
    produkte = pd.DataFrame({"ProductKey": range(1, 91), "Category": kats,
                             "Lifecycle Status": ["Active", "EOL"] * 45})
    return lanes, org, produkte


@pytest.fixture(scope="module")
def daten() -> pd.DataFrame:
    return ff.erzeuge(*_dims(), TAGE, SEED)


@pytest.fixture(scope="module")
def slots(daten) -> pd.DataFrame:
    return ff.slots(daten)


def _volle_wochen(s: pd.DataFrame) -> pd.DataFrame:
    """Nur ISO-Wochen, deren sieben Tage im Zeitraum liegen (2020-W01 und 2025-W01 sind Teilwochen)."""
    montag = pd.to_datetime(s["Jahr"].astype(str) + "-W" + s["Woche"].astype(str).str.zfill(2) + "-1",
                            format="%G-W%V-%u")
    return s[(montag >= TAGE.min()) & (montag + pd.Timedelta(days=6) <= TAGE.max())]


def test_otif_is_on_time_and_in_full_in_every_row(daten):
    assert (daten["OTIF Flag"] == (daten["On-Time Flag"] & daten["In-Full Flag"])).all()


def test_two_runs_are_identical(daten):
    pd.testing.assert_frame_equal(daten, ff.erzeuge(*_dims(), TAGE, SEED))
    assert not daten.equals(ff.erzeuge(*_dims(), TAGE, SEED + 1))


def test_orgkey_is_the_dc_of_the_lane(daten):
    lanes, org, _ = _dims()
    erwartet = daten["LaneKey"].map(ff.lane_dc(lanes, org))
    assert (daten["OrgKey"] == erwartet).all()


def test_main_lanes_reach_the_volume_guardrail_in_every_full_week(slots):
    voll = _volle_wochen(slots)
    haupt = voll[voll["LaneKey"].isin(ff.HAUPTLANES)]
    neben = slots[~slots["LaneKey"].isin(ff.HAUPTLANES)]
    assert len(haupt) == len(ff.HAUPTLANES) * 260
    assert (haupt["Sendungen"] >= ff.GUARDRAIL).all(), haupt["Sendungen"].min()
    assert (neben["Sendungen"] < ff.GUARDRAIL).all(), neben["Sendungen"].max()


def test_l2_and_l3_only_in_the_affected_lanes(slots):
    ernst = slots[slots["stufe"].isin(["L2", "L3"])]
    assert set(ernst["LaneKey"]) == set(ff.BETROFFENE_LANES)
    assert (slots["stufe"] == "L3").any()
    assert (slots["stufe"] == "L1").any()
    # vor dem ersten Abfall loest keine betroffene Lane aus
    vorher = slots[(slots["LaneKey"].isin(list(ff.BETROFFENE_LANES))) & (slots["Jahr"] <= 2022)]
    assert (vorher["stufe"].isin(["L2", "L3"])).sum() == 0


def test_on_time_drives_the_decline_and_in_full_stays_flat(daten):
    jahr = daten["DateKey"] // 10000
    betroffen = daten["LaneKey"].isin(list(ff.BETROFFENE_LANES))
    def quote(spalte, maske, j):
        return daten.loc[maske & (jahr == j), spalte].mean()
    assert quote("On-Time Flag", betroffen, 2022) - quote("On-Time Flag", betroffen, 2024) > 0.03
    assert abs(quote("On-Time Flag", ~betroffen, 2022) - quote("On-Time Flag", ~betroffen, 2024)) < 0.003
    for maske in (betroffen, ~betroffen):
        assert abs(quote("In-Full Flag", maske, 2022) - quote("In-Full Flag", maske, 2024)) < 0.003
    gesamt = daten.groupby(jahr)[["On-Time Flag", "In-Full Flag", "OTIF Flag"]].mean()
    assert gesamt.loc[2024, "OTIF Flag"] < gesamt.loc[2022, "OTIF Flag"]


def test_affected_lanes_ship_mostly_their_category(daten):
    _, _, produkte = _dims()
    kat = daten["ProductKey"].map(dict(zip(produkte["ProductKey"], produkte["Category"])))
    for lane, a in ff.BETROFFENE_LANES.items():
        anteil = (kat[daten["LaneKey"] == lane] == a.kategorie).mean()
        assert abs(anteil - ff.ANTEIL_HAUPTKATEGORIE) < 0.02
    assert set(daten["ProductKey"]) <= set(produkte.loc[produkte["Lifecycle Status"] == "Active", "ProductKey"])


def test_penalty_only_on_otif_miss_and_expedite_rises_in_affected_lanes(daten):
    assert (daten.loc[daten["OTIF Flag"], "Penalty Amount"] == 0).all()
    assert (daten.loc[~daten["OTIF Flag"], "Penalty Amount"] > 0).all()
    jahr = daten["DateKey"] // 10000
    betroffen = daten["LaneKey"].isin(list(ff.BETROFFENE_LANES))
    def je_sendung(maske, j):
        return daten.loc[maske & (jahr == j), "Expedite Cost"].mean()
    assert je_sendung(betroffen, 2024) > 3 * je_sendung(betroffen, 2022)
    assert 0.8 < je_sendung(~betroffen, 2024) / je_sendung(~betroffen, 2022) < 1.2


def test_slots_need_volume_and_consecutive_weeks():
    def zeilen(tag: str, n: int, spaet: int) -> pd.DataFrame:
        return pd.DataFrame({"DateKey": int(tag.replace("-", "")), "LaneKey": 1, "OrgKey": 9,
                             "On-Time Flag": [False] * spaet + [True] * (n - spaet)})
    df = pd.concat([zeilen("2024-01-01", 100, 7),     # W01: 93 % -> L2
                    zeilen("2024-01-08", 100, 11),    # W02: 89 % -> L3, persistiert L2
                    zeilen("2024-01-22", 100, 11),    # W04: Luecke davor -> nicht persistiert
                    zeilen("2024-01-29", 99, 50)])    # W05: unter Guardrail -> keine Stufe
    s = ff.slots(df).set_index("Woche")
    assert s["stufe_roh"].to_dict() == {1: "L2", 2: "L3", 4: "L3", 5: ""}
    assert s["stufe"].to_dict() == {1: "", 2: "L2", 4: "", 5: ""}


def test_fast_forward_consumes_exactly_the_old_block():
    """Gleicher Zustand des globalen Stroms wie mit dem alten Block -> fact_stockout/fact_forecast
    bleiben bei einem Gesamtlauf unveraendert."""
    tage = pd.date_range("2024-01-01", "2024-03-31", freq="D")
    org_keys, product_keys, lane_keys = list(range(1, 21)), list(range(1, 51)), list(range(1, 33))
    alt = random.Random(SEED)
    for d in tage:   # der Block bis 06.10.2026, Ziehungen unveraendert
        for _ in range(max(1, int(5 * apply_combined_seasonality(d, 1.0, 0.6, 0.4, SEED)))):
            alt.choice(org_keys[:5])
            alt.choice(product_keys[:15])
            alt.choice(lane_keys[:5])
            otif = alt.random() < 0.90
            on_time = alt.random() < 0.92
            alt.random()
            alt.random()
            max(10, int(100 * alt.uniform(0.7, 1.3)))
            if not otif:
                alt.uniform(100, 500)
            if not on_time:
                alt.uniform(200, 800)
    neu = random.Random(SEED)
    ff.alten_zufallsstrom_vorspulen(neu, tage, org_keys, product_keys, lane_keys, SEED)
    assert neu.getstate() == alt.getstate()


@showdaten.pytest_markierung()
def test_affected_and_main_lanes_exist_in_the_released_dim_lane():
    lanes = ff.lies_tabelle(GOLD / "dimensions" / "dim_lane")
    org = ff.lies_tabelle(GOLD / "dimensions" / "dim_org")
    herkunft = dict(zip(lanes["LaneKey"].astype(int), lanes["Origin"]))
    assert herkunft[12] == "DC-AT-01" and herkunft[22] == "DC-CH-02"
    assert set(ff.HAUPTLANES) <= set(herkunft)
    dc = ff.lane_dc(lanes, org)
    typ = dict(zip(org["OrgKey"].astype(int), org["OrgType"]))
    assert {typ[k] for k in dc.values()} == {"DC"}
    pool = ff.produktpool(ff.lies_tabelle(GOLD / "dimensions" / "dim_product"))
    assert all(len(v) == ff.PRODUKTE_JE_KATEGORIE for v in pool.values())
