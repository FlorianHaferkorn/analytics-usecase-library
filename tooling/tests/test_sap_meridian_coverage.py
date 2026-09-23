"""Bruecke Meridian-SAP-Gold -> ALUCA-Use-Cases (Q-3, 23.09.2026).

Die Karte `tooling/connectors/sap/meridian_gold_map.yaml` sagt je Aurora-Spalte, ob
Meridians SAP-Gold sie traegt. Diese Tests halten zwei Zusagen fest: die Karte ist fuer
jede Spalte, die ein Use Case liest, vollstaendig (kein stilles Weglassen), und ein
Tabellen-Blocker schlaegt auf jede Spalte der Tabelle durch.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tooling.connectors.sap import coverage  # noqa: E402

GUELTIG = {"abgebildet", "ableitbar", "fehlt_im_paket", "nicht_in_sap_belegen"}


def test_every_mapped_column_carries_a_known_status_and_a_reason():
    k = coverage.karte()
    for spalte, e in k["spalten"].items():
        assert e["status"] in GUELTIG, spalte
        # Wer "abgebildet" sagt, nennt die Gold-Spalte; alle anderen nennen Regel oder Grund.
        feld = {"abgebildet": "quelle", "ableitbar": "regel"}.get(e["status"], "grund")
        assert e.get(feld), f"{spalte}: {e['status']} ohne {feld}"
    for tabelle, t in k["tabellen"].items():
        assert t["blocker"]["status"] in GUELTIG - {"abgebildet", "ableitbar"}, tabelle
        assert t["blocker"]["grund"], tabelle


def test_no_use_case_column_of_an_sap_table_is_left_unmapped():
    ab = coverage.abdeckung()
    unbelegt = sorted({s for ks in ab.values() for v in ks.values()
                       for s, (st, _) in v["spalten"].items() if st == "unbelegt"})
    assert unbelegt == []


def test_a_table_blocker_overrides_a_mapped_column():
    k = coverage.karte()
    assert k["spalten"]["fact_sales.Net Sales Amount"]["status"] == "abgebildet"
    assert coverage.spalten_status("fact_sales.Net Sales Amount", k)[0] == "fehlt_im_paket"
    # Gegenprobe: ohne Blocker ist dieselbe Spalte nutzbar.
    ohne = {**k, "tabellen": {t: v for t, v in k["tabellen"].items() if t != "fact_sales"}}
    assert coverage.spalten_status("fact_sales.Net Sales Amount", ohne)[0] == "abgebildet"


def test_an_unknown_column_of_an_sap_table_is_reported_not_skipped():
    k = coverage.karte()
    assert coverage.spalten_status("fact_sales.Gibt Es Nicht", k)[0] == "unbelegt"
    assert coverage.spalten_status("fact_support.Tickets", k)[0] == "ausser_sap"


def test_measured_state_of_the_bridge():
    """Der gemessene Stand vom 23.09.2026. Aendert er sich, ist das eine Nachricht."""
    ab = coverage.abdeckung()
    nutzbar = {uc[:7] for uc, ks in ab.items() if any(v["urteil"] == "nutzbar" for v in ks.values())}
    assert nutzbar == {"FIN-001", "FIN-003", "SCM-001", "SCM-002"}
    # Kein Use Case ist vollstaendig aus SAP-Gold bedienbar.
    assert not any(ks and all(v["urteil"] == "nutzbar" for v in ks.values()) for ks in ab.values())
    # Kein Umsatz-Use-Case ist bedienbar, solange VBRK fehlt.
    for uc, ks in ab.items():
        if uc[:7] in {"COM-001", "COM-002"}:
            assert not any(v["urteil"] == "nutzbar" for v in ks.values()), uc
