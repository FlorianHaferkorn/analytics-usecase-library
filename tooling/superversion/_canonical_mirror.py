"""_canonical_mirror — structure-identical mirror of Meridian's canonical contract.

This is ALUCA's **standalone substrate** (ADR-0005 rule 3, PRODUCT_PLAN F4): the
dataclasses are a verbatim mirror of Meridian's `core.pbi_engine.parsers.tmdl_parser`
/ `.pbir_parser` / `.model` — IDENTICAL field names, order, defaults and types — so
ALUCA builds and tests with **no** Meridian present.

`canonical_contract` re-exports Meridian's originals when the vendored core is
available and falls back to this mirror otherwise. Because the mirror is verbatim,
`model_to_json` is byte-identical in both modes (Invariant I2). Drift between this
mirror and the real contract is caught by `test_contract_parity_with_meridian`
(all dataclasses, both directions), enforced in CI where the vendored core is present.

Field parity verified against the vendored Meridian subtree (see PIN.json) on
2026-09-29 (Meridian a8eac299); the class bodies below are copied verbatim from
there, comments included. If Meridian's contract changes, the parity test fails
and this mirror must be re-synced in the same deliberate commit that moves the pin.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

__all__ = [
    "Column", "Measure", "RoleTablePermission", "RoleColumnPermission", "Role",
    "Table", "Relationship", "ModelFunction", "SemanticModel",
    "VisualCalculation", "Visual", "ReportPage", "ExtensionMeasure", "Bookmark",
    "ReportModel", "CanonicalModel",
]


# --- Semantic model (mirror of tmdl_parser) -------------------------------- #

@dataclass
class Column:
    name: str
    data_type: str = ""
    is_hidden: bool = False
    description: str = ""
    summarize_by: str = ""
    # DAX einer BERECHNETEN Spalte (``column X = <DAX>``); leer bei Quellspalten.
    # Zaehlt als Verwendungs-Nachweis: eine versteckte Spalte, die nur von einer
    # anderen Calc-Column gelesen wird, ist NICHT tot (SM010).
    expression: str = ""
    # Ziel eines ``sortByColumn:``. Ebenfalls eine echte Verwendung — die Sortier-
    # spalte ist meist versteckt und taucht in keinem DAX und keiner Beziehung auf.
    # Fehlte das hier, empfiehlt SM010 ihre Loeschung und zerlegt damit die
    # Sortierung (Befund 14.07.2026: dim_artikel[BereichSort]).
    sort_by_column: str = ""
    # Alternativ-Begriffe für semantisches Grounding (Cortex/Genie). Schema-first/optional:
    # leer ⇒ Targets leiten höchstens Namens-Varianten ab; gesetzt ⇒ governte Synonyme.
    synonyms: list = field(default_factory=list)


@dataclass
class Measure:
    name: str
    expression: str = ""
    display_folder: str = ""
    description: str = ""
    format_string: str = ""
    # Dynamischer Format-String (`formatStringDefinition = <DAX>`). Eigenes Feld,
    # weil dieser DAX-Ausdruck Measures, Spalten UND UDFs aufruft — Referenz-Scans
    # (SM010/SM011/UDF003) muessen ihn mitlesen, sonst gelten reine Format-Helfer
    # faelschlich als totes Material (Befund 29.07., Contoso-Repro: _FormatMagnitude
    # 28x / _FormatPercent 9x nur hier verwendet).
    format_string_definition: str = ""
    is_hidden: bool = False
    # Dialekt-Map (ADR-0036): Ausdruck je Ziel-Dialekt — Core liefert jedem Target
    # SEINEN Dialekt direkt (core->sql, nicht core->dax->sql). `expression` bleibt der
    # primaere/DAX-Ausdruck (Power-BI-Quelle); `expressions` traegt z.B. {"sql": ...}.
    expressions: dict = field(default_factory=dict)
    # Alternativ-Begriffe für semantisches Grounding (Cortex Analyst / Databricks Genie).
    synonyms: list = field(default_factory=list)


@dataclass
class RoleTablePermission:
    table: str
    filter_expression: str = ""


@dataclass
class RoleColumnPermission:
    table: str
    column: str
    metadata_permission: str = "read"  # "read" or "none"


@dataclass
class Role:
    name: str
    model_permission: str = "read"
    # ///-Doku ueber der role-Deklaration. Traegt bei Contoso die fachliche
    # Begruendung und die zugehoerige Entra-Gruppe — fuer die Uebergabe die
    # wichtigste Information an einer Rolle, deshalb geparst statt verworfen.
    description: str = ""
    table_permissions: list[RoleTablePermission] = field(default_factory=list)
    column_permissions: list[RoleColumnPermission] = field(default_factory=list)


@dataclass
class Table:
    name: str
    description: str = ""
    is_hidden: bool = False
    is_date_table: bool = False
    columns: list[Column] = field(default_factory=list)
    measures: list[Measure] = field(default_factory=list)
    has_partition: bool = False
    partition_type: str = ""  # "m" · "calculated" · "entity" (Direct Lake)
    m_expression: str = ""    # M-Skript der Partition (Power-Query-Regeln, D-160)
    # Direct-Lake-Partition (partition_type == "entity"): die Lakehouse-Delta-Tabelle,
    # die diese Modell-Tabelle im Direct-Lake-Modus bindet (source = entity).
    entity_name: str = ""     # entityName (Lakehouse-Tabellenname), default = table.name
    entity_schema: str = ""   # schemaName (default dbo)
    # Spaltennamen, die in Hierarchie-Levels referenziert werden —
    # gebraucht von SM010 (Unused Columns) als Verwendungs-Nachweis.
    hierarchy_columns: list[str] = field(default_factory=list)


@dataclass
class Relationship:
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    cardinality: str = ""       # oneToMany, manyToMany, etc.
    cross_filter: str = ""      # bothDirections, singleDirection
    is_active: bool = True


@dataclass
class ModelFunction:
    """DAX User-Defined Function aus definition/functions.tmdl (D-162)."""
    name: str
    expression: str = ""
    description: str = ""  # ///-Doku-Zeilen über der function-Deklaration


@dataclass
class SemanticModel:
    name: str
    tables: list[Table] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    roles: list[Role] = field(default_factory=list)
    functions: list[ModelFunction] = field(default_factory=list)
    # Aus database.tmdl; None = nicht deklariert (Fabric-Default greift)
    compatibility_level: Optional[int] = None
    # Parse-Parity (D-213): je Objektart (roh gezählt, geparst) —
    # Abweichung = Silent-Drop, wird von PAR001 laut gemacht.
    parse_parity: dict = field(default_factory=dict)


# --- Report model (mirror of pbir_parser) ---------------------------------- #

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


@dataclass
class CanonicalModel:
    """Vereinheitlichtes kanonisches Modell: Semantik UND Report (wie Meridian)."""
    semantic: SemanticModel
    report: ReportModel
