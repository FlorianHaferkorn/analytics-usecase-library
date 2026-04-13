# Power BI Visual Mapping (Whitelist)

Dieses Mapping übersetzt die tool-agnostischen Visualtypen aus der Whitelist in Power BI Visualtypen.

| Visual Type (Abstract) | Power BI VisualType      | Hinweise |
|-----------------------|-------------------------|----------|
| kpi_card              | Card Visual             | Für Headline-KPIs, Status, Delta |
| trend_line            | Line Chart              | Für Zeitreihen, Verlauf |
| bar_chart             | Bar Chart (horizontal)  | Für Ranking, Segmentvergleich |
| column_chart          | Column Chart (vertikal) | Für Vergleiche, Segmentierung |
| waterfall             | Waterfall Visual        | Für Treiber, Abweichung |
| matrix                | Table/Matrix            | Für Detail, Drilldown |
| ranking               | Bar/Column Chart        | Sortierte Darstellung, Top-N |
| smart_narrative       | Smart Narrative         | Zusammenfassung, Textbox |
| slicer                | Slicer                  | Filterelement |

**Hinweis:**
- Nur Visualtypen aus der [Visual Whitelist](visual_whitelist.md) dürfen gemappt werden.
- Bei fehlender 1:1-Entsprechung ist die fachlich beste Alternative zu wählen und zu dokumentieren.
