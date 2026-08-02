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
    # BELEGSTAND, ausdruecklich: die Scope-Aussage stammt aus Suchauszuegen
    # (iso.org/standard/88366.html, ibcs.com/iso-24896/), NICHT aus dem gelesenen
    # Normtext — `iso.org` ist in dieser Umgebung gesperrt und der Text
    # kostenpflichtig. Die Gruppenliste ist deshalb eine *Annahme mit Quelle*, keine
    # Messung. Wer sie bestaetigt oder korrigiert, tut das in L14 (Frage B1).
    groups=("UNIFY", "CHECK"),
    marker="iso 24896",
    derives_from="ibcs",
    note="Veroeffentlicht 11.06.2026. Deckt laut Suchbeleg im Kern UNIFY und CHECK ab "
         "— Scope NICHT am Normtext geprueft (iso.org gesperrt, Text kostenpflichtig).",
)

SYSTEMS: dict[str, LayoutSystem] = {s.key: s for s in (IBCS, ISO_24896)}

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


def _klassifiziere(rule_id: str, datei: str, source: str,
                   system: LayoutSystem = IBCS) -> Regel:
    basis = SYSTEMS.get(system.derives_from) if system.derives_from else None
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
                regeln.append(_klassifiziere(str(r.get("id")), "boutique_craft_rubric.yaml", quelle, system))

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
    ibcs = [r for r in regeln if r.vom_system]
    fremd = [r for r in regeln if not r.vom_system and r.fremdstandard]
    haus = [r for r in regeln if not r.vom_system and not r.fremdstandard]

    print(f"[layout-systems] System: {system.label}")
    if system.note:
        print(f"  Hinweis: {system.note}")
    print(f"  {len(regeln)} Regeln mit Herkunft aus 3 Speichern")
    print(f"  System-abgeleitet: {len(ibcs):3}  (austauschbar beim Wechsel des Layout-Systems)")
    print(f"  Fremdstandard   : {len(fremd):3}  (Few/Tufte/Cleveland/WCAG/ISO — bleiben stehen)")
    print(f"  Hausregel       : {len(haus):3}  (ALUCA-eigen)")
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
    codes = sorted({r.code for r in ibcs if r.code})
    print(f"\n  konkrete IBCS-Regelcodes: {', '.join(codes) if codes else 'keine'}")
    # Eine IBCS-Regel ohne SUCCESS-Gruppe ist nicht falsch, aber sie faellt aus der
    # Abdeckungsrechnung heraus — man sieht ihr nicht an, welchen Teil des Standards
    # sie belegt. Das ist die billigste offene Verbesserung und deshalb benannt.
    ohne_gruppe = sorted(r.rule_id for r in ibcs if not r.gruppe)
    if ohne_gruppe:
        print(f"  IBCS-Regeln ohne SUCCESS-Gruppe: {len(ohne_gruppe)} "
              f"({', '.join(ohne_gruppe[:4])}{' …' if len(ohne_gruppe) > 4 else ''}) "
              f"— `source` um die Gruppe ergaenzen, dann zaehlen sie mit")

    if leer and args.strict:
        print(f"\n[layout-systems] FAIL — unbelegte SUCCESS-Gruppen: {', '.join(leer)}")
        return 1
    if leer:
        print(f"\n[layout-systems] OK (advisory) — unbelegt: {', '.join(leer)}. "
              f"Mit --strict wird das rot.")
    else:
        print("\n[layout-systems] OK — alle SUCCESS-Gruppen belegt.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
