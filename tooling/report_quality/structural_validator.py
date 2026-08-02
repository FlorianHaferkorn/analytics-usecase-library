"""Structural PBIR invariants and deterministic fixes."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from .models import Severity, Violation
from .pbir import ParsedPage, ParsedReport, page_pointer, parse_report, visual_pointer, write_json

# Leinwand aus dem EINEN governten Raster (Konsolidierung 02.08.2026). Vorher standen
# hier eigene Literale — eine von 38 Stellen im Repo mit eigener Meinung, und zwei davon
# widersprachen sich (1280 vs 1920). Genau daraus kamen die Fehler in L13 und L8.
#
# Gelesen wird die YAML DIREKT, nicht ueber `tooling.superversion.layer_tools`. Der erste
# Versuch tat genau das — und brach `report_quality` fuer jeden Aufrufer, der mit
# `tooling/` im Pfad importiert (die CLI, und damit die Health-Scorecard). H7 fiel auf
# 0.0 %, weil ihr Import-Guard „validator unavailable" meldet statt zu crashen. Der Guard
# hat sauber funktioniert; mein Import war der Fehler.
#
# Das ist KEINE zweite Meinung: der Pfad zeigt auf dieselbe Datei, und
# `test_konsolidierung.py` haelt fest, dass es hier keine Zahlen-Literale gibt. Ein
# Paket, das standalone importierbar sein muss, darf nicht ueber Paketgrenzen greifen —
# diese Eigenschaft war vorher da und wird nicht fuer Eleganz aufgegeben.
def _canvas() -> tuple[int, int]:
    import yaml

    yml = (Path(__file__).resolve().parents[2]
           / "core/templates/page_templates/tokens/layout_grid.yaml")
    prod = ((yaml.safe_load(yml.read_text(encoding="utf-8")) or {})
            .get("canvas", {}).get("production", {}))
    if not prod.get("width") or not prod.get("height"):
        raise ValueError(
            f"{yml} fuehrt kein vollstaendiges Canvas-Profil 'production'. "
            "Eine geratene Leinwand erzeugt Positionen, die plausibel aussehen "
            "und falsch sind."
        )
    return int(prod["width"]), int(prod["height"])


DEFAULT_PAGE_WIDTH, DEFAULT_PAGE_HEIGHT = _canvas()


@runtime_checkable
class Invariant(Protocol):
    name: str
    severity: Severity

    def check(self, report: ParsedReport, page: ParsedPage) -> list[Violation]: ...


@dataclass
class ReportSpec:
    """A collection of structural invariants for one or more report pages."""

    invariants: list[Invariant] = field(default_factory=list)

    def check(self, report: ParsedReport) -> list[Violation]:
        violations: list[Violation] = []
        for page in report.pages.values():
            for invariant in self.invariants:
                violations.extend(invariant.check(report, page))
        return violations


@dataclass
class PageSize:
    width: int = DEFAULT_PAGE_WIDTH
    height: int = DEFAULT_PAGE_HEIGHT
    severity: Severity = "critical"
    name: str = "page:size"

    def check(self, report: ParsedReport, page: ParsedPage) -> list[Violation]:
        violations: list[Violation] = []
        if page.page_json.get("width") != self.width:
            violations.append(
                Violation(
                    self.name,
                    self.severity,
                    page_pointer(report.report_dir, page, "width"),
                    "Unexpected page width",
                    expected=self.width,
                    actual=page.page_json.get("width"),
                )
            )
        if page.page_json.get("height") != self.height:
            violations.append(
                Violation(
                    self.name,
                    self.severity,
                    page_pointer(report.report_dir, page, "height"),
                    "Unexpected page height",
                    expected=self.height,
                    actual=page.page_json.get("height"),
                )
            )
        return violations

    def fix(self, _report: ParsedReport, page: ParsedPage, _violation: Violation) -> bool:
        changed = False
        if page.page_json.get("width") != self.width:
            page.page_json["width"] = self.width
            changed = True
        if page.page_json.get("height") != self.height:
            page.page_json["height"] = self.height
            changed = True
        if changed:
            write_json(page.page_dir / "page.json", page.page_json)
        return changed


@dataclass
class RequiredSlots:
    """Pflicht-Slots einer Seite — aus `template_manifest.yaml`, nicht von hier.

    Zwei Aenderungen am 02.08.2026, beide gegen eine gemessene Blindheit:

    1. **Keine eigenen Mengen mehr.** Vorher standen hier zwei hartkodierte Listen,
       und sie widersprachen der Autoritaet: das Manifest fuehrt `KPI_Cards` fuer T3
       und T4 auf `mandatory: false`, dieser Wachhund verlangte es unbedingt. Das war
       die fuenfte Stelle mit einer eigenen Meinung ueber governtes Wissen.
    2. **Kein Namens-Schnueffeln mehr.** Vorher entschied `"overview" in label`,
       welche Menge gilt. Die Seiten der kanonischen Kette heissen `page_1_summary`
       und `page_2_execution` — keins von beiden matchte, der Wachhund gab still `[]`
       zurueck. Variante und Ebene werden jetzt **uebergeben**; wer sie nicht kennt,
       bekommt einen Fehler statt eines stillen Bestehens.

    Fuer die kanonische Kette prueft `from_aluca.slot_luecken()` dasselbe eine Schicht
    frueher, wo Variante und Modell ohnehin vorliegen — und deckt damit jeden Emitter
    ab, nicht nur PBIR.
    """

    variant: str = ""
    ebene: str = "overview_slots"
    severity: Severity = "critical"
    name: str = "page:required-slots"

    def check(self, report: ParsedReport, page: ParsedPage) -> list[Violation]:
        from tooling.superversion.layer_tools.page_templates import fehlende_pflichtslots

        if not self.variant:
            raise ValueError(
                "RequiredSlots braucht eine `variant` aus template_manifest.yaml. "
                "Ohne sie gibt es keine Pflichtliste — und eine leere Pflichtliste "
                "sieht aus wie 'alles erfuellt'."
            )
        missing = fehlende_pflichtslots(self.variant, set(page.visuals), ebene=self.ebene)
        if not missing:
            return []
        expected = sorted(set(page.visuals) | set(missing))
        return [
            Violation(
                self.name,
                self.severity,
                page_pointer(report.report_dir, page),
                f"Missing required visual slots: {missing}",
                expected=sorted(expected),
                actual=sorted(page.visuals),
            )
        ]


@dataclass
class ForbiddenVisualTypes:
    forbidden: set[str] = field(default_factory=lambda: {"pieChart", "donutChart", "gauge", "treemap"})
    severity: Severity = "critical"
    name: str = "visual:forbidden-type"

    def check(self, report: ParsedReport, page: ParsedPage) -> list[Violation]:
        violations: list[Violation] = []
        for visual_name, visual in page.visuals.items():
            visual_type = visual.get("visual", {}).get("visualType")
            if visual_type in self.forbidden:
                violations.append(
                    Violation(
                        self.name,
                        self.severity,
                        visual_pointer(report.report_dir, page, visual_name, "visual/visualType"),
                        "Forbidden visual type",
                        expected=f"not in {sorted(self.forbidden)}",
                        actual=visual_type,
                    )
                )
        return violations


@dataclass
class VisualWithinPage:
    severity: Severity = "critical"
    name: str = "visual:bounds"

    def check(self, report: ParsedReport, page: ParsedPage) -> list[Violation]:
        width = page.page_json.get("width", DEFAULT_PAGE_WIDTH)
        height = page.page_json.get("height", DEFAULT_PAGE_HEIGHT)
        violations: list[Violation] = []
        for visual_name, visual in page.visuals.items():
            pos = visual.get("position") or {}
            x = pos.get("x")
            y = pos.get("y")
            w = pos.get("width")
            h = pos.get("height")
            if not all(isinstance(v, (int, float)) for v in (x, y, w, h)):
                violations.append(
                    Violation(
                        self.name,
                        self.severity,
                        visual_pointer(report.report_dir, page, visual_name, "position"),
                        "Visual position must include numeric x, y, width, height",
                        actual=pos,
                    )
                )
                continue
            if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > width or y + h > height:
                violations.append(
                    Violation(
                        self.name,
                        self.severity,
                        visual_pointer(report.report_dir, page, visual_name, "position"),
                        "Visual is outside page bounds",
                        expected={"page_width": width, "page_height": height},
                        actual=pos,
                    )
                )
        return violations


def default_spec() -> ReportSpec:
    """Die Invarianten, die **ohne Zusatzwissen** entscheidbar sind.

    `RequiredSlots` steht bewusst NICHT hier: es braucht die Seitenvariante, und die
    kennt eine Default-Spec nicht. Frueher stand es drin — mit zwei geratenen Mengen,
    die dem Manifest widersprachen. Ein Wachhund, den man ohne sein Wissen bauen kann,
    prueft nicht die Sache, sondern die Vermutung.
    """
    return ReportSpec(invariants=[PageSize(), ForbiddenVisualTypes(), VisualWithinPage()])


def check_report(report_dir: Path, spec: ReportSpec | None = None) -> list[Violation]:
    return (spec or default_spec()).check(parse_report(report_dir))
