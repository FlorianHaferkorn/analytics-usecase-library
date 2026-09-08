"""Die Bruecke zwischen `visual_registry.yaml` und der Visual Library haelt.

Warum es diesen Test gibt
-------------------------
Eine Seitenvariante in `template_manifest.yaml` nennt je Slot einen
`information_block`. Der Block in `visual_registry.yaml` nennt seine erlaubten
Visuals. Und dort endete die Kette: die 25 `visual_id`s der Registry und die 30
Idiom-Bezeichner der Visual Library sind zwei Namensmengen fuer teils dieselben
Sachen — am 08.09.2026 waren genau zwei Namen gleich (`decomposition_tree`,
`small_multiples`). Eine Seite liess sich also vollstaendig deklarieren, ohne dass
irgendetwas sie zeichnen konnte.

Das optionale Feld `idiom` schliesst sie. Dieser Test haelt drei Zusagen:
1. jeder gesetzte `idiom` existiert in der Bibliothek,
2. sein nativer visualType ist genau der `pbip_type` des Registry-Eintrags
   (sonst waere die Bruecke geraten statt gemessen),
3. der `pbip_type` selbst steht im offiziellen Katalogauszug — dieselbe Pruefung,
   die `tooling/visual_library/tests/test_visual_library.py` fuer die Goldens
   faehrt, hier fuer das zweite Register.

Zu (3): Registry-Eintraege duerfen `pbip_type: null` fuehren (ein Verbot, fuer das
es gar kein Kernvisual gibt) oder den Platzhalter `any_chart`. Beides ist eine
Aussage und kein Typname; beides wird ausdruecklich uebersprungen, damit der Test
nicht an seiner eigenen Ausnahme scheitert.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_registry.yaml"
LIB = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library"
FACTS = REPO_ROOT / "tooling" / "visual_library" / "catalog_facts.json"

# Keine Typnamen, sondern Aussagen: `null` = es gibt kein Kernvisual dafuer,
# `any_chart` = die Regel gilt fuer jedes Diagramm.
KEINE_TYPNAMEN = {None, "any_chart"}


def _registry() -> dict:
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))


def _eintraege(nur_erlaubte: bool = False):
    """(block_id, feld, eintrag) fuer jedes Visual der Registry."""
    felder = ("allowed_visuals",) if nur_erlaubte else ("allowed_visuals", "forbidden_visuals")
    for block in _registry()["information_blocks"]:
        for feld in felder:
            for v in block.get(feld) or []:
                yield block["block_id"], feld, v


def _idiom_nativer_typ(idiom: str) -> str | None:
    p = LIB / f"{idiom}.yaml"
    if not p.exists():
        return None
    d = yaml.safe_load(p.read_text(encoding="utf-8"))
    nat = (d.get("realizations") or {}).get("powerbi_native") or {}
    t = nat.get("template")
    return json.loads(t.replace("{{", "__").replace("}}", "__"))["visualType"] if t else None


def test_jede_idiom_bruecke_zeigt_auf_ein_vorhandenes_idiom():
    for block, feld, v in _eintraege():
        idiom = v.get("idiom")
        if not idiom:
            continue
        assert (LIB / f"{idiom}.yaml").exists(), (
            f"{block}.{feld}.{v['visual_id']}: idiom '{idiom}' gibt es in der Visual Library nicht")


def test_die_bruecke_ist_gemessen_und_nicht_geraten():
    """Der native visualType des Idioms ist der `pbip_type` des Registry-Eintrags.

    Die Ausnahme ist benannt statt still: ein Idiom OHNE native Spur (in-Zellen-Measure
    wie `matrix_bullet`, `matrix_delta_pill`, `matrix_sparkline`) traegt keinen eigenen
    visualType — es lebt in einer `tableEx`-Zelle. Fuer die verlangt der Test den Wirt.
    """
    for block, feld, v in _eintraege():
        idiom = v.get("idiom")
        if not idiom:
            continue
        nativ = _idiom_nativer_typ(idiom)
        erwartet = v.get("pbip_type")
        if nativ is None:
            assert erwartet == "tableEx", (
                f"{block}.{v['visual_id']}: '{idiom}' hat keine native Spur und ist damit eine "
                f"Measure in einer Zelle — der Wirt muss `tableEx` sein, hier steht '{erwartet}'")
            continue
        assert nativ == erwartet, (
            f"{block}.{v['visual_id']}: die Registry sagt '{erwartet}', das Idiom '{idiom}' "
            f"erzeugt '{nativ}' — eine Bruecke, die zwei verschiedene Visuals verbindet")


def test_jeder_pbip_typ_der_registry_steht_im_offiziellen_katalog():
    """Ein Typname, den es nicht gibt, macht jede Pruefung darauf blind.

    Gemessen 08.09.2026, vor der Korrektur: `100%StackedBarChart` und
    `100%StackedColumnChart` in `allowed_visuals` (und damit in der Tabelle, die
    `check_page_template_compliance._aus_registry()` daraus ableitet), sowie
    `gaugeVisual`, `radarChart` und zweimal `stackedBarChart` in `forbidden_visuals` —
    ein Verbot auf einen Namen, den kein Visual traegt, greift nie.
    """
    facts = json.loads(FACTS.read_text(encoding="utf-8"))
    # Der Auszug deckt die Typen der Bibliothek. Fuer die Registry zaehlt hier nur, ob
    # der Name ueberhaupt ein Katalogtyp ist — dafuer wird der volle Katalog gebraucht,
    # den ALUCA nicht hat. Also gegen die Vereinigung aus Auszug + der hier gepflegten
    # Zusatzliste pruefen, die genau die Typen fuehrt, die die Registry darueber hinaus
    # nennt und die am 08.09.2026 einzeln gegen den Katalog 0.1.1 gemessen wurden.
    weitere = {"areaChart", "barChart", "cardVisual", "gauge", "hundredPercentStackedBarChart",
               "kpi", "pieChart", "pivotTable", "slicer", "textbox", "treemap"}
    bekannt = set(facts["visuals"]) | weitere
    unbekannt = []
    for block, feld, v in _eintraege():
        t = v.get("pbip_type")
        if t in KEINE_TYPNAMEN:
            continue
        if t not in bekannt:
            unbekannt.append(f"{block}.{feld}.{v['visual_id']}: '{t}'")
    assert not unbekannt, (
        "pbip_type steht nicht im offiziellen Katalog:\n  " + "\n  ".join(unbekannt))


def test_jeder_block_hat_mindestens_ein_zeichenbares_visual_oder_sagt_warum_nicht():
    """Ein Block ohne einzige Idiom-Bruecke kann von keiner Seite gerendert werden.

    Das ist heute fuer mehrere Bloecke der Fall und ausdruecklich erlaubt — aber
    nachgehalten, nicht still. Waechst die Liste, ist das eine Verschlechterung; wird
    sie kuerzer, gehoert dieser Test nachgezogen.
    """
    ohne = sorted(
        b["block_id"] for b in _registry()["information_blocks"]
        if not any(v.get("idiom") for v in (b.get("allowed_visuals") or [])))
    # Gemessen 08.09.2026: 3 der 10 Bloecke. Ihre erlaubten Visuals sind Formen, die die
    # Bibliothek bewusst nicht nativ fuehrt (Histogramm-Baender, Ausnahmelisten,
    # Handlungskarten) — nachzulesen je Idiom in `powerbi_native.reason` mit Datum.
    erwartet = ["distribution_spread", "exception_list", "prescriptive_action"]
    assert ohne == erwartet, (
        f"Bloecke ohne zeichenbares Visual: {ohne}, nachgehalten: {erwartet}. "
        "Bei mehr: eine Bruecke ist verloren gegangen. Bei weniger: diese Liste nachziehen.")


COMPONENTS = REPO_ROOT / "core" / "templates" / "page_templates" / "components"


def test_jede_komponenten_vorlage_nennt_nur_governte_bloecke():
    """`components/*.json` beschreiben Seitenkompositionen. Bis 08.09.2026 nannten sie
    unter `visuals` frei gewaehlte Woerter (`kpi_cards`, `trend_main`, `driver_cards`,
    `decomposition_or_bridge`, `ranking_table`, `matrix_breakdown`) — sechs Namen, die
    in keinem Register standen und deshalb nichts binden konnten. Seit v2 heisst das
    Feld `blocks` und fuehrt `block_id`s aus `visual_registry.yaml`.

    Das alte Feld ist ausdruecklich verboten: eine Vorlage, die wieder `visuals` fuehrt,
    ist auf das ungebundene Vokabular zurueckgefallen und wuerde von diesem Test sonst
    schlicht nicht gelesen.
    """
    gueltig = {b["block_id"] for b in _registry()["information_blocks"]}
    dateien = sorted(COMPONENTS.glob("*.json"))
    assert dateien, f"{COMPONENTS} fuehrt keine Vorlage — der Test waere blind"
    for f in dateien:
        d = json.loads(f.read_text(encoding="utf-8"))
        for s in d["layout"]["sections"]:
            assert "visuals" not in s, (
                f"{f.name}/{s['id']}: `visuals` ist das alte, ungebundene Vokabular — `blocks` nennt "
                f"Informationsbloecke aus visual_registry.yaml")
            unbekannt = [b for b in s["blocks"] if b not in gueltig]
            assert not unbekannt, f"{f.name}/{s['id']}: keine Bloecke der Registry: {unbekannt}"
