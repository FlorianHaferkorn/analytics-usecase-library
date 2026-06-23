"""
PBIR Parser — liest report.json / page.json / visual.json aus PBIP Report-Ordner.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class VisualCalculation:
    """Visual Calculation aus der queryState-Projektion (A2, D-196):
    Feld-Typ `NativeVisualCalculation` (semanticQuery/1.0.0)."""
    name: str
    expression: str = ""
    language: str = "dax"


@dataclass
class Visual:
    visual_id: str
    visual_type: str
    x: float = 0
    y: float = 0
    width: float = 0
    height: float = 0
    title: str = ""
    has_title: bool = True
    # Tooltip-Befund (RL011, D-182)
    binds_measures: bool = False      # queryState enthält Measure-Projektionen
    has_tooltip_fields: bool = False  # Tooltips-Rolle mit Projektionen
    has_tooltip_vco: bool = False     # visualTooltip in visualContainerObjects
    visual_calculations: list[VisualCalculation] = field(default_factory=list)
    # Namen aller gebundenen Measures (inkl. Tooltips-Rolle) — SM011-Korpus (D-210)
    bound_measures: list[str] = field(default_factory=list)
    # Generierungs-Felder (vom pbir-Target genutzt; beim Parsen leer):
    # "Entity.Property"-Strings für Matrix-Rollen bzw. Slicer-Bindung.
    rows: list[str] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    slicer_field: str = ""


@dataclass
class ReportPage:
    name: str
    display_name: str = ""
    visuals: list[Visual] = field(default_factory=list)
    width: int = 1280
    height: int = 720
    page_type: str = "Default"        # "Default", "Drillthrough", "Tooltip"
    has_mobile_layout: bool = False
    is_hidden: bool = False           # page.json visibility: 1 = HiddenInViewMode


@dataclass
class ExtensionMeasure:
    """Report-Level-Measure aus definition/reportExtensions.json (A1, D-196).

    Extension Measures leben im Thin-Report statt im Semantic Model —
    eigene Governance-Fläche (RL012)."""
    name: str
    table: str            # entity name (Zieltabelle der Erweiterung)
    expression: str = ""
    data_type: str = ""
    is_hidden: bool = False
    format_string: str = ""


@dataclass
class Bookmark:
    """Bookmark aus definition/bookmarks/ (A2, D-196): Metadaten +
    <name>.bookmark.json mit explorationState.activeSection als Zielseite."""
    name: str
    display_name: str = ""
    target_page: str = ""


@dataclass
class ReportModel:
    name: str
    theme: str = ""
    pages: list[ReportPage] = field(default_factory=list)
    extension_measures: list[ExtensionMeasure] = field(default_factory=list)
    bookmarks: list[Bookmark] = field(default_factory=list)


def parse_report(pbip_root: Path) -> ReportModel:
    """Parst ein PBIP Report-Verzeichnis."""
    report_dir = _find_report_dir(pbip_root)
    report_name = report_dir.name.replace(".Report", "") if report_dir else pbip_root.name

    report = ReportModel(name=report_name)

    if not report_dir or not report_dir.exists():
        return report

    # report.json für Theme — PBIR legt es in definition/report.json oder report.json
    for report_json in [report_dir / "definition" / "report.json", report_dir / "report.json"]:
        if report_json.exists():
            try:
                data = json.loads(report_json.read_text(encoding="utf-8"))
                theme = data.get("themeCollection", {}).get("baseTheme", {})
                report.theme = theme.get("name", "")
            except Exception:
                pass
            break

    # Extension Measures — offizieller Ort: definition/reportExtensions.json
    for ext_json in [report_dir / "definition" / "reportExtensions.json",
                     report_dir / "reportExtensions.json"]:
        if ext_json.exists():
            report.extension_measures = _parse_report_extensions(ext_json)
            break

    # Bookmarks — offizieller Ort: definition/bookmarks/
    for bm_dir in [report_dir / "definition" / "bookmarks", report_dir / "bookmarks"]:
        if bm_dir.is_dir():
            report.bookmarks = _parse_bookmarks(bm_dir)
            break

    # Pages einlesen — PBIR legt sie in definition/pages/ oder pages/
    for pages_dir in [report_dir / "definition" / "pages", report_dir / "pages"]:
        if pages_dir.exists():
            for page_dir in sorted(pages_dir.iterdir()):
                if page_dir.is_dir():
                    page = _parse_page(page_dir)
                    if page:
                        report.pages.append(page)
            break

    return report


def _find_report_dir(pbip_root: Path) -> Optional[Path]:
    # pbip_root selbst ist ein .Report-Verzeichnis (Fabric: Report+Modell getrennt,
    # z.B. Meridian-derive-Output — der UC.Report wird direkt uebergeben)
    if pbip_root.is_dir() and ".Report" in pbip_root.name and (pbip_root / "definition").is_dir():
        return pbip_root
    if pbip_root.is_dir():
        for d in pbip_root.iterdir():
            if d.is_dir() and ".Report" in d.name:
                return d
    return None


def _parse_page(page_dir: Path) -> Optional[ReportPage]:
    page_json = page_dir / "page.json"
    if not page_json.exists():
        return None

    try:
        data = json.loads(page_json.read_text(encoding="utf-8"))
    except Exception:
        return None

    page = ReportPage(
        name=page_dir.name,
        display_name=data.get("displayName", page_dir.name),
        width=data.get("width", 1280),
        height=data.get("height", 720),
        # PBIR: visibility 1 = HiddenInViewMode; String-Variante zur Sicherheit
        is_hidden=data.get("visibility") in (1, "HiddenInViewMode"),
    )

    # Extract page type: neueres PBIR nutzt top-level "type", älteres "pageBinding.type"
    if "type" in data:
        page.page_type = data["type"]
    else:
        page_binding = data.get("pageBinding", {})
        page.page_type = page_binding.get("type", "Default")

    # Visuals
    visuals_dir = page_dir / "visuals"
    if visuals_dir.exists():
        for visual_dir in visuals_dir.iterdir():
            if visual_dir.is_dir():
                visual = _parse_visual(visual_dir)
                if visual:
                    page.visuals.append(visual)

    # Check mobile layout — any visual with mobile.json = mobile layout configured
    if visuals_dir.exists():
        for visual_dir in visuals_dir.iterdir():
            if visual_dir.is_dir() and (visual_dir / "mobile.json").exists():
                page.has_mobile_layout = True
                break

    return page


def _parse_visual(visual_dir: Path) -> Optional[Visual]:
    visual_json = visual_dir / "visual.json"
    if not visual_json.exists():
        return None

    try:
        data = json.loads(visual_json.read_text(encoding="utf-8"))
    except Exception:
        return None

    vcfg = data.get("visual", {})
    vtype = vcfg.get("visualType", "unknown")
    pos = data.get("position", {})

    visual = Visual(
        visual_id=visual_dir.name,
        visual_type=vtype,
        x=pos.get("x", 0),
        y=pos.get("y", 0),
        width=pos.get("width", 0),
        height=pos.get("height", 0),
    )

    # Container-Objekte: Schema 2.x nutzt "visualContainerObjects",
    # Altbestand "vcObjects" — beide lesen (D-182-Nebenbefund).
    vc_objects = vcfg.get("visualContainerObjects") or vcfg.get("vcObjects") or {}

    # Titel
    title_cfg = vc_objects.get("title", [{}])
    if title_cfg and isinstance(title_cfg, list):
        props = title_cfg[0].get("properties", {})
        title_text = props.get("text", {}).get("expr", {}).get("Literal", {}).get("Value", "")
        if title_text:
            visual.title = title_text.strip("'")
        show = props.get("show", {}).get("expr", {}).get("Literal", {}).get("Value", "true")
        visual.has_title = str(show).lower() != "false"

    # Tooltip-Befund (RL011): Tooltips-Rolle + visualTooltip-VCO
    visual.has_tooltip_vco = bool(vc_objects.get("visualTooltip"))
    query_state = vcfg.get("query", {}).get("queryState", {})
    for role, role_cfg in query_state.items():
        projections = role_cfg.get("projections", []) if isinstance(role_cfg, dict) else []
        if not projections:
            continue
        if role == "Tooltips":
            visual.has_tooltip_fields = True
        for p in projections:
            if not isinstance(p, dict):
                continue
            f = p.get("field") or {}
            if "Measure" in f:
                visual.binds_measures = True
                prop = f["Measure"].get("Property") if isinstance(f["Measure"], dict) else None
                if prop:
                    visual.bound_measures.append(prop)
            calc = f.get("NativeVisualCalculation")
            if isinstance(calc, dict) and calc.get("Name"):
                visual.visual_calculations.append(VisualCalculation(
                    name=calc["Name"],
                    expression=calc.get("Expression", ""),
                    language=calc.get("Language", "dax"),
                ))

    return visual


def _parse_report_extensions(ext_json: Path) -> list[ExtensionMeasure]:
    """Liest definition/reportExtensions.json (Schema reportExtension/1.0.0):
    entities[].measures[] mit name/dataType/expression (+ optionale Felder)."""
    try:
        data = json.loads(ext_json.read_text(encoding="utf-8"))
    except Exception:
        return []

    measures: list[ExtensionMeasure] = []
    for entity in data.get("entities", []):
        table = entity.get("name", "")
        for m in entity.get("measures", []):
            if not m.get("name"):
                continue
            measures.append(ExtensionMeasure(
                name=m["name"],
                table=table,
                expression=m.get("expression", ""),
                data_type=m.get("dataType", ""),
                is_hidden=bool(m.get("hidden", False)),
                format_string=m.get("formatString", ""),
            ))
    return measures


def _parse_bookmarks(bm_dir: Path) -> list[Bookmark]:
    """Liest definition/bookmarks/: jede <name>.bookmark.json wird ein Bookmark
    (Schema bookmark/1.0.0); bookmarks.json-Metadaten sind nur Reihenfolge/
    Gruppierung und für den Audit nicht nötig."""
    bookmarks: list[Bookmark] = []
    for bm_file in sorted(bm_dir.glob("*.bookmark.json")):
        try:
            data = json.loads(bm_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        name = data.get("name") or bm_file.name.replace(".bookmark.json", "")
        bookmarks.append(Bookmark(
            name=name,
            display_name=data.get("displayName", ""),
            target_page=(data.get("explorationState") or {}).get("activeSection", ""),
        ))
    return bookmarks
