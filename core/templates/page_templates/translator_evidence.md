# Evidence.dev Visual Mapping (Whitelist)

Dieses Mapping übersetzt die tool-agnostischen Visualtypen aus der Whitelist in Evidence.dev Visualtypen.

| Visual Type (Abstract) | Evidence VisualType   | Hinweise |
|-----------------------|----------------------|----------|
| kpi_card              | evidence:stat        | Für Headline-KPIs, Status, Delta |
| trend_line            | evidence:line        | Für Zeitreihen, Verlauf |
| bar_chart             | evidence:bar         | Für Ranking, Segmentvergleich |
| column_chart          | evidence:column      | Für Vergleiche, Segmentierung |
| waterfall             | evidence:waterfall   | Für Treiber, Abweichung |
| matrix                | evidence:table       | Für Detail, Drilldown |
| ranking               | evidence:bar/column  | Sortierte Darstellung, Top-N |
| smart_narrative       | evidence:text        | Zusammenfassung, Textbox |
| slicer                | evidence:filter      | Filterelement |

**Hinweis:**
- Nur Visualtypen aus der [Visual Whitelist](visual_whitelist.md) dürfen gemappt werden.
- Bei fehlender 1:1-Entsprechung ist die fachlich beste Alternative zu wählen und zu dokumentieren.
