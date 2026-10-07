"""dist/ und Themes gegen den vendorten Formatierungskatalog des offiziellen Validators.

Anlass (07.10.2026): `powerbi-report-author validate` (Pin 0.4.0) meldete in jedem der 17
dist-Reports 23 Theme-Befunde (`PBIR_THEME_VISUAL_PROP_UNKNOWN` 18, `PBIR_FORMATTING_OBJECT_UNKNOWN`
5). Ursache: dist traegt ein veraltetes Aurora-Theme (Stand #421), nicht die vendorte Ausgabe der
Theme-Engine (`products/fabric/powerbi/themes/`, PIN.json), die keinen dieser Befunde hat.

Das Engine-Theme wird bewusst NICHT uebernommen (Stand 07.10.2026): es nimmt die globale
Nullbasis `valueAxis.start = 0` weg (BC-CHART-09, `test_theme_consistency.py`) und setzt
`fontFace` Inter statt der Brand-Schrift Segoe UI (`showcases/aurora_group/brand/brand_spec.yaml`).
Beides gehoert in die Engine (Freelancing `products/pbi_theme`), danach `--write-themes` und
`apply_report_theme`. Bis dahin halten die Tests den dist-Bestand als Ratsche fest.

Die Pruefung laeuft offline ueber `tooling/report_quality/formatting_metadata.py` und den Snapshot
`tooling/schemas/pbir/formatting_metadata_snapshot.json`. Der erste Test ist die Gegenprobe: am
bis 07.10.2026 ausgelieferten Theme muss der Checker genau die 23 Befunde der CLI finden —
sonst prueft er nichts.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tooling.report_quality import formatting_metadata as fm

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / "products/fabric/powerbi/dist"
VENDORED = REPO / "products/fabric/powerbi/themes"
FIXTURE = Path(__file__).parent / "fixtures/pbir/aurora_theme_dist_bis_2026-10-07.json"
THEME_FILE = "Aurora_Group__Monochromatic__Light___2ECDE7.json"

#: Was die CLI 0.4.0 am 07.10.2026 je Report fuer das alte Theme meldete (validate --format json).
CLI_BEFUNDE_ALTES_THEME = {
    "*:columnHeaders.backColorPrimary", "*:columnHeaders.backColorSecondary", "*:legend.alignment",
    "*:lineStyles.areaTransparency", "*:lineStyles.strokeLineCap", "*:outspace", "*:padding.show",
    "*:rowHeaders.backColorPrimary", "*:rowHeaders.backColorSecondary",
    "*:smallMultiplesLayout.padding", "*:smallMultiplesLayout.spacing",
    "*:smallMultiplesLayout.titleShow", "actionButton:header", "advancedSlicerVisual:padding.bottom",
    "advancedSlicerVisual:padding.left", "advancedSlicerVisual:padding.right",
    "advancedSlicerVisual:padding.top", "bookmarkNavigator:header", "pageNavigator:header",
    "pageNavigator:padding.show", "scatterChart:markers.markerShape", "scatterChart:markers.markerSize",
    "shape:header",
}

#: Offene Befunde, die keine Generator-Eingabe haben (Stand 07.10.2026). Die Variante
#: COM-001_Sales_Performance_vs_Plan_LY hat keinen eigenen Bracket (KNOWN_ERRORS: "Benannte
#: Variante ohne eigenen Bracket"); ihre Visuals werden nicht erzeugt und nicht von Hand
#: gepatcht. Faellt ein Eintrag weg, gehoert er hier gestrichen (test_open_findings_not_stale).
OFFEN_OHNE_GENERATOR = {
    "COM-001_Sales_Performance_vs_Plan_LY.Report/Page_COM001LY_Overview/KPI_Cards: calloutValue",
    "COM-001_Sales_Performance_vs_Plan_LY.Report/Page_COM001LY_Overview/Main_3: dataLabels",
}


def _reports() -> list[Path]:
    reports = sorted(DIST.glob("*.Report"))
    assert reports, "keine dist-Reports — Test hat seinen Gegenstand verloren"
    return reports


def _visual_findings() -> set[str]:
    found: set[str] = set()
    for report in _reports():
        for vj in sorted(report.glob("definition/pages/*/visuals/*/visual.json")):
            page, name = vj.parent.parent.parent.name, vj.parent.name
            for f in fm.unknown_visual_objects(json.loads(vj.read_text(encoding="utf-8"))):
                found.add(f"{report.name}/{page}/{name}: {f}")
    return found


def test_checker_reproduces_cli_findings_on_old_theme():
    old = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert set(fm.unknown_theme_entries(old)) == CLI_BEFUNDE_ALTES_THEME


@pytest.mark.parametrize("theme", sorted(p for p in VENDORED.rglob("*.json") if p.name != "PIN.json"),
                         ids=lambda p: p.stem)
def test_vendored_engine_themes_have_no_unknown_entries(theme: Path):
    assert fm.unknown_theme_entries(json.loads(theme.read_text(encoding="utf-8"))) == []


@pytest.mark.parametrize("report", sorted(DIST.glob("*.Report")), ids=lambda p: p.name)
def test_dist_custom_theme_findings_do_not_grow(report: Path):
    """dist-Theme: hoechstens die 23 bekannten Befunde (Ratsche bis zur Engine-Korrektur).

    Wird das Engine-Theme uebernommen, faellt die Menge auf 0 — dann gehoert dieser Test auf
    `== []` umgestellt (test_dist_theme_findings_not_stale meldet das).
    """
    shipped = json.loads((report / "StaticResources/RegisteredResources" / THEME_FILE).read_text(encoding="utf-8"))
    neu = set(fm.unknown_theme_entries(shipped)) - CLI_BEFUNDE_ALTES_THEME
    assert not neu, f"{report.name}: neue unbekannte Theme-Eintraege: {sorted(neu)}"


def test_dist_theme_findings_not_stale():
    befunde: set[str] = set()
    for report in _reports():
        shipped = json.loads((report / "StaticResources/RegisteredResources" / THEME_FILE).read_text(encoding="utf-8"))
        befunde.update(fm.unknown_theme_entries(shipped))
    assert befunde == CLI_BEFUNDE_ALTES_THEME, (
        "Theme-Befunde in dist haben sich veraendert (Engine-Theme uebernommen?) — Ratsche "
        f"nachziehen. Jetzt: {sorted(befunde)}")


def test_dist_visual_objects_known_except_documented_open():
    neu = _visual_findings() - OFFEN_OHNE_GENERATOR
    assert not neu, "Unbekannte Formatierungsobjekte in dist/: " + "; ".join(sorted(neu))


def test_open_findings_not_stale():
    erledigt = OFFEN_OHNE_GENERATOR - _visual_findings()
    assert not erledigt, "Erledigt, bitte aus OFFEN_OHNE_GENERATOR streichen: " + "; ".join(sorted(erledigt))
