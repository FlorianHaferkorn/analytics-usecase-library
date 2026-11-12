"""Auswahl einer Strukturform (ADR-0029).

Zu Struktur, Frage und Knotenzahl liefert ``waehle`` die passenden Formen aus
``core/templates/page_templates/visual_library/strukturformen/`` in fester Reihenfolge:
erst Formen, für die die Frage primär ist, dann nach ``vorrang``, dann nach ID.
Rein und deterministisch; die Fälle in ``strukturform_cases.json`` frieren das Ergebnis ein.

    python tooling/visual_library/strukturform.py netz nachbarschaft 34
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
FORMEN = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library" / "strukturformen"


@dataclass(frozen=True)
class Daten:
    """Eigenschaften der Daten, die über eine Voraussetzung entscheiden."""

    masse: bool = False
    zyklen: bool = False
    wurzeln: int = 1
    start_ziel: bool = False
    kantenklassen: int = 1


@dataclass(frozen=True)
class Treffer:
    id: str
    stufe: str  # primaer | sekundaer
    vorrang: int
    reduktion_noetig: tuple[str, ...] = field(default_factory=tuple)


def _lade(name: str) -> Any:
    return yaml.safe_load((FORMEN / name).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def formen() -> dict[str, dict[str, Any]]:
    """Alle Formdateien, nach ID."""
    return {p.stem: _lade(p.name) for p in sorted(FORMEN.glob("[a-z]*.yaml"))}


@lru_cache(maxsize=1)
def vokabular() -> dict[str, Any]:
    return _lade("_vokabular.yaml")


@lru_cache(maxsize=1)
def regeln() -> dict[str, dict[str, Any]]:
    return _lade("_regeln.yaml")["regeln"]


def _voraussetzung_erfuellt(v: dict[str, Any], d: Daten) -> bool:
    if "masse" in v and v["masse"] != d.masse:
        return False
    if "zyklen" in v and v["zyklen"] != d.zyklen:
        return False
    if "wurzeln_max" in v and d.wurzeln > v["wurzeln_max"]:
        return False
    if "start_ziel" in v and v["start_ziel"] != d.start_ziel:
        return False
    return True


def _menge_passt(menge: dict[str, Any], knoten: int) -> bool:
    hi = menge.get("max")
    return menge["min"] <= knoten and (hi is None or knoten <= hi)


def waehle(struktur: str, frage: str, knoten: int, daten: Daten | None = None) -> list[Treffer]:
    """Passende Formen, beste zuerst. Leere Liste = keine Form im Katalog."""
    vok = vokabular()
    if struktur not in vok["strukturtypen"]:
        raise ValueError(f"unbekannte Struktur {struktur!r}")
    if frage not in vok["fragetypen"]:
        raise ValueError(f"unbekannte Frage {frage!r}")
    d = daten or Daten()
    treffer: list[Treffer] = []
    for fid, f in formen().items():
        if f["status"] == "deprecated" or struktur not in f["strukturtypen"]:
            continue
        if frage in f["fragen"]["primaer"]:
            stufe = "primaer"
        elif frage in f["fragen"]["sekundaer"]:
            stufe = "sekundaer"
        else:
            continue
        if not _menge_passt(f["menge"], knoten) or not _voraussetzung_erfuellt(f["voraussetzung"], d):
            continue
        noetig = ("filter_kantenklasse",) if d.kantenklassen > f["kantenklassen_max"] else ()
        treffer.append(Treffer(fid, stufe, f["vorrang"], noetig))
    return sorted(treffer, key=lambda t: (t.stufe != "primaer", t.vorrang, t.id))


def gedeckte_paare() -> set[tuple[str, str]]:
    """Struktur x Frage, für die mindestens eine Form steht (unabhängig von Menge und Daten)."""
    paare: set[tuple[str, str]] = set()
    for f in formen().values():
        for s in f["strukturtypen"]:
            for q in f["fragen"]["primaer"] + f["fragen"]["sekundaer"]:
                paare.add((s, q))
    return paare


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("struktur")
    ap.add_argument("frage")
    ap.add_argument("knoten", type=int)
    ap.add_argument("--masse", action="store_true")
    ap.add_argument("--zyklen", action="store_true")
    ap.add_argument("--wurzeln", type=int, default=1)
    ap.add_argument("--start-ziel", action="store_true")
    ap.add_argument("--kantenklassen", type=int, default=1)
    a = ap.parse_args(argv)
    d = Daten(a.masse, a.zyklen, a.wurzeln, a.start_ziel, a.kantenklassen)
    out = [t.__dict__ | {"name": formen()[t.id]["name"]} for t in waehle(a.struktur, a.frage, a.knoten, d)]
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out else 1


if __name__ == "__main__":
    sys.exit(main())
