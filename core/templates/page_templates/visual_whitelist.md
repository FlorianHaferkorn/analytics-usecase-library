# Visual Whitelist (Abstract Layer)

Nur folgende Visualtypen sind in tool-agnostischen Page Templates erlaubt. Diese Liste wird zentral gepflegt und ist verbindlich für alle Templates und Übersetzer.

| Visual Type (Abstract) | Beschreibung | Beispiel-Use | Mapping Power BI | Mapping Evidence |
|-----------------------|--------------|--------------|------------------|------------------|
| kpi_card              | KPI-Karte mit Status/Delta | Headline-KPI      | Card Visual      | evidence:stat    |
| trend_line            | Zeitreihen-/Trend-Chart    | Entwicklung, Verlauf | Line Chart    | evidence:line    |
| bar_chart             | Balkendiagramm (horizontal) | Ranking, Segment | Bar Chart         | evidence:bar     |
| column_chart          | Säulendiagramm (vertikal)   | Vergleich, Segment | Column Chart      | evidence:column  |
| waterfall             | Wasserfalldiagramm         | Treiber, Abweichung | Waterfall Visual | evidence:waterfall |
| matrix                | Tabelle/Matrix              | Detail, Drilldown | Table/Matrix      | evidence:table   |
| ranking               | Sortierte Liste             | Top-N, Bottom-N   | Bar/Column Chart  | evidence:bar/column |
| smart_narrative       | Text/Narrative              | Zusammenfassung   | Smart Narrative   | evidence:text    |
| slicer                | Filterelement               | Kontextfilter     | Slicer            | evidence:filter  |

**Hinweis:**
- Visuals außerhalb dieser Liste sind in Templates und Übersetzern nicht zulässig.
- Die Mappings werden in den Übersetzer-Dateien gepflegt.
- Erweiterungen der Whitelist nur mit fachlicher Begründung und Review.
