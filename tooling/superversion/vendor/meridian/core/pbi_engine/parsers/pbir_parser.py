"""
PBIR Parser — liest report.json / page.json / visual.json aus PBIP Report-Ordner.
"""

from __future__ import annotations
import json
import re
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
    # Slicer-Darstellung: "" / "list" -> Basic-Liste (Default), "between" -> Datums-
    # Range-Slider (objects.data.mode='Between'). Aus dem Manifest via format.style.
    slicer_style: str = ""
    # Generierungsfeld (pbir-Target, D-RPT10 17.07.2026): Slicer-Sync-Gruppe. Slicer mit
    # gleichem groupName synchronisieren seitenübergreifend (visual.syncGroup). Aus v.syncGroup.
    sync_group: str = ""
    # Generierungsfelder (pbir-Target, D-RPT10): Anzeigeeinheiten der cardVisual Reference-
    # Labels (Wert- bzw. Detail-Zeile) — sonst zeigen absolute Ref-Measures rohe/"0 Mio"-Werte.
    # Aus format.refValueUnits / format.refDetailUnits (Mapping wie display_units).
    ref_value_units: str = ""
    ref_detail_units: str = ""
    # Multi-Measure-Card (D-RPT19): je Measure eigene Reference-Labels mit per-Feld-Einheiten.
    # Aus bindings.values = [{"measure","referenceLabels":[{value,detail}],"valueUnits","detailUnits"}].
    # Liste von {"measure","ref_labels","value_units","detail_units"}. Leer = Einzel-Card-Pfad.
    value_specs: list = field(default_factory=list)
    # Matrix-Subtotals (pivotTable): None = nicht emittieren (Power-BI-Default = beide an),
    # True/False = objects.subTotals.rowSubtotals/columnSubtotals explizit setzen. Aus dem
    # Manifest via format.rowSubtotals / format.columnSubtotals (Fallback: format.subtotals).
    row_subtotals: bool | None = None
    column_subtotals: bool | None = None
    # Conditional Formatting (pivotTable/tableEx-Werte, D-RPT15 20.07.2026): Field-Value-
    # CF (Ampel). Aus format.conditional = {"color": {"column","measure","font"}} (oder Liste).
    # None = keine CF. Farb-Logik lebt als Text-Hex-Measure im Modell.
    conditional: dict | None = None
    # ── Generischer Formatting-Durchreicher (D-327, 14.07.2026) ──────────────
    # Statt jede Power-BI-Formatting-Property einzeln als Feld nachzuruesten (davon
    # gibt es Hunderte — ein Fass ohne Boden), nehmen diese drei Felder beliebige
    # Property-Maps entgegen; das pbir-Target uebersetzt sie in die Literal-Form.
    #
    #   objects       -> visual.objects                (Datenformatierung: grid,
    #                    columnHeaders, rowHeaders, subTotals, data, header ...)
    #   container     -> visual.visualContainerObjects (Rahmen: title, subTitle,
    #                    divider, spacing, background, border ...)
    #   column_widths -> objects.columnWidth mit metadata-Selector je Feld
    #                    ({"dim_land.Mandant": 260, "_Measures.X": 80})
    #
    # Anlass: Der Kunde formatierte den Report in Desktop (Titel, Untertitel,
    # Spaltenbreiten, Zeilenabstand, Dropdown-Slicer). Das Manifest konnte nichts
    # davon ausdruecken — ein Rebuild haette die Arbeit geloescht.
    objects: dict = field(default_factory=dict)
    container: dict = field(default_factory=dict)
    column_widths: dict = field(default_factory=dict)
    # Generierungsfeld (pbir-Target, T3 02.07.2026): Measures, die als eigene
    # "Tooltips"-Query-Rolle projiziert werden sollen (statt in Values geflacht).
    # "Entity.Measure"- oder nackte Measure-Namen; owner wird beim Emit aufgelöst.
    tooltip_measures: list[str] = field(default_factory=list)
    # Generierungsfelder (pbir-Target, T1 04.07.2026, Chart-Emission):
    # Category-Rolle (Achse) für columnChart/lineChart-artige Visuals —
    # "Entity.Column"-String, analog slicer_field. bound_measures liefert die
    # Y-Rolle (Säulen-/Balkenwerte); legend_field ist die optionale Legend-Rolle
    # (Serien-Aufteilung, "Entity.Column"). line_measures sind die Y2-Rolle
    # (Linien-Werte) bei Combo-Charts — Measure-Namen wie bound_measures.
    category_field: str = ""
    # Mehrstufige Kategorie-Achse (05.08.2026): Power BI rendert aus mehreren
    # Category-Projektionen eine DRILL-HIERARCHIE mit Auf-/Abwaerts-Buttons. Der
    # Emitter konnte bisher nur EIN Feld — deshalb liess sich ein Pareto ueber
    # Kundenland -> Kunde -> Kundenvariante nicht bauen, obwohl PBI es kann.
    # category_field bleibt der Einzelfall-Weg; ist diese Liste gefuellt, gewinnt sie.
    category_fields: list[str] = field(default_factory=list)
    legend_field: str = ""
    line_measures: list[str] = field(default_factory=list)
    # Generierungsfeld (pbir-Target, T4 04.07.2026): labelDisplayUnits-Literal
    # exakt wie im PBIR-Orakel (z.B. "1D" fuer Auto/Ohne-Einheit-Kürzung, PBI
    # kodiert Display-Units als DAX-Double-Literal-String) — wird 1:1 in
    # visual.objects.labels[0].properties.labelDisplayUnits geschrieben, kein
    # Mapping/Raten von Werten wie "millions" -> Zahl in der Emission.
    display_units: str = ""
    # Generierungsfeld (pbir-Target, D-RPT8 16.07.2026): cardVisual Callout-Nachkommastellen
    # (objects.value.labelPrecision). None = nicht setzen (PBI-Default). Aus format.decimals.
    card_precision: int | None = None
    # Generierungsfeld (pbir-Target, D-RPT7 16.07.2026): cardVisual Reference Labels
    # (Δ-Zeilen unter dem Hauptwert). Liste von {"value": <measure>, "detail": <measure>}
    # (beide optional), an das erste Data-Measure der Card gebunden.
    reference_labels: list[dict] = field(default_factory=list)
    # Generierungsfeld (pbir-Target, D-RPT9 17.07.2026): Visual-Level Top-N-Filter
    # {"field": "Entity.Column", "measure": <measure>, "top": <int>} — begrenzt eine
    # Ranking-Tabelle auf die Top-N nach measure (sonst Tausende Zeilen / O(n²)-Measures).
    top_n: dict = field(default_factory=dict)
    # Generierungsfeld (pbir-Target, 30.07.2026): explizite Sortierung ->
    # query.sortDefinition. {"measure": <m>} ODER {"field": "Entity.Column"},
    # plus optional "direction": "Descending"|"Ascending" (Default Descending).
    # Top-N begrenzt die MENGE, ordnet sie aber nicht — fuer Pareto-Sichten muss
    # die Reihenfolge explizit gesetzt werden, sonst ist die Kumulationskurve
    # unlesbar. Shape ist query-weit, gilt daher fuer jeden Visualtyp mit query.
    sort_spec: dict = field(default_factory=dict)
    # Generierungsfeld (pbir-Target, D-326): Visual-Level-Categorical-Filter
    # analog page_filters. Jeder Eintrag: {"field": "Entity.Column", "value":
    # <literal|[literal,...]>} — wird zu visual.json filterConfig.filters mit
    # In-Where emittiert (gleiche Shape wie Page-Filter, siehe _categorical_filter).
    visual_filters: list[dict] = field(default_factory=list)
    # --- REINE LESE-Felder (Audit), 02.08.2026 ---------------------------------
    # Bewusst getrennt von den Generierungsfeldern darueber. `visual_filters`,
    # `top_n` und `page_filters` werden vom pbir-Target GESCHRIEBEN und nie
    # gelesen; sie beim Parsen mitzubefuellen haette die Byte-Stabilitaet der
    # Generierung zur Wette gemacht. Ein gelesener Wert und ein zu schreibender
    # Wert sind nicht dasselbe, auch wenn sie gleich heissen.
    bound_columns: list[str] = field(default_factory=list)
    shows_items_with_no_data: bool = False
    #: Aus `filterConfig.filters` gelesen. Je Eintrag: {"target": "Measure"|"Column",
    #: "name": <Property>, "type": <filter type, z. B. "TopN">}.
    parsed_filters: list[dict] = field(default_factory=list)
    # Generierungsfelder (pbir-Target, D-326): Textbox-Visual. text ist der rohe
    # Paragraph-Inhalt (NICHT expr/Literal-gewrappt); text_font_size (pt),
    # text_color (#RRGGBB Schriftfarbe), text_bg (#RRGGBB Container-Hintergrund)
    # sind optionales Formatting.
    text: str = ""
    text_bg: str = ""
    text_color: str = ""
    text_font_size: int = 0
    # Generierungsfelder (Phase 1, 24.07.2026): actionButton mit Seiten-Navigation
    # (nav_target = Ziel-Page-Name, text = Button-Label) und dunkle Akzent-Card
    # (accent_fill = #RRGGBB fuer new-card fillCustom + heller Text). Leer = aus.
    nav_target: str = ""
    accent_fill: str = ""
    # shape-Rechteck (Phase 1, 24.07.2026): dekoratives Panel (z.B. Sidebar).
    # shape_fill = #RRGGBB Fuellfarbe, shape_radius = Eckenradius in px. Leer/0 = Theme-Default.
    shape_fill: str = ""
    shape_radius: int = 0
    # image-Visual (Phase 1, 24.07.2026): Logo/Bild aus RegisteredResources.
    # image_name = Dateiname (im Branding-Ordner), image_fit = Fit|Stretch|Fill|Normal.
    image_name: str = ""
    image_fit: str = ""
    # pageNavigator (Phase 1, 24.07.2026): nativer Seiten-Navigator (Nav-Pane).
    # nav_orientation = 'vertical'|'horizontal', nav_show_hidden = versteckte Seiten mitzeigen.
    nav_orientation: str = ""
    nav_show_hidden: bool = False
    # Referenzlinien (v5, 27.07.2026): Liste von {label, measure|value, color, style} ->
    # objects.y1AxisReferenceLine. Wert entweder an ein Measure gebunden (dynamisch, z.B.
    # 'Plan-Bedarf pro Tag') oder eine Konstante (z.B. Book-to-Bill = 1,0).
    reference_lines: list = field(default_factory=list)
    # rawObjects (Capture, 27.07.2026): report-formatige objects-Einträge (inkl. Selektoren),
    # VERBATIM in visual.objects gemergt — für finalisierte Spezial-Formate (z.B. Data Bars/
    # columnFormatting), die der generische _obj_block-Passthrough nicht ausdrücken kann.
    raw_objects: dict = field(default_factory=dict)
    # Sortier-/Top-N-Befund (RL020, BC-CHART-10): worst-first-Ordnung + explizites
    # Top-N auf Ranking-/Evidence-Tabellen. sort_keys = Feldnamen aus
    # query.sortDefinition.sort (leer = keine explizite Sortierung); top_n = itemCount
    # eines Top-N-Visual-Filters (None = keiner). Beim Parsen best-effort befüllt.
    sort_keys: list[str] = field(default_factory=list)
    top_n: "int | None" = None
    # Werteachsen-Start (RL022, BC-CHART-09): visual.objects.valueAxis[].properties.start
    # als Zahl (PBIR-Literal, z.B. "50D"→50.0). None = kein expliziter Start (auto/
    # nullbasiert); ein Wert ≠ 0 = abgeschnittene Baseline (verzerrt Balkenlängen).
    value_axis_start: "float | None" = None
    # Dekoratives Chrome (RL023, BC-CHART-04): Namen der Chartjunk-Objekte auf dem Visual
    # (background/shadow/gradient/bevel/glow mit show=true). Leer = decluttered.
    decorative_objects: list[str] = field(default_factory=list)


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
    # Generierungsfeld (pbir-Target, T3 02.07.2026): Page-Level-Filter analog
    # page.json filterConfig.filters. Jeder Eintrag: {"field": "Entity.Column",
    # "value": <literal>} — wird zu einem Categorical-Filter mit In-Where emittiert.
    page_filters: list[dict] = field(default_factory=list)
    # Generierungsfelder (pbir-Target, D-326): Page-Background-Bild. Wird zu
    # page.json objects.background + einem RegisteredResources-Package in
    # report.json emittiert; das PNG kopiert die Pipeline nach StaticResources/
    # RegisteredResources/. Leer = kein Background (Default, byte-identisch).
    background_image: str = ""
    background_scaling: str = "Fit"
    background_transparency: int = 0
    # FREEZE (28.07.2026): Seite ist in Desktop finalisiert und wird vom Emitter NICHT
    # mehr neu geschrieben. Sie bleibt in pages.json (pageOrder), damit sie nicht als
    # Waise geloescht wird — aber page.json/visuals/ bleiben unangetastet. Schuetzt
    # manuelle Feinarbeit davor, vom naechsten Build ueberschrieben zu werden.
    frozen: bool = False
    # Page-Background als FARBE (config-driven, 23.07.2026): sehr helles Grau statt
    # manuell gemaltem PNG — weisse Karten "schweben". Hex-String; leer = keine
    # Farbe. Hat Vorrang vor background_image (nur EIN objects.background-Slot).
    background_color: str = ""
    # Generierungsfeld (pbir-Target, D-RPT5 16.07.2026): Drillthrough-ZIEL-Seite.
    # Liste von Spalten-Feldern ("Entity.Column"), auf die diese Seite als
    # Drillthrough-Ziel gebunden wird — emittiert filterConfig(howCreated=Drillthrough)
    # + pageBinding. Leer = normale Seite (Default, byte-identisch). Setzt zugleich
    # page_type="Drillthrough" (RL-Checks erkennen die Zielseite).
    drillthrough_fields: list[str] = field(default_factory=list)
    # Generierungsfeld (pbir-Target, D-RPT21): Cross-Filter/Highlight zwischen Visuals.
    # Jeder Eintrag: {"source": "<manifestVisualId>", "target": "<manifestVisualId>",
    # "type": "NoFilter"|"DataFilter"|"HighlightFilter"} -> page.json visualInteractions
    # mit visual_<id>-Namen. Leer = Power-BI-Default (alles cross-filtert).
    visual_interactions: list[dict] = field(default_factory=list)
    #: REINES LESE-Feld (Audit) — aus page.json `filterConfig.filters`.
    parsed_filters: list[dict] = field(default_factory=list)


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
    #: REINES LESE-Feld (Audit) — aus report.json `filterConfig.filters`.
    parsed_filters: list[dict] = field(default_factory=list)
    # False nur, wenn parse_report keinen .Report-Ordner fand (Modell-only-PBIP).
    # Direkt konstruierte Instanzen (Tests, Writer) repräsentieren echte Reports.
    exists: bool = True
    # True, wenn der .Report-Ordner im deprecateten report.json-Single-File-Format
    # vorliegt (kein definition/pages/). Der PBIR-Parser liest dieses Format NICHT
    # (Official-First: kein Legacy-Parser; Re-Save als PBIR ist der offizielle Pfad,
    # Runbook Schritt 2). Report-Layer-Regeln werden dann übersprungen statt blind
    # auf einem leeren Parse-Ergebnis zu feuern.
    is_legacy: bool = False
    pages: list[ReportPage] = field(default_factory=list)
    extension_measures: list[ExtensionMeasure] = field(default_factory=list)
    bookmarks: list[Bookmark] = field(default_factory=list)
    # Rohpfad des .Report-Ordners (T1, 02.07.2026, report_binding_rules): der
    # PBIR-Parser flacht Visuals in Dataclasses ab, die nicht alle Rohstrukturen
    # (filterConfig/objects/expansionStates) halten. Regeln, die das rohe
    # visual.json erneut einlesen müssen (RB001-RB003), nutzen diesen Pfad statt
    # den Parser um jede erdenkliche Rohstruktur zu erweitern.
    report_dir: Optional[Path] = None


