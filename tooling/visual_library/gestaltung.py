"""Gestaltungsregeln der Visual Library als Funktionen (Felder aus `_gestaltungsregeln.yaml`).

Die Regeln stehen als Felder im Register; hier stehen die Entscheidungen, die ein Generator, das Cockpit oder ein Test
daraus ableitet. Die Vega-Lite-Templates rechnen dieselben Entscheidungen im Browser nach (Signal `_beschriftet`,
Transformation `_ybasis`); `tests/test_gestaltungsregeln.py` stellt Funktion und gerendertes Template gegeneinander.

    werteachse(werte, ziel, alarm, klasse)   Basis der Werteachse: 0 oder angepasst mit Achsenbruch
    beschriftet(kategorien)                  trägt der Chart Datenbeschriftungen? (W2)
    achsen_bei_beschriftung(beschriftet)     Wertegitter und Werteachse an oder aus (W2)
    zebra_an(zeilen, spalten, art)           Zebra-Streifen einer Tabelle (W3)
    eckenradius(profil, pack_wert)           Radius der Balkenenden im Profil (W1)
    marke_lesbar(farbe)                      erreicht eine Marke 3:1 auf Weiß?

Reines Modul: liest nur das Register, schreibt nichts.
"""
from __future__ import annotations

import functools
import math
from pathlib import Path
from typing import Any, Iterable, Optional

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTER = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library" / "_gestaltungsregeln.yaml"


@functools.lru_cache(maxsize=1)
def _register_text() -> str:
    return REGISTER.read_text(encoding="utf-8")


def register() -> dict[str, Any]:
    """Das Register (je Aufruf eine frische Kopie)."""
    return yaml.safe_load(_register_text())


def regel(name: str) -> dict[str, Any]:
    return register()["regeln"][name]


def _zahlen(werte: Iterable[Any]) -> list[float]:
    out: list[float] = []
    for v in werte:
        if isinstance(v, bool) or v is None:
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if not math.isnan(f) and math.isfinite(f):
            out.append(f)
    return out


def werteachse(werte: Iterable[Any], ziel: Optional[float] = None, alarm: Optional[float] = None,
               klasse: str = "null_oder_angepasst") -> dict[str, Any]:
    """Basis der Werteachse nach Regel `werteachse_basis`.

    Rückgabe {basis: "null" | "angepasst" | "daten" | "index" | "frei", untergrenze: float | None, achsenbruch: bool,
    spannweite_anteil: float | None}. `untergrenze` ist der Wert, den die Achse mindestens einschließt (0 oder knapp
    unter dem kleinsten Wert); die Templates rechnen dieselbe Zahl als `_ybasis`."""
    r = regel("werteachse_basis")
    if klasse == "null":
        return {"basis": "null", "untergrenze": 0.0, "achsenbruch": False, "spannweite_anteil": None}
    if klasse == "angepasst":
        return {"basis": "daten", "untergrenze": None, "achsenbruch": False, "spannweite_anteil": None}
    if klasse == "index":
        return {"basis": "index", "untergrenze": None, "achsenbruch": False, "spannweite_anteil": None}
    if klasse in ("position", "entfaellt"):
        return {"basis": "frei", "untergrenze": None, "achsenbruch": False, "spannweite_anteil": None}
    if klasse != "null_oder_angepasst":
        raise KeyError(f"unbekannte Klasse {klasse!r} (Register werteachse_basis.klassen)")
    alle = _zahlen([*werte, ziel, alarm])
    if not alle:
        return {"basis": "null", "untergrenze": 0.0, "achsenbruch": False, "spannweite_anteil": None}
    lo, hi = min(alle), max(alle)
    top = max(abs(lo), abs(hi))
    anteil = (hi - lo) / top if top > 0 else None
    if anteil is not None and anteil < float(r["schwelle_spannweite"]):
        abstand = max((hi - lo) * float(r["abstand_unten"]), top * 0.01)
        return {"basis": "angepasst", "untergrenze": lo - abstand, "achsenbruch": True, "spannweite_anteil": anteil}
    return {"basis": "null", "untergrenze": 0.0, "achsenbruch": False, "spannweite_anteil": anteil}


def beschriftet(kategorien: int) -> bool:
    """Trägt ein Chart mit `kategorien` gezeichneten Kategorien Datenbeschriftungen? (W2, Signal `_beschriftet`)."""
    return int(kategorien) < int(regel("beschriftung_gitter")["schwelle_kategorien"])


def achsen_bei_beschriftung(ist_beschriftet: bool) -> dict[str, bool]:
    """Wertegitter und Werteachse nach W2: beschriftet → beide aus; sonst beide an."""
    return {"wertegitter": not ist_beschriftet, "werteachse": not ist_beschriftet}


def zebra_an(zeilen: int, spalten: int, art: Optional[str] = None) -> bool:
    """Zebra-Streifen nach W3: ab `min_zeilen` Zeilen und `min_spalten` Spalten, nie bei Heatmap oder Datenbalken."""
    r = regel("zebra")
    if art is not None and art in r["aus_bei"]:
        return False
    return int(zeilen) >= int(r["min_zeilen"]) and int(spalten) >= int(r["min_spalten"])


def eckenradius(profil: str, pack_wert: Optional[int]) -> int:
    """Radius der Balkenenden: der Pack-Wert, gedeckelt durch das Profil (W1; ibcs 0)."""
    wert = int(pack_wert or 0)
    deckel = (regel("eckenradius").get("profil_max") or {}).get(profil)
    return min(wert, int(deckel)) if deckel is not None else wert


@functools.lru_cache(maxsize=1)
def _contrast():
    """contrast.py derselben Bibliothek (Tool-Reuse), per Dateipfad geladen wie in render._contrast."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("visual_library_contrast_gestaltung",
                                                  Path(__file__).with_name("contrast.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def kontrast(farbe: str, grund: str = "#FFFFFF") -> float:
    """WCAG-2.x-Kontrast zweier Hex-Farben, ungerundet (contrast.contrast_ratio_exact: Schwellen nie gerundet)."""
    return float(_contrast().contrast_ratio_exact(farbe, grund))


def marke_lesbar(farbe: str, grund: str = "#FFFFFF") -> bool:
    """Erreicht eine Marke den Mindestkontrast der Regel `markenkontrast` (3:1)?"""
    return kontrast(farbe, grund) >= float(regel("markenkontrast")["min_kontrast"])
