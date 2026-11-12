"""Strukturformen (ADR-0029): Schema, Vokabular, Regeln mit Beleg, Auswahl.

Hält fest: jede Form trägt genau die Schemaschlüssel; jeder Wert stammt aus dem Vokabular;
jede Regel hat eine Belegart, gemessene Regeln eine Zahl; jedes Paar Struktur x Frage hat
eine Form oder steht mit Grund in `ungedeckt`; die Auswahl ist deterministisch und trifft
die eingefrorenen Fälle.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import strukturform as sf  # noqa: E402

LIB = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library"
CASES = json.loads((REPO_ROOT / "tooling" / "visual_library" / "strukturform_cases.json").read_text(encoding="utf-8"))
SCHEMA = yaml.safe_load((sf.FORMEN / "_schema.yaml").read_text(encoding="utf-8"))
VOK = sf.vokabular()
REGELN = sf.regeln()
ANTI = yaml.safe_load((LIB / "_anti_patterns.yaml").read_text(encoding="utf-8"))["patterns"]

ANZAHL_FORMEN = 13
ANZAHL_REGELN = 21
ANZAHL_FAELLE = 20


def test_anzahl_formen_regeln_faelle() -> None:
    assert len(sf.formen()) == ANZAHL_FORMEN
    assert len(REGELN) == ANZAHL_REGELN
    assert len(CASES["faelle"]) == ANZAHL_FAELLE


@pytest.mark.parametrize("fid", sorted(sf.formen()))
def test_form_schema(fid: str) -> None:
    f = sf.formen()[fid]
    assert list(f) == SCHEMA["required_keys"], f"{fid}: Schlüssel/Reihenfolge weichen vom Schema ab"
    assert f["id"] == fid
    assert f["status"] in {"active", "experimental", "deprecated"}
    assert set(f["strukturtypen"]) <= set(VOK["strukturtypen"])
    fragen = f["fragen"]["primaer"] + f["fragen"]["sekundaer"]
    assert f["fragen"]["primaer"], f"{fid}: keine primäre Frage"
    assert set(fragen) <= set(VOK["fragetypen"]) and len(fragen) == len(set(fragen))
    lo, hi = f["menge"]["min"], f["menge"]["max"]
    assert isinstance(lo, int) and lo >= 1 and (hi is None or hi >= lo)
    assert set(f["voraussetzung"]) <= {"masse", "zyklen", "wurzeln_max", "start_ziel"}
    assert 1 <= f["kantenklassen_max"] <= len(VOK["kantenklassen"])
    assert set(f["reduktion"]) <= set(VOK["reduktion"])
    assert set(f["interaktion"]) <= set(VOK["interaktion"])
    assert f["technik"] and set(f["technik"]) <= {"svg", "html", "canvas", "webgl"}
    assert f["textalternative"].strip()
    assert f["regeln"] and set(f["regeln"]) <= set(REGELN)
    assert f["vorrang_regel"] in REGELN
    assert set(f["anti_patterns"]) <= set(ANTI)
    if f["idiom_ref"] is not None:
        assert (LIB / f"{f['idiom_ref']}.yaml").is_file(), f"{fid}: Idiom {f['idiom_ref']} fehlt"


def test_webgl_nur_raeumlich() -> None:
    """3D bleibt der räumlichen Struktur vorbehalten (Regel raum_3d_nur_mit_tiefenhinweis)."""
    for fid, f in sf.formen().items():
        if "webgl" in f["technik"]:
            assert f["strukturtypen"] == ["raeumlich"], fid


@pytest.mark.parametrize("rid", sorted(REGELN))
def test_regel_beleg(rid: str) -> None:
    r = REGELN[rid]
    assert r["regel"].strip() and r["quelle"].strip() and r["geltung"].strip()
    assert r["beleg"] in SCHEMA["belegarten"]
    if r["beleg"] == "gemessen":
        assert str(r.get("zahl", "")).strip(), f"{rid}: gemessen ohne Zahl"


def test_jede_regel_wird_genutzt() -> None:
    genutzt = {r for f in sf.formen().values() for r in f["regeln"] + [f["vorrang_regel"]]}
    assert set(REGELN) - genutzt == set()


def test_kantenklassen_darstellung() -> None:
    assert len(VOK["kantenklassen"]) == 6
    for k, v in VOK["kantenklassen"].items():
        assert set(v["darstellung"]) == {"strich", "richtung", "glyphe"}, k
        assert v["quelle"].strip()
    # zwei Klassen mit gleicher Darstellung wären nicht unterscheidbar
    darst = [tuple(sorted(v["darstellung"].items())) for v in VOK["kantenklassen"].values()]
    assert len(darst) == len(set(darst))


def test_deckung_struktur_frage() -> None:
    alle = {(s, q) for s in VOK["strukturtypen"] for q in VOK["fragetypen"]}
    ungedeckt = {(u["struktur"], u["frage"]) for u in VOK["ungedeckt"]}
    for u in VOK["ungedeckt"]:
        assert u["grund"].strip()
    gedeckt = sf.gedeckte_paare()
    assert alle - gedeckt == ungedeckt, "Paar ohne Form fehlt in ungedeckt oder ungedeckt ist veraltet"
    assert len(gedeckt) + len(ungedeckt) == len(alle) == 42


@pytest.mark.parametrize("fall", CASES["faelle"], ids=lambda c: c["name"])
def test_fall(fall: dict) -> None:
    d = sf.Daten(**fall.get("daten", {}))
    treffer = sf.waehle(fall["struktur"], fall["frage"], fall["knoten"], d)
    erst = treffer[0].id if treffer else None
    assert erst == fall["erwartet"]
    if "folge" in fall:
        assert [t.id for t in treffer] == fall["folge"]
    if "reduktion_noetig" in fall:
        assert list(treffer[0].reduktion_noetig) == fall["reduktion_noetig"]


def test_deterministisch() -> None:
    for fall in CASES["faelle"]:
        d = sf.Daten(**fall.get("daten", {}))
        a = sf.waehle(fall["struktur"], fall["frage"], fall["knoten"], d)
        b = sf.waehle(fall["struktur"], fall["frage"], fall["knoten"], d)
        assert a == b


def test_unbekannte_werte_brechen_ab() -> None:
    with pytest.raises(ValueError):
        sf.waehle("hypergraph", "weg", 10)
    with pytest.raises(ValueError):
        sf.waehle("netz", "warum", 10)
