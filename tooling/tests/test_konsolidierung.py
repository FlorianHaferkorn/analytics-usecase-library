"""Konsolidierungs-Waechter: „wie viele Stellen muss man anfassen?" als Testfrage.

Warum es diesen Test gibt
-------------------------
Am 02.08.2026 gemessen, bevor konsolidiert wurde:

  * ein neuer Visualtyp beruehrte **11** Stellen
  * **19** Dateien kannten Slot-Namen
  * die Leinwandgroesse hatte **7** unabhaengige Meinungen, davon zwei mit
    verschiedenen Werten als Default (1280 und 1920)

Aus der letzten Zeile sind an einem einzigen Tag zwei Fehler entstanden (L13, L8).
Das ist die Signatur einer Dublette: jede Seite hat recht ueber sich und unrecht ueber
die andere, und niemand merkt es, weil beide fuer sich konsistent sind.

Konsolidieren allein reicht nicht — Dubletten wachsen nach. Dieser Test macht die
**Einfachheit selbst** pruefbar: er zaehlt die Stellen und wird rot, wenn sie wieder
mehr werden. Eine Obergrenze, die man bewusst anheben muss, ist etwas anderes als eine
Zahl, die unbemerkt steigt.

Was er NICHT tut
----------------
Er verbietet keine Kopie um jeden Preis. `_canonical_mirror.py` spiegelt Meridians
Vertrag **absichtlich** verbatim (ADR-0005, durch einen Parity-Test geschuetzt), und
`vendor/` ist Fremdcode. Beide sind ausgenommen — eine Regel, die legitime Spiegel
mitverbietet, wird umgangen statt befolgt.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]

# Absichtliche Spiegel und Fremdcode. Jede Ausnahme nennt ihren Grund — eine
# Ausnahmeliste ohne Begruendungen wird zur Muellhalde.
_AUSGENOMMEN = {
    "_canonical_mirror.py": "verbatim-Spiegel von Meridians Vertrag (ADR-0005), parity-getestet",
    "vendor": "Fremdcode — wird gepinnt, nicht editiert",
    "node_modules": "Fremdcode",
    "dist": "erzeugte Artefakte",
    "tests": "Testfixtures duerfen konkrete Zahlen nennen",
    # AUSGENOMMEN, NICHT VERGESSEN: der Prototyp ist deprecated (KONZEPT_LAYOUT_SYSTEM
    # §2: „Beide Modi des page_scaffold_generator sind deprecated"). Er haelt 36 der
    # frueher 38 Leinwand-Literale. Sie dort aufzuloesen waere Arbeit an Code, der
    # wegsoll — und jede Aenderung daran ist Risiko ohne Ertrag. Faellt der Prototyp,
    # faellt diese Ausnahme mit ihm; bis dahin ist die Schuld benannt statt versteckt.
    "page_scaffold_generator": "deprecated Prototyp (36 Literale) — Schuld benannt, s. C4",
    ".git": "Versionskontrolle, kein Quellcode",
}


def _relevante_dateien(endungen=(".py",)):
    for f in _ROOT.rglob("*"):
        if f.suffix not in endungen or not f.is_file():
            continue
        if any(teil in _AUSGENOMMEN for teil in f.parts) or f.name in _AUSGENOMMEN:
            continue
        yield f


# Obergrenze = gemessener Stand nach der Konsolidierung vom 02.08.2026: **null**
# Leinwand-Literale im lebenden Code. Bewusst kein Puffer — eine Grenze, die Luft
# laesst, schuetzt nichts: die erste neue Dublette passte hinein und faellt nicht auf.
# Sie DARF steigen, aber nur bewusst und mit Begruendung im Commit.
_MAX_CANVAS_STELLEN = 0


def test_canvas_size_has_one_home():
    """Die Leinwandgroesse steht in der YAML — nicht in Python-Literalen.

    Vorher: sieben Stellen, zwei davon widersprachen sich. Jetzt liest alles
    `layer_tools/layout_grid.load()`. Der Test zaehlt die verbliebenen Literale;
    steigt die Zahl, ist eine neue Meinung entstanden.
    """
    treffer: list[str] = []
    muster = re.compile(r"\b(1920|1080|1280|720)\b")
    for f in _relevante_dateien():
        for nr, zeile in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            nackt = zeile.split("#")[0]
            if muster.search(nackt) and re.search(r"canvas|width|height|_CANVAS|PAGE_", nackt, re.I):
                treffer.append(f"{f.relative_to(_ROOT)}:{nr}: {zeile.strip()[:80]}")
    assert len(treffer) <= _MAX_CANVAS_STELLEN, (
        f"{len(treffer)} Stellen mit eigener Leinwand-Meinung (erlaubt: "
        f"{_MAX_CANVAS_STELLEN}). Neue Stellen lesen bitte "
        "`layer_tools.layout_grid.load()`:\n  " + "\n  ".join(treffer)
    )


def test_grid_parameters_are_not_copied():
    """Spalten/Zeilen/Gutter/Rand stehen nicht ein zweites Mal im Code.

    `grid_calculator.py` fuehrte eine VOLLSTAENDIGE zweite Kopie des Rasters als
    Defaults. Zwei Kopien derselben Zahlen driften nicht vielleicht, sondern sicher —
    die Frage ist nur, wann es jemand merkt.
    """
    verdaechtig: list[str] = []
    for f in _relevante_dateien():
        text = f.read_text(encoding="utf-8", errors="replace")
        for nr, zeile in enumerate(text.splitlines(), 1):
            nackt = zeile.split("#")[0]
            # Nur ZUWEISUNGEN mit Literal, keine Parameter-Uebergaben aus Variablen.
            if re.search(r"\b(outer_margin|gutter)\s*=\s*\d", nackt):
                verdaechtig.append(f"{f.relative_to(_ROOT)}:{nr}: {nackt.strip()[:60]}")
    assert not verdaechtig, (
        "Rasterwerte als Literale gefunden — sie gehoeren in layout_grid.yaml:\n  "
        + "\n  ".join(verdaechtig))


def test_one_resolver_for_lu_to_pixels():
    """Es gibt genau EINE Stelle, die Logical Units in Pixel umrechnet.

    Zwei Implementierungen derselben Formel sind die klassische Drift-Quelle. Der
    Compiler rechnete frueher selbst; heute leitet er auf den Layer-Tool-Resolver
    weiter. Die TS-Seite (`slot-pos.ts`) ist bewusst eine zweite Implementierung —
    sie laeuft im Browser und wird durch `test_formula_mirrors_slot_pos_ts`
    zusammengehalten, nicht durch Hoffnung.
    """
    formel = re.compile(r"outer.*\+.*col.*\*.*\(.*lu_w.*\+.*gutter", re.I)
    stellen = [
        str(f.relative_to(_ROOT))
        for f in _relevante_dateien()
        if formel.search(f.read_text(encoding="utf-8", errors="replace"))
    ]
    assert len(stellen) <= 1, f"mehr als ein LU→px-Resolver: {stellen}"


def test_every_exemption_states_a_reason():
    """Eine Ausnahmeliste ohne Begruendungen wird zur Muellhalde."""
    ohne = [k for k, v in _AUSGENOMMEN.items() if not v and k != ".git"]
    assert not ohne, f"Ausnahmen ohne Grund: {ohne}"
