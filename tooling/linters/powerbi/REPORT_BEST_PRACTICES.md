# Report Best Practices (BPA Rules)

Lesbare Übersicht der Regeln aus `bpa-rules-report.json`. `validate_report.ps1` wertet davon REDUCE_PAGES, REDUCE_VISUALS_ON_PAGE, ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY und ENSURE_ALTTEXT gegen PBIR-Reports (`definition/pages/**`) aus und liest die Schwellen aus dieser Datei bzw. aus `layout_grid.yaml`; die übrigen Regeln wertet das Skript nicht aus.

**Version:** v1 · **Letzte Aktualisierung:** 2025-10-12 · **Owner:** analytics-core-team

---

## Übersicht

| ID | Kurzbeschreibung | Standard-Parameter | Aktiv |
|----|------------------|--------------------|-------|
| REMOVE_UNUSED_CUSTOM_VISUALS | Ungenutzte Custom Visuals entfernen | — | Ja |
| REDUCE_VISUALS_ON_PAGE | Anzahl sichtbarer Visuals pro Seite begrenzen | max. 20 | Ja |
| REDUCE_OBJECTS_WITHIN_VISUALS | Anzahl Objekte (Felder) pro Visual begrenzen | max. 6 | Ja |
| REDUCE_TOPN_FILTERS | TopN-Filter pro Seite begrenzen | max. 4 | Ja |
| REDUCE_ADVANCED_FILTERS | Advanced-Filter pro Seite begrenzen | max. 4 | Ja |
| REDUCE_PAGES | Anzahl Seiten pro Report begrenzen | max. 10 | Ja |
| AVOID_SHOW_ITEMS_WITH_NO_DATA | „Show items with no data“ vermeiden | — | Ja |
| HIDE_TOOLTIP_DRILLTROUGH_PAGES | Tooltip- und Drillthrough-Seiten ausblenden | — | Ja |
| ENSURE_THEME_COLOURS | Charts nutzen Theme-Farben (keine Hardcodierung) | — | Ja |
| ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY | Keine vertikale Scroll-Seiten | Leinwände aus `layout_grid.yaml` (1280×720, 1920×1080) | Ja |
| ENSURE_ALTTEXT | Alt-Text für alle Visuals (Barrierefreiheit) | ausgenommen `shape`; max. 250 Zeichen (Learn) | Ja (seit 01.10.2026) |

---

## Regeln im Detail

### REMOVE_UNUSED_CUSTOM_VISUALS
- **Was:** Custom Visuals, die in `publicCustomVisuals` referenziert sind, aber in keinem Visual des Reports verwendet werden, sollen entfernt werden.
- **Warum:** Reduziert Report-Größe und vermeidet unnötige Abhängigkeiten.
- **Aktion bei Verstoß:** Liste der zu entfernenden Custom-Visual-Namen; manuell aus Report/Referenzen entfernen.

### REDUCE_VISUALS_ON_PAGE
- **Was:** Pro Seite maximal eine feste Anzahl **sichtbarer** Visuals (ohne Shape, Slicer, Action-Button, Textbox).
- **Parameter:** `paramMaxVisualsPerPage` = **20** (Standard).
- **Warum:** Übersichtlichkeit und Performance; Vermeidung überladener Seiten.
- **Aktion bei Verstoß:** Seiten mit mehr als 20 zählbaren Visuals reduzieren oder aufteilen.

### REDUCE_OBJECTS_WITHIN_VISUALS
- **Was:** Pro Visual maximal 6 **Objekte** (Datenfelder in den Projektionen des Visuals).
- **Parameter:** implizit max. **6** Objekte.
- **Warum:** Weniger Felder pro Visual verbessert Lesbarkeit und oft Performance.
- **Aktion bei Verstoß:** Felder aus dem Visual entfernen oder auf mehrere Visuals verteilen.

### REDUCE_TOPN_FILTERS
- **Was:** Pro Seite maximal eine feste Anzahl von Visuals mit **TopN**-Filter.
- **Parameter:** `paramMaxTopNFilteringPerPage` = **4**.
- **Warum:** Zu viele TopN-Filter können Verhalten und Performance beeinträchtigen.
- **Aktion bei Verstoß:** TopN-Filter reduzieren oder auf andere Seiten verlagern.

### REDUCE_ADVANCED_FILTERS
- **Was:** Pro Seite maximal eine feste Anzahl von Visuals mit **Advanced**-Filter.
- **Parameter:** `paramMaxAdvancedFilteringVisualsPerPage` = **4**.
- **Warum:** Advanced-Filter sind rechenintensiver; Begrenzung verbessert Stabilität.
- **Aktion bei Verstoß:** Advanced-Filter pro Seite reduzieren.

### REDUCE_PAGES
- **Was:** Pro Report maximal eine feste Anzahl **Seiten**.
- **Parameter:** `paramMaxNumberOfPagesPerReport` = **10** (in der Regel im JSON nicht sichtbar, aber in der Beschreibung genannt).
- **Warum:** Fokussierte Reports; Vermeidung zu großer Dateien.
- **Aktion bei Verstoß:** Report in mehrere Reports aufteilen oder Seiten zusammenfassen.

