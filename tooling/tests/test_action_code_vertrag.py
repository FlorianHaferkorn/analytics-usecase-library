"""Action-Vertrag D-833 Schritt 1 (SOM-001): Form (Schema), Bezuege (check_action_contract) und Zaehler.

Gezaehlt wird gegen den Bestand vom 14.11.2026: 61 Action Codes, alle mit den vier Feldern. Die
Leerstellen (`nicht_belegt`) sind eine Sperrklinke: sie duerfen weniger werden, nie mehr. Jede Regel
hat eine Gegenprobe, die zeigt, dass sie einen Fehler auch faengt.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest
import yaml

from tooling.migration import action_code_vertrag as mig
from tooling.validation import check_action_contract as chk

REPO = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((REPO / "tooling/generator/schemas/action_code.schema.json").read_text(encoding="utf-8"))
VALIDATOR = jsonschema.Draft7Validator(SCHEMA)
DATEIEN = chk.action_code_dateien(REPO)
CODES = {yaml.safe_load(p.read_text(encoding="utf-8"))["id"]: yaml.safe_load(p.read_text(encoding="utf-8"))
         for p in DATEIEN}
KATALOG = chk.lade_katalog(REPO)
ROLLEN = chk.lade_rollen(REPO)
SPALTEN = chk.lade_spalten(REPO)

#: Bestand 14.11.2026 (Migration `tooling/migration/action_code_vertrag.py --report`).
ANZAHL_CODES = 61
#: Sperrklinke: Leerstellen je Feld. Migration 14.11.2026: binding 225, status 6, role_id 53; nach
#: `--nachtragen` (11 Rollen + 9 Aliase im Kern-Register, Spalten aus den Data Contracts): 124, 6, 0.
LEERSTELLEN_HOECHSTENS = {"parameters.binding": 124, "preconditions.status": 6, "permitted_role.role_id": 0}


def _fehler(d: dict) -> list[str]:
    return [e.message for e in VALIDATOR.iter_errors(d)]


def test_61_codes_tragen_alle_vier_felder_und_bestehen_das_schema():
    assert len(CODES) == ANZAHL_CODES
    z = mig.zaehlung(CODES)
    assert z["mit_allen_feldern"] == ANZAHL_CODES
    assert {c: _fehler(d) for c, d in CODES.items() if _fehler(d)} == {}


def test_bezuege_ohne_befund():
    n, befunde = chk.pruefe(REPO)
    assert n == ANZAHL_CODES
    assert befunde == []


def test_zaehler_und_sperrklinke_der_leerstellen():
    z = mig.zaehlung(CODES)
    assert z["eintraege"]["preconditions.pruefbar"] >= 232
    assert z["eintraege"]["permitted_role.roles"] == sum(
        len(d["governance"]["approvals_required"]) for d in CODES.values())
    for feld, grenze in LEERSTELLEN_HOECHSTENS.items():
        assert z["nicht_belegt"][feld] <= grenze, feld
    assert z["review_state"] == ["vorgeschlagen"]


def test_migration_ist_idempotent_und_ueberschreibt_nichts():
    """Ein zweiter Lauf fuegt nichts ein; ein von Hand gefuelltes Feld bleibt."""
    for p in DATEIEN[:3]:
        text = p.read_text(encoding="utf-8")
        ac = yaml.safe_load(text)
        fehlend = {k: v for k, v in mig.ableiten(ac, mig.rollen_index()).items() if k not in ac}
        assert fehlend == {}
    ac = copy.deepcopy(CODES["F-C1.1"])
    ac["permitted_role"]["roles"][0]["role_id"] = "finance_director"
    assert "permitted_role" not in {k for k in mig.ableiten(ac, mig.rollen_index()) if k not in ac}


def test_ableitung_aus_dem_bestand_f_c1_1():
    ac = CODES["F-C1.1"]
    assert [c["kpi_id"] for c in ac["preconditions"]["checks"]] == ["KPI-FIN-010", "KPI-FIN-006", "KPI-FIN-006",
                                                                    "KPI-FIN-007"]
    assert ac["permitted_role"]["roles"] == [{"approver": "CFO", "role_id": "cfo"}]
    assert {p["name"]: p.get("binding", p["type"]) for p in ac["parameters"]} == {
        "period": "period", "trigger_level": "trigger_level", "legal_entity": "dim_org.Entity",
        "region": "nicht_belegt"}


def test_rolle_wird_nur_bei_gleichem_titel_gebunden():
    roles = [r for d in CODES.values() for r in d["permitted_role"]["roles"] if r["role_id"] != "nicht_belegt"]
    assert roles, "mindestens eine gebundene Rolle"
    for r in roles:
        assert ROLLEN[r["role_id"]]["title"].lower() == r["approver"].lower() or \
            r["approver"].lower() in [a.lower() for a in ROLLEN[r["role_id"]].get("aliases") or []]


# ── Gegenproben: jede Regel faengt ihren Fehler ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name,aendern", [
    ("Feld fehlt", lambda d: d.pop("parameters")),
    ("unbekannter Zustand", lambda d: d["review"].__setitem__("state", "erledigt")),
    ("pruefbar ohne KPI", lambda d: d["preconditions"]["checks"][0].pop("kpi_id")),
    ("Prosa als pruefbar", lambda d: d["preconditions"]["checks"][0].update(kind="composite_rule")),
    ("Rolle frei getextet", lambda d: d["permitted_role"]["roles"][0].__setitem__("role_id", "Der CFO")),
    ("period mit binding", lambda d: d["parameters"][0].__setitem__("binding", "dim_date.Month")),
    ("dimension ohne binding", lambda d: d["parameters"][2].pop("binding")),
])
def test_gegenprobe_schema(name, aendern):
    d = copy.deepcopy(CODES["F-C1.1"])
    aendern(d)
    assert _fehler(d), name


@pytest.mark.parametrize("name,aendern,regel", [
    ("KPI nicht im Katalog", lambda d: d["preconditions"]["checks"][0].__setitem__("kpi_id", "KPI-FIN-999"), "V1"),
    ("KPI weicht von ref ab", lambda d: d["preconditions"]["checks"][0].__setitem__("kpi_id", "KPI-FIN-006"), "V2"),
    ("ref loest nicht auf", lambda d: d["preconditions"]["checks"][0].__setitem__("ref", "trigger.levels.L9.condition"),
     "V2"),
    ("Rolle nicht im Register", lambda d: d["permitted_role"]["roles"][0].__setitem__("role_id", "cfo_x"), "V3"),
    ("Rolle mit anderem Titel", lambda d: d["permitted_role"]["roles"][0].__setitem__("role_id", "finance_director"),
     "V3"),
    ("Freigeber nachtraeglich geaendert", lambda d: d["governance"]["approvals_required"].append("COO"), "V4"),
    ("Stufe ohne Vorbedingung", lambda d: d["preconditions"]["checks"].pop(0), "V6"),
    ("Koernung abweichend", lambda d: d["scope"].__setitem__("default_grain", "week"), "V5"),
    ("Spalte nicht im Contract", lambda d: d["parameters"][2].__setitem__("binding", "dim_org.Erfunden"), "V7"),
])
def test_gegenprobe_bezuege(name, aendern, regel):
    d = copy.deepcopy(CODES["F-C1.1"])
    aendern(d)
    befunde = chk.pruefe_code(d, KATALOG, ROLLEN, SPALTEN)
    assert any(f" {regel}" in b for b in befunde), (name, befunde)


def test_gegenprobe_tor_unterscheidet_nicht_gelaufen(tmp_path):
    """Ohne Action Codes endet das Tor mit 2 (nicht geprueft), nicht mit 0."""
    (tmp_path / "core" / "organization").mkdir(parents=True)
    (tmp_path / "core" / "organization" / "org_roles.yaml").write_text("schema_version: '1.0'\nroles: []\n",
                                                                       encoding="utf-8")
    assert chk.main(["--repo-root", str(tmp_path)]) == 2


# ── Nachtragen (14.11.2026): nur eindeutige Leerstellen, sonst nichts ────────────────────────────────────────

def test_nachtragen_ist_idempotent():
    rollen, spalten = mig.rollen_index(), mig.spalten_index()
    for p in DATEIEN:
        neu, n = mig.nachtragen(p.read_text(encoding="utf-8"), rollen, spalten)
        assert n == 0, p.name


def test_bindung_nur_bei_genau_einem_treffer():
    spalten = mig.spalten_index()
    assert mig.bindung("Customer Segment", spalten) == "dim_customer.Segment"
    assert len(spalten[mig._norm("Region")]) > 1
    assert mig.bindung("Region", spalten) == "nicht_belegt"
    assert mig.bindung("Erfundene Dimension", spalten) == "nicht_belegt"


def test_gegenprobe_nachtragen_fuellt_nur_leerstellen():
    """Ein von Hand gesetzter Wert bleibt; eine unbekannte Rolle bleibt Leerstelle; sonst aendert sich nichts."""
    text = (REPO / "core/action_codes/Finance/F-C1.1.yaml").read_text(encoding="utf-8")
    leer = text.replace("role_id: cfo", "role_id: nicht_belegt").replace(
        "binding: dim_org.Entity", "binding: nicht_belegt")
    assert leer != text
    neu, n = mig.nachtragen(leer, mig.rollen_index(), mig.spalten_index())
    assert (neu, n) == (text, 2)
    hand = text.replace("role_id: cfo", "role_id: finance_director")
    assert mig.nachtragen(hand, mig.rollen_index(), mig.spalten_index()) == (hand, 0)
    fremd = leer.replace("- approver: CFO", "- approver: Chief Wizard").replace(
        "  - CFO\n", "  - Chief Wizard\n")
    neu, n = mig.nachtragen(fremd, mig.rollen_index(), mig.spalten_index())
    assert "role_id: nicht_belegt" in neu and n == 1
