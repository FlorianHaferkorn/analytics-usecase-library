"""Die dist-Reports gegen den offiziellen Validator — als Ratsche, nicht als Gate.

Gemessen am 03.08.2026: jeder der 17 dist-Reports meldet **25 Errors** des offiziellen
`powerbi-report-author validate` (damals Repo-Pin 0.1.1; seit 29.09.2026 Pin 0.4.0 mit
derselben Befundmenge, `docs/architecture/pbir_cli_040_triage.md`), repo-weit identisch und ausnahmslos
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
da ist, ist kein Befund) und in diesem Repo etabliert. Mit `ALUCA_PBIR_CLI_PFLICHT=1`
(gesetzt in `.github/workflows/superversion.yml`) ist die fehlende CLI dagegen rot; die
Regel steht im Marker `braucht_pbir_cli` in der Wurzel-`conftest.py`.

Nachgemessen am 29.09.2026 (CLI 0.1.1, `validate --format json`, alle 17 dist-Reports):
16 Reports mit 25 Errors, 1 Report mit 23 — der schlechteste Wert steht weiter auf 25.

Nachgemessen am 30.09.2026 (CLI 0.4.0): unverändert 16 × 25 und 1 × 23. Der offizielle Emit
käme auf 0, trägt aber nur 105 statt 211 Visuals und 39 von 133 im dist-Modell auflösbare
Bindungen; `dist/` bleibt deshalb auf dem Prototyp und die Ratsche auf 25
(`docs/architecture/research/2026-09-30_a18-dist-emit-messung.md`, A-18).

Nachgemessen am 07.10.2026 (CLI 0.4.0, `validate --format json`, alle 17 dist-Reports): vorher
16 × 25 und 1 × 23 (423 Errors), nachher 15 × 23, FIN-001 23, COM-001LY 25 (393). Die 25 waren
keine Katalogluecke, sondern Quellfehler: der Generator schrieb `calloutValue` an `cardVisual`
und `text.text` an die Header-Textbox (beide behoben, 15 Reports neu erzeugt). Die 23 im Theme
stammen aus einem veralteten dist-Theme; das vendorte Engine-Theme haette 0, nimmt aber die
globale Nullbasis (BC-CHART-09) weg und wechselt die Schrift — Engine-Korrektur offen.
COM-001_Sales_Performance_vs_Plan_LY bleibt bei 25 (keine Generator-Eingabe). Offline
gefuehrt in `test_dist_formatting_catalogue.py`.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
_DIST = REPO / "products/fabric/powerbi/dist"
_CLI_NAME = "powerbi-report-author"
_CLI = shutil.which(_CLI_NAME)


def _cli_args(report: Path) -> list[str]:
    args = ["validate", str(report), "--format", "json"]
    if _CLI and Path(_CLI).suffix.lower() in {".cmd", ".bat"}:
        # CreateProcess cannot execute cmd/bat shims directly. Keep shell=False
        # and invoke the Windows command processor explicitly with fixed args.
        return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", _CLI, *args]
    return [_CLI or _CLI_NAME, *args]

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
#:
#: 07.10.2026: cardVisual `value` statt `calloutValue`, Textbox `general.paragraphs` statt
#: `text.text` — 15 Reports 25 -> 23. Der schlechteste bleibt COM-001LY mit 25 (Theme 23 +
#: `calloutValue` + `dataLabels`, handgepflegte Variante ohne Bracket), daher Baseline 25.
#: Faellt COM-001LY oder das Theme, gehoert die Zahl gesenkt (test_baseline_is_not_stale).
BASELINE_ERRORS = 25


def _validate(report: Path) -> dict:
    proc = subprocess.run(_cli_args(report),
                          capture_output=True, text=True, cwd=str(REPO), encoding="utf-8", errors="replace")
    return (json.loads(proc.stdout) or {}).get("data", {})


@pytest.mark.braucht_pbir_cli
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


@pytest.mark.braucht_pbir_cli
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
