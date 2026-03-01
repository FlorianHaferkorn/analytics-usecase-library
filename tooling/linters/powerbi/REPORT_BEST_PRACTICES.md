# Report Best Practices (BPA Rules)

Lesbare Übersicht der Regeln aus `bpa-rules-report.json`. Diese Regeln werden von `validate_report.ps1` gegen Power-BI-Report-Dateien (PBIP) ausgewertet.

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
| ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY | Keine vertikale Scroll-Seiten | max. Höhe 720 px | Ja |
| ENSURE_ALTTEXT | Alt-Text für alle Visuals (Barrierefreiheit) | — | **Nein** (disabled) |

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
- **Was:** Seiten vom Typ **Tooltip** oder **Drillthrough** müssen in der View ausgeblendet sein (`visibility = HiddenInViewMode`).
- **Warum:** Diese Seiten sind nur als Overlay/Drillthrough gedacht und sollen nicht in der Seitenliste erscheinen.
- **Aktion bei Verstoß:** Sichtbarkeit der betroffenen Seiten auf „Hidden in view mode“ setzen.

### ENSURE_THEME_COLOURS
- **Was:** Charts (außer Textboxen) dürfen **keine** hart codierten Hex-Farben (z. B. `#FF0000`) verwenden; es sollen Theme-Farben genutzt werden.
- **Warum:** Einheitliches Erscheinungsbild und einfache Anpassung über das Report-Theme.
- **Aktion bei Verstoß:** Custom-Farben in den Visuals durch Theme-Farben ersetzen (z. B. über „Theme colors“ im Formatierungsbereich).

### ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY
- **Was:** Sichtbare Seiten sollen **nicht höher als 720 px** sein (kein vertikales Scrollen).
- **Parameter:** implizit max. **720** px Höhe.
- **Warum:** Einheitliche Darstellung auf verschiedenen Bildschirmgrößen; keine „langen“ Scroll-Seiten.
- **Aktion bei Verstoß:** Seitenhöhe verkleinern oder Inhalt auf weitere Seiten verteilen.

### ENSURE_ALTTEXT
- **Was:** Alle Visuals (außer Shapes) sollen **alternativeText** für Screenreader gesetzt haben.
- **Warum:** Barrierefreiheit.
- **Status:** In der Standard-Konfiguration **deaktiviert** (`disabled: true`). Kann in `bpa-rules-report.json` aktiviert werden.

---

## Verwendung

```powershell
# Einzelnen Report prüfen
& tooling/validation/validate_report.ps1 -ReportPath "products/fabric/powerbi/dist/Commercial.SemanticModel/Report/COM-001.Report" -BpaRulesPath "tooling/linters/powerbi/bpa-rules-report.json"

# Über run_all_checks (Check 19f)
.\tooling\run_all_checks.ps1
```

Regeln anpassen: `tooling/linters/powerbi/bpa-rules-report.json` (Parameter in den jeweiligen Rule-`test`-Blöcken; `disabled: true` deaktiviert eine Regel).