def _parse_filters(cfg: dict) -> list[dict]:
    """`filterConfig.filters[]` → normalisierte Audit-Eintraege.

    Bis 02.08.2026 hat der Parser `filterConfig` **nie** gelesen — die gleichnamigen
    Felder am Modell werden ausschliesslich vom pbir-Target GESCHRIEBEN. Damit war
    jede Regel ueber Filter (Measure-Filter, TopN) unmoeglich zu bauen: sie haette
    gegen ein Feld geprueft, das beim Lesen immer leer ist, und waere still nie
    angeschlagen. Gemessen am gevendorten Fremd-Report: 3 Dateien mit `filterConfig`,
    davon der Report-Level mit mehreren Column-Filtern.

    Je Eintrag: `target` ("Column"|"Measure"|""), `name` (Property), `type`
    (Filtertyp; `TopN` ist der, an dem die offizielle BPA-Regel haengt).
    """
    out: list[dict] = []
    for f in (cfg or {}).get("filters") or []:
        if not isinstance(f, dict):
            continue
        feld = f.get("field") or {}
        ziel = next((k for k in ("Measure", "Column", "Aggregation", "HierarchyLevel")
                     if k in feld), "")
        inner = feld.get(ziel) if isinstance(feld.get(ziel), dict) else {}
        out.append({
            "target": ziel,
            "name": inner.get("Property", "") if isinstance(inner, dict) else "",
            "type": f.get("type", ""),
            "how_created": f.get("howCreated", ""),
        })
    return out


