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


# --------------------------------------------------------------------------- #
# Steuerelemente (09.09.2026): der Vertrag wird geprueft, nicht nur geschrieben #
# --------------------------------------------------------------------------- #
# Ein Steuerelement zeigt nichts, es aendert was die anderen zeigen — deshalb steht es
# nicht unter `information_blocks`. Diese Tests halten fest, dass der Abschnitt seine
# eigenen Zusagen einhaelt und nicht zu einem Block zurueckdriftet.


def _controls() -> list[dict]:
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8")).get("controls", [])


def test_the_registry_has_a_controls_section_and_it_is_not_a_block():
    """Kein Steuerelement traegt Block-Felder — sonst waere die Trennung nur Kosmetik."""
    controls = _controls()
    assert controls, "kein Steuerelement deklariert"
    block_felder = {"required_inputs", "allowed_visuals", "forbidden_visuals", "primary_layer"}
    for c in controls:
        assert not (set(c) & block_felder), (
            f"{c['control_id']} traegt Block-Felder {sorted(set(c) & block_felder)} — "
            f"dann gehoert es unter information_blocks oder die Felder weg")


def test_every_control_names_a_slot_the_page_manifest_actually_has():
    """Ein Steuerelement ohne Platz auf der Seite ist ein Eintrag ohne Aufrufer."""
    manifest = yaml.safe_load(
        (REPO_ROOT / "core/templates/page_templates/template_manifest.yaml").read_text(
            encoding="utf-8"))
    slots: set[str] = set()

    def lauf(o):
        nonlocal slots
        if isinstance(o, dict):
            for k, v in o.items():
                if k.endswith("_slots") and isinstance(v, list):
                    slots |= {x if isinstance(x, str) else x.get("slot_id") for x in v}
                lauf(v)
        elif isinstance(o, list):
            for v in o:
                lauf(v)

    lauf(manifest)
    slots.discard(None)
    for c in _controls():
        for slot in c["slot_compatibility"]:
            assert slot in slots, (
                f"{c['control_id']} nennt Slot '{slot}', den keine Seitenvariante fuehrt; "
                f"bekannt sind u. a. {sorted(s for s in slots if s)[:8]}")


def test_a_control_realization_names_a_real_pbip_type_and_never_invents_one():
    """Gemessen 09.09.2026: ein Feldparameter ist KEIN Visualtyp.

    Er ist eine berechnete Tabelle im Modell, und Power BI erzeugt dazu einen gewoehnlichen
    Slicer (MS Learn, power-bi-field-parameters). Der offizielle Katalogauszug fuehrt
    entsprechend keinen Parameter-Typ. Wer hier `fieldParameter` schriebe, erfaende ihn.
    """
    bekannt = set(json.loads(FACTS.read_text(encoding="utf-8")).get("visuals", {}))
    for c in _controls():
        r = c["realization"]
        typ = r["report"]["pbip_type"]
        assert typ == "slicer" or typ in bekannt, f"{c['control_id']}: {typ} ist kein Kernvisual"
        assert "fieldParameter" not in json.dumps(r), (
            f"{c['control_id']} nennt einen Visualtyp `fieldParameter`, den es nicht gibt")
        # Die Dreiteilung ist der Punkt: Modell, Bericht, Bindung. Faellt eine weg, dreht
        # der Leser an einem Knopf ohne Wirkung.
        assert set(r) == {"model", "report", "binding"}, (
            f"{c['control_id']}: realization braucht model + report + binding, hat {sorted(r)}")


def test_the_granularity_switch_keeps_the_distinction_that_makes_it_necessary():
    """Slicer filtert Zeilen, Feldparameter tauscht das Feld — der Unterschied ist die Substanz."""
    g = next(c for c in _controls() if c["control_id"] == "granularity_switch")
    regeln = {r["rule_id"]: r for r in g["quality_rules"]}
    assert "not_a_filter" in regeln and regeln["not_a_filter"]["severity"] == "error"
    # Er ist ein Slicer und zaehlt deshalb gegen die Obergrenze der Seite.
    assert regeln["counts_against_max_slicers"]["severity"] == "error"
    assert "NAMEOF" in g["realization"]["model"]["dax_shape"]


def test_a_contract_only_control_says_so_and_names_the_gap():
    """Ein Vertrag ohne Emitter ist in Ordnung — ein Vertrag, der so tut als gaebe es einen, nicht.

    Gemessen 09.09.2026: `tooling/superversion/targets/tmdl.py` fuehrt kein `calculated`,
    kein `NAMEOF` und keine `calculationGroup`. Die Modell-Haelfte des Feldparameters
    existiert also nicht, und genau das steht im Eintrag.
    """
    tmdl = (REPO_ROOT / "tooling/superversion/targets/tmdl.py").read_text(encoding="utf-8")
    kann_berechnete_tabellen = any(t in tmdl for t in ("NAMEOF", "calculationGroup"))
    for c in _controls():
        if c.get("emission_status") != "contract_only":
            continue
        assert c.get("emission_gap"), f"{c['control_id']}: contract_only ohne benannte Luecke"
        assert not kann_berechnete_tabellen, (
            f"{c['control_id']} steht auf contract_only, aber der TMDL-Emitter kann inzwischen "
            f"berechnete Tabellen — die Luecke ist zu, der Eintrag veraltet.")
