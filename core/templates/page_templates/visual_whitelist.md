# Visual Whitelist (Abstract Layer) — **abgelöst (02.08.2026)**

> **Diese Datei ist NICHT mehr normativ.**
> Autorität für das Visualtyp-Vokabular ist
> [`visual_registry.yaml`](visual_registry.yaml).
> Entscheidung und Begründung: [ADR-0018](../../../docs/architecture/adr/0018-visual-vocabulary-single-authority.md).
>
> **Warum:** die Datei nannte sich „verbindlich für alle Templates und Übersetzer",
> wurde aber von keinem Checker gelesen. Eine Zusicherung, die nichts prüft, hält nicht.
>
> **Wozu sie bleibt:** die `Mapping Evidence`-Spalte unten ist die **Herkunft** der
> `evidence:*`-Einträge, die heute als `targets.evidence` in der Registry stehen. Wer
> eine solche Zuordnung belegen muss, findet hier ihren Ursprung — und in
> `translator_evidence.md` ihren gepflegten Stand.
>
> **Achtung, offene Folgearbeit:** die 20 Brackets deklarieren bis heute Typen aus der
> Liste unten (`kpi_card`, `trend_line`, `bar_chart`, `waterfall`, `line_chart`,
> `bar_chart_horizontal`). Sie sind damit **nicht falsch**, sondern folgen der
> abgelösten Autorität. Die Normalisierung auf die Registry ist Task **L2** in
> `KONZEPT_LAYOUT_SYSTEM.md`.

---

<details>
<summary>Historischer Stand (nicht mehr gültig)</summary>

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

</details>
