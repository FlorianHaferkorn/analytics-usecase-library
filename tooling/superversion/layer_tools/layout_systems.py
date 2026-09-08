"""layer_tools.layout_systems — Herkunftssicht auf die governten Regeln (L6).

Ein Layer-Tool neben `visual_library.py` und `design_tokens.py`. Es legt **keinen
neuen Regelspeicher** an, sondern liest die drei vorhandenen und beantwortet die
Frage, die das Plugin-Zielbild stellt:

    Welche unserer Regeln stammen aus IBCS — und sind damit beim Wechsel des
    Layout-Systems austauschbar — und welche sind Hausregel und bleiben?

Warum ueberhaupt eine Sicht statt einer Datei
---------------------------------------------
Der Konzeptentwurf schlug `layout_systems/ibcs/rules.yaml` vor. Gemessen am
01.08.2026 waere das der **fuenfte** Ort fuer dieselbe Sache gewesen:

  * `visual_registry.yaml`         — `quality_rules` je Informationsblock (11 IBCS-Bezuege)
  * `design_rules.yaml`            — formale Constraints (0 IBCS-Bezuege: Hausregeln)
  * `tokens/boutique_craft_rubric.yaml` — 30 Regeln / 6 Dimensionen (7 IBCS-Bezuege)
  * lebende Validatoren (`title_policy`, `check_deviation_display`, `check_forbidden_charts`)

Jede dieser Quellen traegt ihre Herkunft bereits im Feld `source`. Was fehlte, war
nicht die Information, sondern ihre Auswertbarkeit.

Was die Sicht sichtbar macht
----------------------------
IBCS ordnet seine 98 Regeln in sieben Gruppen — **SUCCESS**: Say, Unify, Condense,
Check, Express, Simplify, Structure. Gegen diese Gliederung laesst sich zeigen, welche
Teile des Standards wir heute abdecken und welche gar nicht vorkommen. Beim ersten
Lauf: vier von sieben Gruppen belegt, und nur zwei konkrete Regelcodes (U4, E3).

Das ist kein Vorwurf an das Repo — es ist die Ausgangslage, gegen die sich Fortschritt
messen laesst. Ein Layout-System, das seine eigene Abdeckung nicht kennt, kann nicht
sagen, was ein Wechsel zu einem zweiten System kosten wuerde.

Reines Lesen. Kein Urteil ueber Regelqualitaet — nur Herkunft und Abdeckung.
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[3]
_TPL = _REPO_ROOT / "core" / "templates" / "page_templates"

# ─────────────────────────────────────────────────────────────────────────────
# Layout-Systeme als Plugin (Task L6/L7)
#
# Bis zum 02.08.2026 war `SUCCESS` hier eine Konstante — das Konzept nannte IBCS ein
# „Plugin", der Code kannte aber nur eines. Ein Plugin-Mechanismus mit genau einer
# Instanz ist keiner; er ist eine Behauptung, die beim zweiten System auffliegt.
#
# Ein Layout-System ist deshalb jetzt ein Deskriptor: wie heisst es, in welche Gruppen
# ordnet es seine Regeln, und woran erkennt man in einem `source`-Feld, dass eine Regel
# von ihm stammt. Alles andere (Sammeln, Klassifizieren, Abdeckung) ist systemneutral.
@dataclass(frozen=True)
class LayoutSystem:
    """Ein austauschbares Notations-/Layout-System."""
    key: str
    label: str
    groups: tuple[str, ...]
    marker: str          # Kleinbuchstaben-Marker im `source`-Feld
    note: str = ""
    # Ein System kann von einem anderen ABLEITEN. Ohne diese Beziehung meldet der
    # Schnitt-Test Unsinn, und das ist beim ersten Lauf am 02.08.2026 passiert:
    # gegen ISO 24896 waren 0 von 72 Regeln „system-abgeleitet", weil kein einziges
    # `source`-Feld im Repo die Zeichenfolge „ISO 24896" enthaelt — unsere Herkunft
    # ist durchgehend in IBCS-Vokabular geschrieben.
    #
    # Das war kein Fehler der Daten, sondern eine Luecke im Modell: eine Regel
    # „IBCS UNIFY U4" IST inhaltlich auch ISO-24896-Stoff, weil ISO 24896 auf den
    # IBCS-Vorschlaegen beruht. Ein Herkunftsmodell, das nur einen Ursprung je Regel
    # kennt, kann „dieselbe Regel, zwei Systeme" nicht ausdruecken — und meldet dann
    # eine Migrationsluecke, die es nicht gibt.
    derives_from: Optional[str] = None   # key des Basissystems
    # Ein System kann seine Regeln nicht an einem Marker erkennen, sondern daran, dass
    # sie **keinem anderen** gehoeren. Genau das ist eine Hausregel: sie hat keine
    # Fremdherkunft, weil wir sie selbst aufgestellt haben. Bis zum 03.08.2026 war das
    # keine Systemeigenschaft, sondern eine Restmenge im Bericht — mit der Folge, dass
    # IBCS eine Gruppen-Abdeckung bekam und das eigene System eine blosse Zahl.
    residual: bool = False
    # Woher kommt die Gruppe einer Regel? Bei IBCS steht sie im `source`-Text
    # („IBCS UNIFY U4"). Bei einem residualen System steht sie nirgends im Text — wohl
    # aber in der STRUKTUR des Speichers: die Rubrik ordnet jede Regel bereits einer
    # Dimension zu. `sammle()` hat diese Zuordnung schon gelesen und weggeworfen.
    gruppe_aus_struktur: bool = False

    def owns(self, source: str, basis: Optional["LayoutSystem"] = None) -> bool:
        """Gehoert eine Regel diesem System — direkt oder ueber die Ableitung?"""
        text = source.lower()
        if self.marker in text:
            return True
        if basis is not None and basis.marker in text:
            # Geerbt gilt nur, wenn die Regel in einer Gruppe steht, die dieses
            # System uebernommen hat. Sonst wuerde eine SAY-Regel bei ISO 24896
            # mitzaehlen, obwohl der Standard SAY gar nicht fuehrt.
            ab = text[text.index(basis.marker):]
            if any(re.search(rf"\b{g}\b", ab, re.IGNORECASE) for g in self.groups):
                return True
            # Manche Quellen nennen nur den CODE, nicht die Gruppe („S9 — IBCS U4").
            # Ohne diesen Zweig fiel genau eine Regel still heraus: der Schnitt-Test
            # meldete UNIFY 6 statt 7, und die Differenz sah nach einer echten
            # Migrationsluecke aus, war aber ein Erkennungsfehler. Die code→Gruppe-
            # Tabelle ist zu diesem Zeitpunkt bereits gelernt (`sammle()` ruft
            # `_lerne_codes()` vor der Klassifikation) — sie wird hier mitbenutzt
            # statt ein zweites Mal geraten.
            for kandidat in re.findall(r"\b([A-Za-z]\d+)\b", ab):
                if _CODE_ZU_GRUPPE.get(kandidat.upper()) in self.groups:
                    return True
        return False


IBCS = LayoutSystem(
    key="ibcs",
    label="IBCS 1.2 (SUCCESS)",
    # Reihenfolge = die des Standards, nicht alphabetisch — so liest sich der Bericht
    # wie die Vorlage.
    groups=("SAY", "UNIFY", "CONDENSE", "CHECK", "EXPRESS", "SIMPLIFY", "STRUCTURE"),
    marker="ibcs",
    note="98 Regeln in sieben Gruppen. Fassung 2.0 ist erschienen und auf ISO 24896 "
         "ausgerichtet — die Umstellung haengt an Task L14 (Delta + Lizenz ungeklaert).",
)

ISO_24896 = LayoutSystem(
    key="iso24896",
    label="ISO 24896:2026 (Notation for business reporting)",
    # ISO 24896 beruht laut ibcs.com auf den IBCS-Vorschlaegen, **im Kern auf UNIFY und
    # CHECK** — nicht auf allen sieben Gruppen. Genau diese engere Fassung macht das
    # System zum brauchbaren Schnitt-Test: es zeigt, welche unserer Regeln bei einem
    # Wechsel heimatlos wuerden.
    #
    # NACHGEPRUEFT am 02.08.2026 (L14/B1), zweite unabhaengige Suche: die Zuordnung
    # „mainly the UNIFY and CHECK parts of IBCS' SUCCESS formula" ist bestaetigt.
    #
    # Wichtiger als die Bestaetigung ist, was dabei auffiel: **IBCS 2.0 gliedert sich
    # nicht mehr nach SUCCESS**, sondern in die Teile **Notation** und **Composition** —
    # und ISO 24896 IST der Notation-Teil. Fuer dieses Modul heisst das: beim Wechsel auf
    # 2.0 aendert sich nicht nur der Inhalt, sondern die FORM des Gruppenvokabulars.
    # Genau dafuer wurde der Deskriptor gebaut; ein fest verdrahtetes SUCCESS haette den
    # Wechsel gar nicht ausdruecken koennen.
    #
    # BELEGSTAND, ausdruecklich: die Scope-Aussage stammt aus Suchauszuegen
    # (iso.org/standard/88366.html, ibcs.com/iso-24896/), NICHT aus dem gelesenen
    # Normtext — `iso.org` ist in dieser Umgebung gesperrt und der Text
    # kostenpflichtig. Die Gruppenliste ist deshalb eine *Annahme mit Quelle*, keine
    # Messung. Wer sie bestaetigt oder korrigiert, tut das in L14 (Frage B1).
    groups=("UNIFY", "CHECK"),
    marker="iso 24896",
    derives_from="ibcs",
    note="Veroeffentlicht 11.06.2026. ISO 24896 IST der Notation-Teil von IBCS 2.0 "
         "(zwei unabhaengige Belege, 02.08.2026); die Zuordnung auf UNIFY+CHECK bezieht "
         "sich auf die SUCCESS-Gliederung von 1.2. Normtext nicht gelesen (iso.org und "
         "der freie ISO-Auszug sind beide durch die Egress-Policy gesperrt).",
)

def _rubrik_dimensionen() -> tuple[str, ...]:
    """Die Gruppen des Hausystems — GELESEN aus der Rubrik, nicht hier gepflegt.

    Eine zweite Liste waere die Manifest-Dublette in klein: zwei Stellen mit einer
    Meinung ueber dieselbe Sache. Kommt eine Dimension dazu, erscheint sie im Bericht,
    ohne dass jemand hier nachzieht. Fehlt die Datei, wirft es — eine leere Gruppenliste
    saehe aus wie „nichts zu berichten".
    """
    p = _TPL / "tokens" / "boutique_craft_rubric.yaml"
    doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    dims = tuple(str(d["id"]).upper() for d in doc.get("dimensions") or [] if d.get("id"))
    if not dims:
        raise ValueError(f"{p} fuehrt keine `dimensions` — das Hausystem haette keine Gruppen.")
    return dims


HAUS = LayoutSystem(
    key="haus",
    label="ALUCA-Hausystem (Boutique Craft)",
    # Die sechs Dimensionen der Craft-Rubrik. Sie sind die gelebte Gliederung des
    # eigenen Systems — mit Gewichten, Severity und `machine_hint` je Regel, also
    # feiner ausgearbeitet als unsere IBCS-Bezuege, die nur Herkunftsvermerke sind.
    groups=_rubrik_dimensionen(),
    marker="",            # kein Marker: Zugehoerigkeit ergibt sich aus dem Fehlen anderer
    residual=True,
    gruppe_aus_struktur=True,
    note="Eigenes System, kein Fremdstandard. 33 Regeln gegen 16 mit IBCS-Bezug; auf der "
         "Visualseite dagegen duenn — 2 von 26 Registry-Visuals sind hauseigen, 1 ist "
         "IBCS (S9), 23 stammen aus Fremdstandards (Cleveland & McGill allein 15). Bis "
         "03.08.2026 war es hier keine Systeminstanz, sondern die Restmenge des "
         "IBCS-Berichts.",
)

SYSTEMS: dict[str, LayoutSystem] = {s.key: s for s in (IBCS, ISO_24896, HAUS)}

# Rueckwaertskompatibel: der frueher exportierte Name bleibt gueltig.
SUCCESS = IBCS.groups

# Bekannte Herkuenfte ausser IBCS. Sie sind KEIN Mangel: eine Regel aus Cleveland &
# McGill oder WCAG gilt unabhaengig vom gewaehlten Layout-System und bleibt beim
# Wechsel stehen. Genau diese Unterscheidung ist der Zweck dieser Sicht.
_ANDERE_HERKUNFT = ("Few", "Tufte", "Cleveland", "WCAG", "ISO", "IEC", "Shneiderman",
                    "Microsoft", "Miller")

def _gruppen_regex(system: LayoutSystem) -> re.Pattern:
    """Gruppen-plus-Code-Muster fuer EIN System. Nicht mehr fest auf SUCCESS verdrahtet."""
    return re.compile(r"\b(" + "|".join(system.groups) + r")\b\s*([A-Z]\d+)?", re.IGNORECASE)


@dataclass(frozen=True)
class Regel:
    rule_id: str
    quelle_datei: str
    herkunft: str          # der rohe `source`-Text
    vom_system: bool         # gehoert dem geprueften Layout-System
    gruppe: Optional[str]
    code: Optional[str]

    @property
    def fremdstandard(self) -> Optional[str]:
        for name in _ANDERE_HERKUNFT:
            if name.lower() in self.herkunft.lower():
                return name
        return None


# Manche Herkunftsangaben nennen nur den Regelcode („S9 — IBCS U4") ohne die Gruppe.
# Die Zuordnung steht aber im Repo selbst — anderswo heisst dieselbe Regel
# „S9 — IBCS UNIFY U4". Statt aus dem Anfangsbuchstaben zu raten (S ist SAY, SIMPLIFY
# ODER STRUCTURE; C ist CONDENSE ODER CHECK) wird die Tabelle aus den ausgezeichneten
# Vorkommen GELERNT. Kein Code ohne Beleg im Repo bekommt eine Gruppe.
_CODE_ZU_GRUPPE: dict[str, str] = {}


def _lerne_codes(quellen: list[str], system: LayoutSystem = IBCS) -> None:
    """Baue code→Gruppe aus den Stellen, die BEIDES nennen."""
    _CODE_ZU_GRUPPE.clear()
    muster = re.compile(r"\b(" + "|".join(system.groups) + r")\s+([A-Z]\d+)\b", re.IGNORECASE)
    for text in quellen:
        for gruppe, code in muster.findall(text):
            _CODE_ZU_GRUPPE.setdefault(code.upper(), gruppe.upper())


_DOKTRIN = _REPO_ROOT / "studio" / "docs" / "rebuild" / "PAGE_TEMPLATE_DOCTRINE.md"


@lru_cache(maxsize=1)
def quellenmatrix() -> dict[str, str]:
    """`S1`…`S18` → Quelltext aus der Doktrin-Quellenmatrix.

    Warum das noetig ist (gemessen 03.08.2026)
    ------------------------------------------
    Die Registry schreibt ihre Herkunft als **Kuerzel**: `S2 — length encoding`.
    Wer nur nach Autorennamen sucht, findet dort keinen — und zaehlt eine Regel von
    Cleveland & McGill als hauseigen. Genau das tat die Sicht seit L6 still: die Zahl
    „33 Hausregeln" enthielt Fremdstandards, die sich hinter ihrem Kuerzel versteckt
    hatten. Es faellt erst auf, wenn das eigene System eine Systeminstanz wird und
    seine Abdeckung ausweisen muss.

    Die Aufloesung liest die **eine** Autoritaet (die Quellenmatrix der Doktrin) statt
    eine zweite Tabelle zu pflegen.
    """
    if not _DOKTRIN.is_file():
        raise ValueError(f"{_DOKTRIN} fehlt — ohne Quellenmatrix ist jedes S-Kuerzel "
                         f"unaufloesbar und wuerde als hauseigen durchgehen.")
    out: dict[str, str] = {}
    for zeile in _DOKTRIN.read_text(encoding="utf-8").splitlines():
        if m := re.match(r"\|\s*(S\d+)\s*\|([^|]+)\|", zeile):
            out[m.group(1)] = m.group(2).strip()
    if not out:
        raise ValueError(f"{_DOKTRIN} fuehrt keine Quellenmatrix-Zeilen (| S<n> | …).")
    return out


#: S-Kuerzel, deren Quelle das Haus SELBST ist. S13 ist die Meridian-Referenz — eigenes
#: Material, kein Fremdstandard. Bewusst eine kurze, benannte Ausnahme statt einer
#: Heuristik ueber den Matrixtext.
_EIGENE_KUERZEL = frozenset({"S13"})


def _fremd_ueber_kuerzel(source: str) -> bool:
    """Nennt die Herkunft ein S-Kuerzel, das auf eine FREMDE Quelle zeigt?"""
    matrix = quellenmatrix()
    for kuerzel in re.findall(r"\bS\d+\b", source):
        if kuerzel in matrix and kuerzel not in _EIGENE_KUERZEL:
            return True
    return False


def _gehoert_niemand_anderem(source: str) -> bool:
    """Keine Fremdherkunft — weder ein anderes Layout-System noch ein Fremdstandard.

    Das ist die Definition einer Hausregel, und sie ist bewusst NEGATIV: wir haben sie
    selbst aufgestellt, also traegt sie keinen fremden Marker. Sie hier auszurechnen
    statt im Bericht heisst, dass das eigene System dieselbe Behandlung bekommt wie
    IBCS — eigene Gruppen, eigene Abdeckung — statt als Rest uebrig zu bleiben.
    """
    if any(s.owns(source) for s in SYSTEMS.values() if not s.residual):
        return False
    if _fremd_ueber_kuerzel(source):
        return False
    return not any(n.lower() in source.lower() for n in _ANDERE_HERKUNFT)


def _klassifiziere(rule_id: str, datei: str, source: str,
                   system: LayoutSystem = IBCS,
                   struktur_gruppe: Optional[str] = None) -> Regel:
    basis = SYSTEMS.get(system.derives_from) if system.derives_from else None
    if system.residual:
        eigen = _gehoert_niemand_anderem(source)
        # Die Gruppe steht nicht im Text, sondern im Speicher: die Rubrik ordnet jede
        # Regel bereits einer Dimension zu. Eine Hausregel ausserhalb der Rubrik
        # (design_rules.yaml, visual_registry.yaml) hat keine — und das bleibt sichtbar,
        # statt sie in eine passende zu raten.
        g = (struktur_gruppe or "").upper() or None
        return Regel(rule_id, datei, source.strip(), eigen,
                     g if (eigen and g in system.groups) else None, None)
    ist_ibcs = system.owns(source, basis)
    gruppe = code = None
    if ist_ibcs:
        # Nur innerhalb des System-Teils suchen: „S9 — IBCS UNIFY U4" soll U4 finden,
        # „S11 — Tufte; CHECK" darf keine Gruppe erfinden.
        # Bei einem abgeleiteten System steht die Gruppe hinter dem Marker des
        # BASIS-Systems („S9 — IBCS UNIFY U4"), nicht hinter dem eigenen.
        marker = system.marker if system.marker in source.lower() else (basis.marker if basis else system.marker)
        ab_ibcs = source[source.lower().index(marker):]
        if treffer := _gruppen_regex(system).search(ab_ibcs):
            gruppe = treffer.group(1).upper()
            code = treffer.group(2)
        elif nur_code := re.search(r"\b([A-Z]\d+)\b", ab_ibcs):
            # Gruppe fehlt, Code da → NUR uebernehmen, wenn er in der gelernten Tabelle
            # steht. Die Herkunftsfelder mischen Nummerierungen: „S9 — IBCS; S11 — Tufte"
            # enthaelt hinter „IBCS" das repo-eigene Quellenkuerzel S11, das kein
            # IBCS-Regelcode ist. Ein unbelegter Code wird deshalb verworfen statt
            # gemeldet — sonst erfindet die Sicht Abdeckung, die es nicht gibt.
            if (kandidat := nur_code.group(1)) in _CODE_ZU_GRUPPE:
                code = kandidat
                gruppe = _CODE_ZU_GRUPPE[kandidat]
    return Regel(rule_id, datei, source.strip(), ist_ibcs, gruppe, code)


def sammle(system: LayoutSystem = IBCS) -> list[Regel]:
    """Alle Regeln mit Herkunft aus den drei vorhandenen Speichern."""
    regeln: list[Regel] = []
    # Erst die code→Gruppe-Tabelle aus allen Quelltexten lernen, dann klassifizieren —
    # sonst haengt das Ergebnis von der Lesereihenfolge ab.
    _lerne_codes([(_TPL / n).read_text(encoding="utf-8") for n in
                  ("visual_registry.yaml", "design_rules.yaml",
                   "tokens/boutique_craft_rubric.yaml")], system)

    registry = yaml.safe_load((_TPL / "visual_registry.yaml").read_text(encoding="utf-8")) or {}
    for block in registry.get("information_blocks") or []:
        for r in block.get("quality_rules") or []:
            if isinstance(r, dict) and r.get("source"):
                regeln.append(_klassifiziere(
                    f"{block.get('block_id')}/{r.get('rule_id')}",
                    "visual_registry.yaml", str(r["source"]), system))

    rubrik = yaml.safe_load((_TPL / "tokens" / "boutique_craft_rubric.yaml").read_text(
        encoding="utf-8")) or {}
    for dim in rubrik.get("dimensions") or []:
        for r in dim.get("rules") or []:
            if isinstance(r, dict):
                quelle = str(r.get("source") or r.get("rationale") or r.get("statement") or "")
                # Die Dimension wird durchgereicht statt verworfen — sie IST die
                # Gliederung des Hausystems und war bis 03.08.2026 die einzige
                # Information, die hier gelesen und weggeworfen wurde.
                regeln.append(_klassifiziere(str(r.get("id")), "boutique_craft_rubric.yaml",
                                             quelle, system, str(dim.get("id") or "")))

    design = yaml.safe_load((_TPL / "design_rules.yaml").read_text(encoding="utf-8")) or {}
    for r in design.get("rules") or []:
        if isinstance(r, dict):
            quelle = str(r.get("source") or r.get("description") or "")
            regeln.append(_klassifiziere(str(r.get("id")), "design_rules.yaml", quelle, system))

    return regeln


def abdeckung(regeln: list[Regel], system: LayoutSystem = IBCS) -> dict[str, list[str]]:
    """Gruppe → Regel-IDs, die sie belegen. Leere Gruppen bleiben leer."""
    out: dict[str, list[str]] = {g: [] for g in system.groups}
    for r in regeln:
        if r.vom_system and r.gruppe in out:
            out[r.gruppe].append(r.rule_id)
    return out


@dataclass(frozen=True)
class VisualEintrag:
    """Eine Visualdefinition der Registry, aus der Sicht EINES Layout-Systems."""
    block_id: str
    visual_id: str
    herkunft: str
    vom_system: bool
    ziele: tuple[str, ...]      # welche Zielwerkzeuge die Registry zuordnet


def visuelle_abdeckung(system: LayoutSystem = IBCS) -> list[VisualEintrag]:
    """Welche Visualdefinitionen groundet dieses System — und wohin bauen sie?

    Warum diese Sicht (L12, 03.08.2026)
    -----------------------------------
    L12 war als *IBCS*-Visualkatalog geschrieben. Die Messung davor hat das
    umgedreht: von 26 Visualdefinitionen der Registry traegt genau **eine** eine
    IBCS-Herkunft (S9); 15 stammen aus Cleveland & McGill (S2), der Rest aus
    Shneiderman, Few, Tufte, Munzner. Ein Katalog nur fuer IBCS haette das System
    ausgebaut, das ein Sechsundzwanzigstel stellt.

    Dieselbe Herkunftsmechanik wie bei den Regeln, eine Schicht daneben: kein
    zweiter Speicher, keine zweite Meinung — `visual_registry.yaml` bleibt die
    Autoritaet, diese Funktion liest sie nur nach System.
    """
    doc = yaml.safe_load((_TPL / "visual_registry.yaml").read_text(encoding="utf-8")) or {}
    basis = SYSTEMS.get(system.derives_from) if system.derives_from else None
    out: list[VisualEintrag] = []
    for block in doc.get("information_blocks") or []:
        for v in block.get("allowed_visuals") or []:
            quelle = str(v.get("source") or "")
            eigen = (_gehoert_niemand_anderem(quelle) if system.residual
                     else system.owns(quelle, basis))
            out.append(VisualEintrag(
                block_id=str(block.get("block_id")),
                visual_id=str(v.get("visual_id")),
                herkunft=quelle.strip(),
                vom_system=eigen,
                ziele=tuple(sorted((v.get("targets") or {}).keys())),
            ))
    return out


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python tooling/superversion/layer_tools/layout_systems.py",
        description="Herkunftssicht auf die governten Regeln: IBCS vs. Hausregel (L6).")
    parser.add_argument("--system", default="ibcs", choices=sorted(SYSTEMS),
                        help="welches Layout-System geprueft wird (L6/L7-Plugin). "
                             "Der Wechsel zeigt, welche Regeln beim Systemwechsel "
                             "heimatlos wuerden.")
    parser.add_argument("--strict", action="store_true",
                        help="rot, wenn eine SUCCESS-Gruppe voellig unbelegt ist "
                             "(heute bewusst NICHT der Standard — die Luecken sind bekannt "
                             "und werden schrittweise geschlossen)")
    args = parser.parse_args(argv)

    system = SYSTEMS[args.system]
    regeln = sammle(system)
    eigen = [r for r in regeln if r.vom_system]
    fremd = [r for r in regeln if not r.vom_system and r.fremdstandard]
    rest = [r for r in regeln if not r.vom_system and not r.fremdstandard]

    # Die Restmenge heisst nicht immer dasselbe. Prueft man IBCS, sind es die eigenen
    # Regeln; prueft man das Hausystem, sind es die Regeln der ANDEREN Systeme. Bis
    # 03.08.2026 stand hier fest „Hausregel (ALUCA-eigen)" — beim Hausystem waeren damit
    # 12 IBCS-Regeln als hauseigen ausgewiesen worden. Dieselbe Klasse wie die
    # SUCCESS-Konstante aus L6: der Sammler war systemneutral, der Bericht nicht.
    andere = ", ".join(s.label.split(" ")[0] for s in SYSTEMS.values()
                       if s.key != system.key and not s.residual)
    rest_label = ("Andere Systeme", f"{andere} — waeren beim Wechsel neu zu belegen")
    if not system.residual:
        rest_label = ("Hausregel", "ALUCA-eigen, bleibt beim Systemwechsel stehen")

    print(f"[layout-systems] System: {system.label}")
    if system.note:
        print(f"  Hinweis: {system.note}")
    print(f"  {len(regeln)} Regeln mit Herkunft aus 3 Speichern")
    bleibt = "bleibt beim Wechsel" if system.residual else "austauschbar beim Wechsel"
    print(f"  System-abgeleitet: {len(eigen):3}  ({bleibt} des Layout-Systems)")
    print(f"  Fremdstandard   : {len(fremd):3}  (Few/Tufte/Cleveland/WCAG/ISO — bleiben stehen)")
    print(f"  {rest_label[0]:16}: {len(rest):3}  ({rest_label[1]})")
    print()
    print(f"  Gruppen-Abdeckung ({system.label}, {len(system.groups)} Gruppen):")
    leer = []
    for gruppe, treffer in abdeckung(regeln, system).items():
        if treffer:
            print(f"    {gruppe:10} {len(treffer):2} — {', '.join(sorted(treffer)[:3])}"
                  + (" …" if len(treffer) > 3 else ""))
        else:
            print(f"    {gruppe:10}  0 — nicht belegt")
            leer.append(gruppe)
    kurz = system.label.split(" ")[0]
    codes = sorted({r.code for r in eigen if r.code})
    if not system.residual:
        # Regelcodes gibt es nur, wo der Standard sie vergibt. Das Hausystem nummeriert
        # in der Regel-ID selbst (BC-COLOR-01) — eine leere Code-Zeile dort waere kein
        # Befund, sondern ein Kategoriefehler.
        print(f"\n  konkrete {kurz}-Regelcodes: {', '.join(codes) if codes else 'keine'}")
    # Eine Regel ohne Gruppe ist nicht falsch, aber sie faellt aus der Abdeckungs-
    # rechnung heraus — man sieht ihr nicht an, welchen Teil des Systems sie belegt.
    ohne_gruppe = sorted(r.rule_id for r in eigen if not r.gruppe)
    if ohne_gruppe:
        woher = ("stehen ausserhalb der Craft-Rubrik und haben deshalb keine Dimension"
                 if system.residual else "`source` um die Gruppe ergaenzen, dann zaehlen sie mit")
        print(f"  {kurz}-Regeln ohne Gruppe: {len(ohne_gruppe)} "
              f"({', '.join(ohne_gruppe[:4])}{' …' if len(ohne_gruppe) > 4 else ''}) "
              f"— {woher}")

    # Visualseite — dieselbe Frage eine Schicht daneben (L12). Ohne sie waere „gleiche
    # Reife" eine Aussage ueber Regeln allein, und genau dort liegt die Schieflage nicht.
    vis = visuelle_abdeckung(system)
    eigene_vis = [v for v in vis if v.vom_system]
    print(f"\n  Visualdefinitionen: {len(eigene_vis)} von {len(vis)} tragen "
          f"{kurz}-Herkunft")
    if eigene_vis:
        for v in eigene_vis[:6]:
            ziele = ", ".join(v.ziele) if v.ziele else "KEIN Ziel zugeordnet"
            print(f"    {v.block_id:22} {v.visual_id:26} -> {ziele}")
        if len(eigene_vis) > 6:
            print(f"    … und {len(eigene_vis) - 6} weitere")
    # Ein Visual ohne Zielzuordnung ist der Katalog-Befund: die Registry sagt, es sei
    # erlaubt, aber kein Konnektor weiss, wie er es baut.
    ohne_ziel = [v.visual_id for v in eigene_vis if not v.ziele]
    if ohne_ziel:
        print(f"    ohne Zielzuordnung: {len(ohne_ziel)} "
              f"({', '.join(sorted(ohne_ziel)[:5])}"
              f"{' …' if len(ohne_ziel) > 5 else ''})")

    if leer and args.strict:
        print(f"\n[layout-systems] FAIL — unbelegte Gruppen ({kurz}): {', '.join(leer)}")
        return 1
    if leer:
        print(f"\n[layout-systems] OK (advisory) — unbelegt: {', '.join(leer)}. "
              f"Mit --strict wird das rot.")
    else:
        print(f"\n[layout-systems] OK — alle Gruppen von {kurz} belegt.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
