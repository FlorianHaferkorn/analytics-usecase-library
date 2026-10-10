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
stammten aus dem veralteten dist-Theme; seit 08.10.2026 traegt dist das Engine-Theme
(D-685/D-710), dort 0 Befunde.

Nachgemessen am 09.10.2026 (CLI 0.5.0, `validate --format json`, alle 17 dist-Reports, Stand
nach Zusammenfuehrung der Emitter-Korrektur mit dem Engine-Theme): 16 × 0, COM-001LY 2
(`calloutValue` an cardVisual, `dataLabels` an clusteredBarChart; Variante ohne Bracket, keine
Generator-Eingabe), Summe 2. Offline gefuehrt in `test_dist_formatting_catalogue.py`.
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
#: 25 -> 2 am 08.10.2026: dist traegt das Engine-Theme (Freelancing products/pbi_theme 0.6.0,
#: Meridian D-685/D-710, Spiegel c9efa687). CLI 0.5.0 `validate --format json` ueber 17 Reports:
#: 423 -> 32 Errors, 0 im Theme; je Report hoechstens 2 (15 Generator-Reports: `calloutValue`
#: an cardVisual und `text.text` an der Header-Textbox; COM-001LY: `calloutValue` und
#: `dataLabels`; FIN-001: 0). Gemessen ohne Zugang zu
#: developer.microsoft.com (7 x PBIR_SCHEMA_UNREACHABLE je Report), wie die Messungen davor.
#:
#: 09.10.2026, Emitter-Korrektur (cardVisual `value`, Textbox `general.paragraphs`) auf dem
#: Engine-Theme: 15 Generator-Reports 2 -> 0, FIN-001 0, COM-001LY 2 (Summe 32 -> 2). Der
#: schlechteste bleibt COM-001LY, daher Baseline weiter 2; faellt er, gehoert die Zahl auf 0.
BASELINE_ERRORS = 2


#: Code, mit dem die CLI ein nicht ladbares ``$schema`` meldet -- als *Warning*. Dann lief
#: die Schemapruefung fuer diese Datei nicht, ``errorCount`` zaehlt nur den Rest. Gemessen am
#: 02.10.2026 (CLI 0.4.0, Sandbox ohne Zugang zu developer.microsoft.com): COM-001 meldet
#: 25 Errors = Baseline und 7 dieser Warnings -- die Ratsche waere ohne Schemapruefung gruen.
#: Gleiche Regel wie Freelancing ``scripts/check_pbir.py`` (D-613): nicht gelaufen ist kein Gruen.
NICHT_GEPRUEFT = "PBIR_SCHEMA_UNREACHABLE"


def nicht_geprueft(daten: dict) -> list[str]:
    """Die ``$schema``-URLs, deren Pruefung der Validator ausgelassen hat (leer = alles geprueft)."""
    eintrag = (daten.get("diagnostics") or {}).get(NICHT_GEPRUEFT) or {}
    return [str(i.get("message", ""))[:160] for i in (eintrag.get("items") or [])]


def _validate(report: Path) -> dict:
    proc = subprocess.run(_cli_args(report),
                          capture_output=True, text=True, cwd=str(REPO), encoding="utf-8", errors="replace")
    daten = (json.loads(proc.stdout) or {}).get("data", {})
    offen = nicht_geprueft(daten)
    if offen:
        grund = (f"{report.name}: Schemapruefung nicht gelaufen, {len(offen)} $schema nicht "
                 f"ladbar ({NICHT_GEPRUEFT}), z. B. {offen[0]}")
        if os.environ.get("ALUCA_PBIR_CLI_PFLICHT", "") == "1":
            pytest.fail(grund + " -- mit ALUCA_PBIR_CLI_PFLICHT=1 ist das rot, kein stilles Gruen.")
        pytest.skip(grund)
    return daten


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


def test_nicht_geprueft_erkennt_nicht_ladbare_schemas():
    """Ohne CLI pruefbar: die Erkennung selbst (Form wie CLI 0.4.0, gemessen 02.10.2026)."""
    daten = {"errorCount": 25, "diagnostics": {
        NICHT_GEPRUEFT: {"severity": "warning", "items": [
            {"message": 'JSON Schema "https://developer.microsoft.com/json-schemas/x" could not be fetched'}]},
        "PBIR_THEME_VISUAL_PROP_UNKNOWN": {"severity": "error", "items": [{}]}}}
    assert len(nicht_geprueft(daten)) == 1
    assert nicht_geprueft({"errorCount": 25, "diagnostics": {}}) == []
    assert nicht_geprueft({}) == []
