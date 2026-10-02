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
        # Die Haerte steht im Manifest, nicht hier: `severity: warning` auf einem Slot
        # senkt den Befund auf `warning`, statt ihn wegzulassen. Ein Slot, den niemand
        # meldet, ist die stille Variante — genau der Fehler, gegen den dieser Wachhund
        # am 02.08. umgebaut wurde.
        missing = fehlende_pflichtslots(self.variant, set(page.visuals), ebene=self.ebene,
                                        severity="error")
        weich = fehlende_pflichtslots(self.variant, set(page.visuals), ebene=self.ebene,
                                      severity="warning")
        if not missing and not weich:
            return []
        expected = sorted(set(page.visuals) | set(missing) | set(weich))
        out = [
            Violation(
                self.name,
                "warning",
                page_pointer(report.report_dir, page),
                f"Missing required visual slots (severity: warning): {weich}",
                expected=sorted(expected),
                actual=sorted(page.visuals),
            )
        ] if weich else []
        if not missing:
            return out
        return out + [
            Violation(
                self.name,
                self.severity,
                page_pointer(report.report_dir, page),
                f"Missing required visual slots: {missing}",
                expected=sorted(expected),
                actual=sorted(page.visuals),
            )
        ]


# ── Verbotsliste: IBCS 2.0 EX 2.1 bis EX 2.5 plus Hausregel BC-CHART-08 ──────────────────
#
# Quelle der IBCS-Regeln: IBCS Standards Version 2.0 (IBCS Association 2026, CC BY-SA 4.0),
# Abschnitt EXPRESS, Gruppe EX 2 „Replace inappropriate chart types", wie katalogisiert in
# `docs/architecture/research/2026-09-30_visual-stack-r1/ibcs_v2.yaml` (Feld `seite`).
# IBCS sagt „replace" mit Ausnahmen, nicht „never" -- daher Schwere `warning`. Die Seitenzahlen
# hier sind Konstanten mit Nachbar: `test_ibcs_ex2_verbotsliste.py` liest sie gegen den Katalog.
#
# Ausnahmen sind Daten, keine Prosa: ein Visual erklaert sie ueber die PBIR-Annotation
# `{"name": "ibcs.ausnahme", "value": "EX 2.2: <Begruendung>"}` (visualContainer-Schema, Feld
# `annotations`). Eine anerkannte Ausnahme erzeugt einen `info`-Befund statt keines -- ein
# Wachhund, der still wird, sieht aus wie einer, der nichts gefunden hat.

AUSNAHME_ANNOTATION = "ibcs.ausnahme"


@dataclass(frozen=True)
class Diagrammregel:
    """Eine Zeile der Verbotsliste."""

    regel_id: str              # "EX 2.1" (IBCS 2.0) oder "BC-CHART-08" (Hausregel)
    seite: int | None          # Seite im IBCS-2.0-Original laut Katalog; None = keine IBCS-Regel
    severity: Severity
    ersatz: str
    ausnahme: str | None       # Katalog-Ausnahme, die per Annotation erklaert werden darf; None = keine

    @property
    def quelle(self) -> str:
        if self.seite is None:
            return f"{self.regel_id} (Hausregel, Boutique-Craft-Rubric)"
        return f"IBCS 2.0 {self.regel_id}, S. {self.seite}"


EX_2_1 = Diagrammregel(
    "EX 2.1", 136, "warning", "Balken oder gestapelte Saeulen",
    # Die Katalog-Ausnahme (Torte auf einem Kartenpunkt, hoechstens 3 Werte) ist in PBIR ein
    # Karten-Visual mit Legende, nie ein pieChart/donutChart -- daher hier nicht erklaerbar.
    None,
)
EX_2_2 = Diagrammregel(
    "EX 2.2", 136, "warning", "Balken/Saeulen oder Bullet (kpi_card_bullet)",
    "Echtzeit-Monitoring UND semantische Faerbung der aktuellen Abweichung (keine Wertbaender) "
    "UND Ziel und Deutung sofort klar -- alle drei Kriterien",
)
EX_2_3_RADAR = Diagrammregel(
    "EX 2.3", 137, "warning", "Balken",
    "Kreisanordnung traegt Bedeutung (z. B. Himmelsrichtung)",
)
EX_2_3_TRICHTER = Diagrammregel("EX 2.3", 137, "warning", "Balken (bar_ranking) oder Sankey", None)
EX_2_4 = Diagrammregel(
    "EX 2.4", 138, "warning", "Small Multiples (eine Linie je Chart)",
    "exakter Hoehenvergleich der Linien noetig",
)
EX_2_5 = Diagrammregel(
    "EX 2.5", 138, "warning", "Balken oder Tabellenbalken",
    "binaere Aussage oder Ziel-/Schwellen-Compliance, Hoehe der Abweichung irrelevant",
)
HAUS_TREEMAP = Diagrammregel("BC-CHART-08", None, "critical", "Balken (bar_ranking)", None)