def parse_report(pbip_root: Path, report_name: Optional[str] = None) -> ReportModel:
    """Parst ein PBIP Report-Verzeichnis.

    Bei mehreren `.Report`-Ordnern unter `pbip_root` ist die Wahl sonst
    stillschweigend nicht deterministisch (erster iterdir()-Treffer). Über
    `report_name` (z.B. "Contoso_Auftragseingaenge_Reproduktion" oder der volle
    Ordnername inkl. ".Report") lässt sich der gewünschte Report explizit
    adressieren; ohne Hint wird bei Mehrdeutigkeit hart mit Auflistung der
    Kandidaten gefehlt statt still einen auszuwählen.
    """
    report_dir = _find_report_dir(pbip_root, report_name=report_name)
    report_name = report_dir.name.replace(".Report", "") if report_dir else pbip_root.name

    report = ReportModel(name=report_name, report_dir=report_dir)

    if not report_dir or not report_dir.exists():
        report.exists = False
        return report

    # Legacy-Erkennung: das deprecatete Single-File-Format hat report.json auf
    # Report-Root-Ebene und KEIN definition/pages/. Der PBIR-Parser liest es nicht
    # (Official-First — Re-Save als PBIR, Runbook Schritt 2). Früh zurück, damit
    # nicht ein leeres Parse-Ergebnis (0 Seiten, kein Theme) Report-Regeln triggert.
    if (report_dir / "report.json").exists() and not (report_dir / "definition" / "pages").exists():
        report.is_legacy = True
        return report

    # report.json für Theme — PBIR legt es in definition/report.json oder report.json
    for report_json in [report_dir / "definition" / "report.json", report_dir / "report.json"]:
        if report_json.exists():
            try:
                data = json.loads(report_json.read_text(encoding="utf-8"))
                theme = data.get("themeCollection", {}).get("baseTheme", {})
                report.theme = theme.get("name", "")
                report.parsed_filters = _parse_filters(data.get("filterConfig") or {})
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


