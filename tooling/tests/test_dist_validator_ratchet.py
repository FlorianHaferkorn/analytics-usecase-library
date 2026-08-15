"""Die dist-Reports gegen den offiziellen Validator — als Ratsche, nicht als Gate.

Gemessen am 03.08.2026: jeder der 17 dist-Reports meldet **25 Errors** des offiziellen
`powerbi-report-author validate` (Repo-Pin 0.1.1), repo-weit identisch und ausnahmslos
im mitgelieferten Theme. Frisch emittierte Reports sind sauber — der Unterschied ist
das Theme, nicht der Emitter.

Warum Ratsche und nicht Gate
-----------------------------
Die 25 sind **zwei Klassen**, und sie lassen sich offline nicht sauber trennen: die CLI
ist Public Preview und ihr Katalog hat Luecken (`padding.left` gilt fuer
`advancedSlicerVisual` als unbekannt, obwohl derselbe Katalog `padding` mit genau diesen
vier Eigenschaften fuehrt). Ein hartes Gate haette entweder auf einer Zahl bestanden,
die zum Teil ein Werkzeugfehler ist, oder zum pauschalen Loeschen gueltiger Formatierung
verleitet. Die Trennung braucht Desktop (L10); bis dahin gilt: **es darf nur besser
werden.**

Der Test ueberspringt sich ohne CLI — das ist ehrlich (ein externes Werkzeug, das nicht
da ist, ist kein Befund) und in diesem Repo etabliert.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
_DIST = REPO / "products/fabric/powerbi/dist"
_CLI = "powerbi-report-author"

#: Gemessener Stand am 03.08.2026: 24–26 je Report (das Theme wird je nach
#: vorhandenen Visualtypen unterschiedlich weit geprueft), plus in 11 von 17 ein
#: `PBIR_ROLE_MAX_EXCEEDED` auf `waterfallChart`. Die Ratsche steht auf dem
#: SCHLECHTESTEN gemessenen Wert — sie soll Rueckschritt fangen, nicht den Bestand
#: verwalten. Sinkt der schlechteste, gehoert die Zahl gesenkt.
#:
#: 26 -> 25 am 05.08.2026: alle elf ROLE_MAX-Verstoesse sind weg. Acht Reports
#: trugen einen waterfallChart, obwohl ihr Bracket `horizontal_bar_chart` vorschreibt
#: (Drift, kein Entwurf); zwei weitere dasselbe mit `line_chart` bzw.
#: `horizontal_bar_chart`; der eine ECHTE Bruecke (COM-001LY) nutzt jetzt das
#: Muster, das COM-002 seit jeher vormacht — dim_pvm_driver als Kategorie, eine
#: Measure auf Y. Was bleibt, sind die Theme-Eigenschaften (Uebergabepunkt A).
BASELINE_ERRORS = 25


def _validate(report: Path) -> dict:
    proc = subprocess.run([_CLI, "validate", str(report), "--format", "json"],
                          capture_output=True, text=True, cwd=str(REPO))
    return (json.loads(proc.stdout) or {}).get("data", {})


@pytest.mark.skipif(shutil.which(_CLI) is None,
                    reason=f"{_CLI} nicht installiert — externes Werkzeug, kein Befund")
def test_no_report_gets_worse_than_the_measured_baseline():
    reports = sorted(_DIST.glob("*.Report"))
    assert reports, "keine dist-Reports — Test hat seinen Gegenstand verloren"
    schlechter = []
    for report in reports:
        daten = _validate(report)
        fehler = daten.get("errorCount")
        assert fehler is not None, f"{report.name}: Validator lieferte keinen errorCount"
        if fehler > BASELINE_ERRORS:
            schlechter.append(f"{report.name}: {fehler} > {BASELINE_ERRORS}")
    assert not schlechter, (
        "Neue Validator-Fehler gegenueber dem gemessenen Stand: " + "; ".join(schlechter)
        + ". Die Ratsche laesst nur Verbesserung zu.")


@pytest.mark.skipif(shutil.which(_CLI) is None, reason=f"{_CLI} nicht installiert")
def test_baseline_is_not_stale():
    """Faellt der Stand unter die Baseline, gehoert die Zahl gesenkt.

    Ohne diesen Test bliebe eine ueberholte Baseline stehen und wuerde kuenftige
    Rueckschritte durchlassen — eine Ratsche, die nicht nachzieht, ist eine Bremse,
    die man vergessen hat.
    """
    schlechteste = max(_validate(r).get("errorCount", 0) for r in sorted(_DIST.glob("*.Report")))
    assert schlechteste >= BASELINE_ERRORS, (
        f"schlechtester Report hat {schlechteste} Fehler, Baseline steht auf "
        f"{BASELINE_ERRORS} — Fortschritt eintragen, sonst schuetzt die Ratsche zu wenig.")