# Exakte PBIR-visualTypes. Radar/Spinnennetz gibt es nur als Custom Visual mit
# wechselnder Kennung, Tacho auch als Custom Visual -- beides per Teilwort (siehe unten).
VERBOTSLISTE: dict[str, Diagrammregel] = {
    "pieChart": EX_2_1,
    "donutChart": EX_2_1,
    "gauge": EX_2_2,
    "funnel": EX_2_3_TRICHTER,
    "treemap": HAUS_TREEMAP,
}
TEILWORT_REGELN: tuple[tuple[str, Diagrammregel], ...] = (
    ("radar", EX_2_3_RADAR),
    ("spider", EX_2_3_RADAR),
    ("gauge", EX_2_2),
)
# EX 2.4: mehr als 3-4 sich kreuzende Linien. Der Katalog-Test setzt die Grenze bei <= 4.
SPAGHETTI_TYPEN = frozenset({"lineChart", "areaChart"})
SPAGHETTI_MAX_LINIEN = 4
# EX 2.5: eine Ampel ist ein Symbol mit drei Stufen; zwei Stufen sind die binaere Ausnahme.
AMPEL_PROPERTIES = frozenset({"icon", "iconSet"})


def regel_fuer_typ(visual_type: str | None) -> Diagrammregel | None:
    """Die Verbotsregel eines visualType, oder None, wenn der Typ nicht auf der Liste steht."""
    if not visual_type:
        return None
    if visual_type in VERBOTSLISTE:
        return VERBOTSLISTE[visual_type]
    low = visual_type.lower()
    for wort, regel in TEILWORT_REGELN:
        if wort in low:
            return regel
    return None


def _erklaerte_ausnahme(visual: dict, regel: Diagrammregel) -> str | None:
    """Wert der Annotation `ibcs.ausnahme`, wenn sie diese Regel nennt und der Katalog eine
    Ausnahme kennt; sonst None."""
    if regel.ausnahme is None:
        return None
    for a in visual.get("annotations") or []:
        if not isinstance(a, dict) or a.get("name") != AUSNAHME_ANNOTATION:
            continue
        wert = str(a.get("value") or "").strip()
        if wert.startswith(regel.regel_id):
            return wert
    return None


def _linien(visual: dict) -> tuple[int, bool, bool]:
    """(Anzahl Measures auf Y/Y2, Series-Feld gebunden, Small Multiples gebunden)."""
    qs = ((visual.get("visual") or {}).get("query") or {}).get("queryState") or {}

    def n(rolle: str) -> int:
        return len((qs.get(rolle) or {}).get("projections") or [])

    return n("Y") + n("Y2"), n("Series") > 0, n("Rows") > 0


def _literale(knoten: object) -> set[str]:
    out: set[str] = set()
    if isinstance(knoten, dict):
        lit = knoten.get("Literal")
        if isinstance(lit, dict) and isinstance(lit.get("Value"), str):
            out.add(lit["Value"])
        for v in knoten.values():
            out |= _literale(v)
    elif isinstance(knoten, list):
        for v in knoten:
            out |= _literale(v)
    return out


def _ampel_stufen(visual: dict) -> int | None:
    """Stufen einer Symbol-Formatierung: 0 = keine Symbole, n = verschiedene Literale,
    None = Symbole vorhanden, aber Stufenzahl nicht statisch bestimmbar (Measure-gesteuert)."""
    objects = (visual.get("visual") or {}).get("objects") or {}
    gefunden = False
    stufen: set[str] = set()
    for eintraege in objects.values():
        for e in eintraege if isinstance(eintraege, list) else [eintraege]:
            props = (e.get("properties") or {}) if isinstance(e, dict) else {}
            for name, wert in props.items():
                if name in AMPEL_PROPERTIES:
                    gefunden = True
                    stufen |= _literale(wert)
    if not gefunden:
        return 0
    return len(stufen) or None