def _find_report_dir(pbip_root: Path, report_name: Optional[str] = None) -> Optional[Path]:
    # pbip_root selbst ist ein .Report-Verzeichnis (Fabric: Report+Modell getrennt,
    # z.B. Meridian-derive-Output — der UC.Report wird direkt uebergeben)
    if pbip_root.is_dir() and ".Report" in pbip_root.name and (pbip_root / "definition").is_dir():
        return pbip_root
    if not pbip_root.is_dir():
        return None

    candidates = sorted(
        (d for d in pbip_root.iterdir() if d.is_dir() and ".Report" in d.name),
        key=lambda d: d.name,
    )
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    # Mehrere .Report-Ordner: explizites report_name-Arg bevorzugen (voller
    # Ordnername oder Report-Name ohne ".Report"-Suffix), sonst hart fehlen
    # statt still den ersten Treffer zu waehlen (vorheriges Verhalten war
    # iterdir()-Reihenfolge-abhaengig und damit nicht deterministisch).
    if report_name:
        for d in candidates:
            if d.name == report_name or d.name == f"{report_name}.Report":
                return d
        names = ", ".join(c.name for c in candidates)
        raise ValueError(
            f"_find_report_dir: report_name={report_name!r} passt auf keinen der "
            f"{len(candidates)} .Report-Ordner unter {pbip_root}: {names}"
        )

    names = ", ".join(c.name for c in candidates)
    raise ValueError(
        f"_find_report_dir: {len(candidates)} .Report-Ordner unter {pbip_root} "
        f"gefunden ({names}) — mehrdeutig ohne explizites report_name-Arg. "
        f"parse_report(pbip_root, report_name=...) mit einem der obigen Namen aufrufen."
    )


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
        parsed_filters=_parse_filters(data.get("filterConfig") or {}),
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


