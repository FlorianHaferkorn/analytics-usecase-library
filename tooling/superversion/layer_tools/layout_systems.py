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

# Die sieben SUCCESS-Gruppen (IBCS 1.2). Reihenfolge = die des Standards, nicht
# alphabetisch — so liest sich der Bericht wie die Vorlage.
SUCCESS = ("SAY", "UNIFY", "CONDENSE", "CHECK", "EXPRESS", "SIMPLIFY", "STRUCTURE")

# Bekannte Herkuenfte ausser IBCS. Sie sind KEIN Mangel: eine Regel aus Cleveland &
# McGill oder WCAG gilt unabhaengig vom gewaehlten Layout-System und bleibt beim
# Wechsel stehen. Genau diese Unterscheidung ist der Zweck dieser Sicht.
_ANDERE_HERKUNFT = ("Few", "Tufte", "Cleveland", "WCAG", "ISO", "IEC", "Shneiderman",
                    "Microsoft", "Miller")

_IBCS_CODE = re.compile(
    r"\b(SAY|UNIFY|CONDENSE|CHECK|EXPRESS|SIMPLIFY|STRUCTURE)\b\s*([A-Z]\d+)?",
    re.IGNORECASE)


@dataclass(frozen=True)
class Regel:
    rule_id: str
    quelle_datei: str
    herkunft: str          # der rohe `source`-Text
    ibcs: bool
    success_gruppe: Optional[str]
    ibcs_code: Optional[str]

    @property
    def fremdstandard(self) -> Optional[str]:
        for name in _ANDERE_HERKUNFT:
            if name.lower() in self.herkunft.lower():
                return name
        return None


def _klassifiziere(rule_id: str, datei: str, source: str) -> Regel:
    ist_ibcs = "ibcs" in source.lower()
    gruppe = code = None
    if ist_ibcs:
        # Nur innerhalb des IBCS-Teils suchen: „S9 — IBCS UNIFY U4" soll U4 finden,
        # „S11 — Tufte; CHECK" darf keine IBCS-Gruppe erfinden.
        ab_ibcs = source[source.lower().index("ibcs"):]
        if treffer := _IBCS_CODE.search(ab_ibcs):
            gruppe = treffer.group(1).upper()
            code = treffer.group(2)
    return Regel(rule_id, datei, source.strip(), ist_ibcs, gruppe, code)


def sammle() -> list[Regel]:
    """Alle Regeln mit Herkunft aus den drei vorhandenen Speichern."""
    regeln: list[Regel] = []

    registry = yaml.safe_load((_TPL / "visual_registry.yaml").read_text(encoding="utf-8")) or {}
    for block in registry.get("information_blocks") or []:
        for r in block.get("quality_rules") or []:
            if isinstance(r, dict) and r.get("source"):
                regeln.append(_klassifiziere(
                    f"{block.get('block_id')}/{r.get('rule_id')}",
                    "visual_registry.yaml", str(r["source"])))

    rubrik = yaml.safe_load((_TPL / "tokens" / "boutique_craft_rubric.yaml").read_text(
        encoding="utf-8")) or {}
    for dim in rubrik.get("dimensions") or []:
        for r in dim.get("rules") or []:
            if isinstance(r, dict):
                quelle = str(r.get("source") or r.get("rationale") or r.get("statement") or "")
                regeln.append(_klassifiziere(str(r.get("id")), "boutique_craft_rubric.yaml", quelle))

    design = yaml.safe_load((_TPL / "design_rules.yaml").read_text(encoding="utf-8")) or {}
    for r in design.get("rules") or []:
        if isinstance(r, dict):
            quelle = str(r.get("source") or r.get("description") or "")
            regeln.append(_klassifiziere(str(r.get("id")), "design_rules.yaml", quelle))

    return regeln


def abdeckung(regeln: list[Regel]) -> dict[str, list[str]]:
    """SUCCESS-Gruppe → Regel-IDs, die sie belegen. Leere Gruppen bleiben leer."""
    out: dict[str, list[str]] = {g: [] for g in SUCCESS}
    for r in regeln:
        if r.ibcs and r.success_gruppe in out:
            out[r.success_gruppe].append(r.rule_id)
    return out


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python tooling/superversion/layer_tools/layout_systems.py",
        description="Herkunftssicht auf die governten Regeln: IBCS vs. Hausregel (L6).")
    parser.add_argument("--strict", action="store_true",
                        help="rot, wenn eine SUCCESS-Gruppe voellig unbelegt ist "
                             "(heute bewusst NICHT der Standard — die Luecken sind bekannt "
                             "und werden schrittweise geschlossen)")
    args = parser.parse_args(argv)

    regeln = sammle()
    ibcs = [r for r in regeln if r.ibcs]
    fremd = [r for r in regeln if not r.ibcs and r.fremdstandard]
    haus = [r for r in regeln if not r.ibcs and not r.fremdstandard]

    print(f"[layout-systems] {len(regeln)} Regeln mit Herkunft aus 3 Speichern")
    print(f"  IBCS-abgeleitet : {len(ibcs):3}  (austauschbar beim Wechsel des Layout-Systems)")
    print(f"  Fremdstandard   : {len(fremd):3}  (Few/Tufte/Cleveland/WCAG/ISO — bleiben stehen)")
    print(f"  Hausregel       : {len(haus):3}  (ALUCA-eigen)")
    print()
    print("  SUCCESS-Abdeckung (IBCS 1.2, 7 Gruppen):")
    leer = []
    for gruppe, treffer in abdeckung(regeln).items():
        if treffer:
            print(f"    {gruppe:10} {len(treffer):2} — {', '.join(sorted(treffer)[:3])}"
                  + (" …" if len(treffer) > 3 else ""))
        else:
            print(f"    {gruppe:10}  0 — nicht belegt")
            leer.append(gruppe)
    codes = sorted({r.ibcs_code for r in ibcs if r.ibcs_code})
    print(f"\n  konkrete IBCS-Regelcodes: {', '.join(codes) if codes else 'keine'}")
    # Eine IBCS-Regel ohne SUCCESS-Gruppe ist nicht falsch, aber sie faellt aus der
    # Abdeckungsrechnung heraus — man sieht ihr nicht an, welchen Teil des Standards
    # sie belegt. Das ist die billigste offene Verbesserung und deshalb benannt.
    ohne_gruppe = sorted(r.rule_id for r in ibcs if not r.success_gruppe)
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