### AVOID_SHOW_ITEMS_WITH_NO_DATA
- **Was:** Die Option **„Show items with no data“** soll auf Spalten nicht aktiviert sein.
- **Warum:** Vermeidet unerwünschte leere Zeilen und oft irreführende Darstellung.
- **Aktion bei Verstoß:** Liste der betroffenen Visual-Namen; Option in den Visual-Einstellungen deaktivieren.

### HIDE_TOOLTIP_DRILLTROUGH_PAGES
- **Was:** Seiten vom Typ **Tooltip** müssen in der View ausgeblendet sein (`visibility = HiddenInViewMode`). **Drillthrough**-Seiten (z. B. 300s-Detail) dürfen sichtbar bleiben, damit sie sowohl als eigene Seite als auch als Drillthrough-Ziel genutzt werden können.
- **Warum:** Tooltip-Seiten sind nur als Overlay gedacht. Drillthrough-Detailseiten sollen in der Seitenliste erscheinen und zusätzlich per Rechtsklick erreichbar sein.
- **Aktion bei Verstoß:** Sichtbarkeit der betroffenen Tooltip-Seiten auf „Hidden in view mode“ setzen.

### ENSURE_THEME_COLOURS
- **Was:** Charts (außer Textboxen) dürfen **keine** hart codierten Hex-Farben (z. B. `#FF0000`) verwenden; es sollen Theme-Farben genutzt werden.
- **Warum:** Einheitliches Erscheinungsbild und einfache Anpassung über das Report-Theme.
- **Aktion bei Verstoß:** Custom-Farben in den Visuals durch Theme-Farben ersetzen (z. B. über „Theme colors“ im Formatierungsbereich).

### ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY
- **Was:** Sichtbare Seiten (ohne `HiddenInViewMode` und Tooltip-Seiten) scrollen nicht vertikal.
- **Parameter (ALUCA, Entscheidung Florian 01.10.2026):** nicht die 720 px dieser Regeldatei, sondern die Leinwände aus `core/templates/page_templates/tokens/layout_grid.yaml` (`canvas.design_base` 1280×720, `canvas.production` 1920×1080). Eine Seite besteht, wenn sie einer Leinwand entspricht oder ihre Höhe ≤ Breite × Höhe/Breite der Leinwand ist. `FitToPage` skaliert und scrollt nicht (Übergröße wird als Info gemeldet), `FitToWidth` und `ActualSize` scrollen bei Übergröße (Warnung).
- **Warum:** Einheitliche Darstellung auf verschiedenen Bildschirmgrößen; keine „langen“ Scroll-Seiten.
- **Aktion bei Verstoß:** Seitenhöhe verkleinern oder Inhalt auf weitere Seiten verteilen.

### ENSURE_ALTTEXT
- **Was:** Alle Visuals (außer Shapes) sollen **alternativeText** für Screenreader gesetzt haben.
- **Warum:** Barrierefreiheit.
- **Status:** **Aktiv** seit 01.10.2026 (`disabled: false`, Entscheidung Florian), Schwere Info. Vorher deaktiviert; aktiviert meldete die Regel 220 von 220 Visuals der 17 dist-Reports.
- **Woher der Alt-Text kommt:** `products/fabric/powerbi/tooling/page_scaffold_generator/alt_text.py`, beim Generieren (Kennzahlen, Achse, Vergleichsreihe; Textbox = ihr Text). Reports ohne Generatorpfad: `python -m products.fabric.powerbi.tooling.page_scaffold_generator.alt_text <X.Report>`.
- **Sprache des Alt-Texts:** `ux_layout_rules.report_locale` im UseCase_Bracket (BCP 47, Default `en-US`; seit 01.10.2026 FIN-001 `de-DE`). Übersetzt werden die Satzbausteine des Moduls („compared with“ = „im Vergleich zu“, „by“ = „nach“, „Filter by“ = „Filtern nach“); Kennzahl- und Spaltennamen bleiben, wie das Visual sie bindet (Katalog und Modell führen keine lokalisierten Namen). Unbekannte Sprache: Englisch mit Warnung. Das Werkzeug ersetzt beim Sprachwechsel nur Alt-Text, den es selbst erzeugt hat.
- **Learn** (*Design Power BI reports for accessibility*, gelesen 01.10.2026): „Ensure alt text is added to all non-decorative visuals on the page.“ · „The Alt Text textbox has a limit of 250 characters.“ · „Because a screen reader reads out the title and type of a visual, you only need to fill in a description.“ Der Titel ersetzt den Alt-Text also nicht (`Design_Spec_3_30_300.md §9`).

---

## Verwendung

```powershell
# Einzelnen Report prüfen
& tooling/validation/validate_report.ps1 -ReportPath "products/fabric/powerbi/dist/COM-001_Sales_Performance.Report"

# Über run_all_checks (Check 19f)
.\tooling\run_all_checks.ps1
```

Regeln anpassen: `tooling/linters/powerbi/bpa-rules-report.json` (Parameter in den jeweiligen Rule-`test`-Blöcken; `disabled: true` deaktiviert eine Regel).