def _collect_measure_bindings(node, out: set) -> None:
    """Sammelt JEDE `{"Measure": {"Property": ...}}`-Bindung im Visual-JSON.

    `queryState.*.projections[]` deckt nur die DATEN-Rollen ab. Measures koennen
    aber auch ausserhalb gebunden sein — Conditional Formatting (fontColor,
    backColor, dataBars), Sort-Definitionen, Filter. Ohne diesen Scan gilt ein
    reines Formatierungs-Measure faelschlich als tot (SM011). Befund 29.07.
    (Contoso-Repro): `Forward-Matrix-Farbe` ist ausschliesslich als fontColor
    gebunden und wurde als "unbenutzt" gemeldet — Loeschen haette die
    Ampelfarben der Forward-Matrix entfernt.
    """
    if isinstance(node, dict):
        measure = node.get("Measure")
        if isinstance(measure, dict) and measure.get("Property"):
            out.add(measure["Property"])
        for value in node.values():
            _collect_measure_bindings(value, out)
    elif isinstance(node, list):
        for value in node:
            _collect_measure_bindings(value, out)


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
    visual.parsed_filters = _parse_filters(vcfg.get("filterConfig") or {})
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
            # Column-Projektionen wurden bis 02.08.2026 verworfen. Gemessen am
            # gevendorten Fremd-Report (BPA.Report, 18 Visuals): 17 Column-Projektionen
            # gegen 9 Measures — der Audit sah also gut zwei Drittel der genutzten
            # Felder nicht. Damit war jede Regel ueber die ANZAHL genutzter Objekte
            # systematisch zu niedrig, ohne dass es auffiel.
            if "Column" in f and isinstance(f["Column"], dict):
                prop = f["Column"].get("Property")
                ent = ((f["Column"].get("Expression") or {}).get("SourceRef") or {}).get("Entity")
                if prop:
                    visual.bound_columns.append(f"{ent}.{prop}" if ent else prop)
            # `showItemsWithNoData` haengt an der Projektion, nicht am Visual.
            if p.get("showItemsWithNoData") or p.get("ShowItemsWithNoData"):
                visual.shows_items_with_no_data = True
            calc = f.get("NativeVisualCalculation")
            if isinstance(calc, dict) and calc.get("Name"):
                visual.visual_calculations.append(VisualCalculation(
                    name=calc["Name"],
                    expression=calc.get("Expression", ""),
                    language=calc.get("Language", "dax"),
                ))

    # Measure-Bindungen ausserhalb der Daten-Rollen (Conditional Formatting, Sort,
    # Filter) nachtragen. `binds_measures` bleibt unberuehrt — das beschreibt, ob das
    # Visual Measures als DATEN fuehrt, und eine Ampelfarbe macht daraus kein
    # Daten-Visual. Ueber das ganze Dokument gescannt, nicht nur ueber `vcfg`, damit
    # auch visualContainerObjects erfasst sind.
    extra_bindings: set = set()
    _collect_measure_bindings(data, extra_bindings)
    for name in sorted(extra_bindings):
        if name not in visual.bound_measures:
            visual.bound_measures.append(name)
    # Sort-/Top-N-Befund (RL020): worst-first-Ordnung + Top-N. query.sortDefinition
    # trägt die explizite Sortierung; ein leeres sort[] oder isDefaultSort zählt NICHT
    # als governte Worst-First-Ordnung. Top-N lebt als Visual-Level-Filter (Shape im
    # PBIR-Korpus unbelegt, s. target/pbir.py — daher best-effort, nie erfunden).
    sort_def = vcfg.get("query", {}).get("sortDefinition", {}) or {}
    for entry in sort_def.get("sort", []) if isinstance(sort_def.get("sort"), list) else []:
        if not isinstance(entry, dict):
            continue
        fld = entry.get("field") or {}
        meas = fld.get("Measure") or fld.get("Column") or {}
        prop = meas.get("Property") if isinstance(meas, dict) else None
        if prop:
            visual.sort_keys.append(prop)
    for filt in vcfg.get("filters", []) if isinstance(vcfg.get("filters"), list) else []:
        if not isinstance(filt, dict):
            continue
        ftype = str(filt.get("type") or filt.get("filterType") or "")
        count = filt.get("itemCount") or filt.get("topN") or (filt.get("filter", {}) or {}).get("itemCount")
        if "top" in ftype.lower() and isinstance(count, int):
            visual.top_n = count

    # Werteachsen-Start (RL022, BC-CHART-09): abgeschnittene Balken-Baseline erkennen.
    for block in (vcfg.get("objects", {}) or {}).get("valueAxis", []) or []:
        start = ((block or {}).get("properties") or {}).get("start")
        if not isinstance(start, dict):
            continue
        try:
            lit = start["expr"]["Literal"]["Value"]
        except (KeyError, TypeError):
            continue
        m = re.match(r"-?\d+(?:\.\d+)?", str(lit))
        if m:
            visual.value_axis_start = float(m.group())
            break

    # Dekoratives Chrome (RL023): background-Fill (show=true) + shadow/gradient/bevel/glow.
    _objs = vcfg.get("objects", {}) or {}
    for _blk in _objs.get("background", []) or []:
        _show = ((_blk or {}).get("properties") or {}).get("show", {})
        if isinstance(_show, dict) and str((_show.get("expr", {}).get("Literal", {}) or {}).get("Value", "")).lower() == "true":
            visual.decorative_objects.append("background")
            break
    for _key in _objs:
        if any(_j in _key.lower() for _j in ("shadow", "gradient", "bevel", "glow")):
            visual.decorative_objects.append(_key)

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