@dataclass
class ForbiddenVisualTypes:
    """Verbotsliste der Diagrammtypen: IBCS 2.0 EX 2.1 bis EX 2.5 (Warnung, mit Ausnahmen)
    plus Hausregel BC-CHART-08 fuer Treemap (kritisch, keine IBCS-Quelle)."""

    regeln: dict[str, Diagrammregel] = field(default_factory=lambda: dict(VERBOTSLISTE))
    name: str = "visual:forbidden-type"

    @property
    def forbidden(self) -> set[str]:
        """Die exakt gelisteten visualTypes (Teilwort-Regeln fuer Custom Visuals kommen dazu)."""
        return set(self.regeln)

    def _regel(self, visual_type: str | None) -> Diagrammregel | None:
        if not visual_type:
            return None
        if visual_type in self.regeln:
            return self.regeln[visual_type]
        if visual_type in VERBOTSLISTE:
            return None  # bewusst aus `regeln` genommen
        return regel_fuer_typ(visual_type)

    def _befund(self, report: ParsedReport, page: ParsedPage, visual_name: str, visual: dict,
                regel: Diagrammregel, was: str, actual: object, severity: Severity | None = None,
                ) -> Violation:
        pointer = visual_pointer(report.report_dir, page, visual_name, "visual/visualType")
        ausnahme = _erklaerte_ausnahme(visual, regel)
        if ausnahme is not None:
            return Violation(self.name, "info", pointer,
                             f"Forbidden visual type {was}: Ausnahme erklaert ({regel.quelle})",
                             expected=f"Ausnahme laut Katalog: {regel.ausnahme}", actual=ausnahme)
        hinweis = (f"; Ausnahme per Annotation '{AUSNAHME_ANNOTATION}': {regel.ausnahme}"
                   if regel.ausnahme else "")
        return Violation(self.name, severity or regel.severity, pointer,
                         f"Forbidden visual type {was} ({regel.quelle}){hinweis}",
                         expected=f"ersetzen durch: {regel.ersatz}", actual=actual)

    def check(self, report: ParsedReport, page: ParsedPage) -> list[Violation]:
        violations: list[Violation] = []
        for visual_name, visual in page.visuals.items():
            visual_type = (visual.get("visual") or {}).get("visualType")
            regel = self._regel(visual_type)
            if regel is not None:
                violations.append(self._befund(report, page, visual_name, visual, regel,
                                               f"'{visual_type}'", visual_type))
                continue
            if visual_type in SPAGHETTI_TYPEN:
                anzahl, series, multiples = _linien(visual)
                # Small Multiples sind der Ersatz, den EX 2.4 verlangt.
                if not multiples and anzahl > SPAGHETTI_MAX_LINIEN:
                    violations.append(self._befund(
                        report, page, visual_name, visual, EX_2_4,
                        f"'{visual_type}' als Spaghetti ({anzahl} Linien > {SPAGHETTI_MAX_LINIEN})",
                        visual_type))
                elif not multiples and series:
                    # Linienzahl haengt an den Daten des Series-Felds: statisch nicht entscheidbar.
                    violations.append(self._befund(
                        report, page, visual_name, visual, EX_2_4,
                        f"'{visual_type}' mit Series-Feld (Linienzahl datenabhaengig, "
                        "nicht statisch geprueft)", visual_type, severity="info"))
            stufen = _ampel_stufen(visual)
            if stufen == 2:
                continue  # binaere Aussage: Ausnahme laut EX 2.5
            if stufen is None or stufen >= 3:
                was = (f"'{visual_type}' mit Ampelsymbolen ({stufen} Stufen)" if stufen
                       else f"'{visual_type}' mit Ampelsymbolen (Stufenzahl Measure-gesteuert)")
                violations.append(self._befund(report, page, visual_name, visual, EX_2_5, was,
                                               visual_type))
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


@dataclass
class VisualsDoNotOverlap:
    """Zwei inhaltstragende Visuals teilen sich keine Flaeche.

    Gemessen 23.09.2026: der Big-Idea-Header lag in COM-002 seit R1.1 (03.07.2026) auf den
    oberen 56 px des KPI-Bandes, beide auf z 10000, und beim Ausrollen des Generators waere
    dasselbe in 16 Reports entstanden. `visual:bounds` prueft nur den Seitenrand, eine
    Flaeche, die zwei Visuals beanspruchen, sah keine Regel. Die visuelle Abnahme, die es
    gezeigt haette (R1.6), fand nie statt -- eine Regel, die man sich merken muss, ist keine.

    Ausgenommen sind dekorative Typen (Form, Bild, Button): sie liegen legitim unter
    oder ueber Inhalt, etwa als Hintergrundflaeche.
    """

    severity: Severity = "critical"
    name: str = "visual:overlap"
    decorative: frozenset = frozenset({"shape", "basicShape", "image", "actionButton"})

    def check(self, report: ParsedReport, page: ParsedPage) -> list[Violation]:
        boxes = []
        for visual_name, visual in page.visuals.items():
            vt = (visual.get("visual") or {}).get("visualType")
            pos = visual.get("position") or {}
            if vt in self.decorative or not all(
                    isinstance(pos.get(k), (int, float)) for k in ("x", "y", "width", "height")):
                continue
            boxes.append((visual_name, pos))
        violations: list[Violation] = []
        for i, (a, p) in enumerate(boxes):
            for b, q in boxes[i + 1:]:
                if (p["x"] < q["x"] + q["width"] and q["x"] < p["x"] + p["width"]
                        and p["y"] < q["y"] + q["height"] and q["y"] < p["y"] + p["height"]):
                    violations.append(
                        Violation(
                            self.name,
                            self.severity,
                            visual_pointer(report.report_dir, page, a, "position"),
                            f"Visual overlaps '{b}'",
                            expected="no shared area between content visuals",
                            actual={a: p, b: q},
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
    return ReportSpec(invariants=[PageSize(), ForbiddenVisualTypes(), VisualWithinPage(), VisualsDoNotOverlap()])


def check_report(report_dir: Path, spec: ReportSpec | None = None) -> list[Violation]:
    return (spec or default_spec()).check(parse_report(report_dir))
