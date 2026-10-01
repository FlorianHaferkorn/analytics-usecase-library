# Idiom × Zielplattform — Machbarkeit (Stand 30.09.2026)

Status: `flint` = Flint-chartType in VegaVisual · `vega_lite` = Vega-Lite-Spec in VegaVisual ·
`native` = Kernvisual/Komponente ohne Eigenbau · `custom_svg` = eigenes React/SVG (DataGrid-cellRenderer
oder eigene Komponente) · `deneb` · `svg_measure` · `nicht_moeglich`. Erste Nennung = Erstwahl.
PBIR-Spalte: native-Typ aus `tooling/visual_library/registry.json` (gemessen 07./08.09.2026 gegen
Katalog 0.1.1, ADR-0021), Rest aus Registry-Spuren. HTML: Vega-Lite über vega-embed oder
`renderVisualToSvg` (fabric-visuals 4.1.0 headless), sonst Inline-SVG/D3.
Beleg = ID in `fabric.yaml`. „(ungeprüft)“ = nicht gerendert, nur aus Typen/Doku abgeleitet.

| Idiom | fabric_app | pbir | html | Beleg |
|---|---|---|---|---|
| area_stacked | vega_lite (area + stack); Flint „Area Chart“ mit color, Stapelmodus nicht steuerbar | native `stackedAreaChart`; deneb | vega_lite | 002, 003, 035 |
| bar_absolute | flint „Bar Chart“; vega_lite für IBCS-Details | native `clusteredBarChart`; svg_measure; deneb | vega_lite | 002, 007 |
| bar_ranking | flint „Bar Chart“ + `sortOrder`; Scroll ab 15 Kategorien abschalten | native `clusteredBarChart`; svg_measure; deneb | vega_lite | 002, 007 |
| bar_stacked | flint „Stacked Bar Chart“; vega_lite | native `columnChart`; deneb | vega_lite | 002 |
| boxplot | flint „Boxplot“; vega_lite `boxplot` | deneb (kein Kernvisual) | vega_lite | 002, 014, 034 |
| bullet | flint „Bullet Chart“ (`goal` Pflicht); vega_lite layer bar+tick | svg_measure; deneb (kein Kernvisual) | vega_lite | 002, 015 |
| column_time | flint „Bar Chart“ mit Zeit-x; vega_lite (Schraffur: custom_svg, ungeprüft) | native `clusteredColumnChart`; Umriss nativ, Schraffur nur deneb | vega_lite | 002, 013, 025 |
| decomposition_tree | custom_svg (eigene React-Komponente; kein Flint-Typ, Vega nicht zugelassen) | native `decompositionTreeVisual` | custom_svg | 001, Registry |
| deviation_bar | vega_lite (bar + bedingte Farbe); Flint „Pyramid Chart“ nur für zwei Seiten | native `clusteredBarChart`; svg_measure; deneb | vega_lite | 002, 004 |
| donut | vega_lite `arc` + innerRadius (Flint-innerRadius wird ignoriert) | native `donutChart`; deneb | vega_lite | 003, 007 |
| dumbbell | flint „Ranged Dot Plot“; vega_lite rule+point | svg_measure; deneb | vega_lite | 002 |
| histogram | flint „Histogram“ (binCount nicht steuerbar); vega_lite `bin` | deneb (kein Kernvisual) | vega_lite | 002, 003 |
| indexed_line | vega_lite (joinaggregate/calculate) oder flint „Line Chart“ auf vorindizierten Daten | native `lineChart`; svg_measure; deneb | vega_lite | 002, 026 |
| kpi_card_bullet | flint „KPI Card“ (metric, value, goal) oder vega_lite `labelCallout` + Bullet-Layer, chromeless | svg_measure (Karte/Callout-Bild) | vega_lite oder Inline-SVG | 002, 011, 028 |
| kpi_card_spark | flint „Sparkline“ + HTML-Karte; vega_lite | native `kpi`; svg_measure (TrendSVG-Muster) | vega_lite oder Inline-SVG | 002, 011, 028 |
| kpi_card_sparkbar | vega_lite bar chromeless in HTML-Karte | svg_measure | vega_lite oder Inline-SVG | 011, 019, 028 |
| line | flint „Line Chart“ (strokeDash-Kanal); vega_lite | native `lineChart` (Strichlinien, Fehlerband) ; svg_measure; deneb | vega_lite | 002, 024, 026 |
| lollipop | flint „Lollipop Chart“; vega_lite | svg_measure; deneb | vega_lite | 002 |
| matrix_bullet | custom_svg (DataGrid-cellRenderer); Flint „Bar Table“ als Näherung ohne Soll | svg_measure | custom_svg (Tabelle + Inline-SVG) | 018, 028 |
| matrix_delta_pill | custom_svg (DataGrid-cellRenderer, HTML-Pille) | svg_measure (bedingte Formatierung ergänzend) | HTML/CSS | 018, 028 |
| matrix_evidence | native `DataGrid` | native `tableEx`; svg_measure | HTML-Tabelle | 018 |
| matrix_sparkline | custom_svg (cellRenderer + Inline-SVG); VegaVisual je Zelle möglich, aber schwer (ungeprüft) | native `tableEx.sparklines`; svg_measure | Inline-SVG | 018, 027 |
| sankey | custom_svg (z. B. d3-sankey; Vega-Lite hat kein Sankey, Vega nicht zugelassen) | deneb (volle Vega-Spec) oder Sankey-Custom-Visual | custom_svg / Vega | 001, 014, 034 |
| scatter | flint „Scatter Plot“; vega_lite | native `scatterChart`; deneb | vega_lite | 002 |
| slope | flint „Slope Chart“; vega_lite | native `lineChart`; svg_measure; deneb | vega_lite | 002 |
| small_multiples | flint Kanäle `column`/`row`; vega_lite `facet` | native (14 Typen, `smallMultiplesLayout`); deneb | vega_lite | 005, 027 |
| stacked_100 | vega_lite `stack: normalize` (Flint-stackMode wird ignoriert) | native `hundredPercentStackedColumnChart`; deneb | vega_lite | 003 |
| waterfall_buildup | flint „Waterfall Chart“ (totals nicht steuerbar); vega_lite window+bar | native `waterfallChart`; deneb | vega_lite | 002, 003, 008 |
| waterfall_pvm | vega_lite (feste Farbdomäne je Treiber, zwei Layer für Eckenradius) | native `waterfallChart`; deneb | vega_lite | 008, 014 |
| waterfall_variance | vega_lite | native `waterfallChart`; deneb | vega_lite | 008, 014 |

## Stilmittel × Ziel

| Stilmittel | fabric_app | pbir | html | Beleg |
|---|---|---|---|---|
| Schraffur (IBCS Prognose) | custom_svg: `fill: "url(#id)"` + eigenes `<pattern>` im DOM (ungeprüft); alternativ Verlauf mit harten Stops (ungeprüft) | deneb (vordefinierte Muster); Kernvisuals nicht | vega_lite / SVG | 013, 025, 032 |
| Umriss-Balken (IBCS Plan) | vega_lite (`fillOpacity 0`/`fill null` + stroke) | native (fillTransparency + border) | vega_lite | 013, 025 |
| Strichlinie (Prognose) | vega_lite `strokeDash`; flint `strokeDash`-Kanal | native (`lineStyles.strokeDashArray`) | vega_lite | 002, 026 |
| Fehlerbalken/-band | vega_lite `errorbar`/`errorband` | native (Analytics-Pane, Objekt `error`) | vega_lite | 014, 024 |
| Soll-/Referenzlinie | vega_lite `rule` + benannte Datentabelle | native Referenzlinien; deneb | vega_lite | 015, 024 |
| Annotationen (Text an Datenpunkt) | vega_lite `text`-Layer | Datenlabels nativ, freie Annotation nur deneb/svg_measure | vega_lite | 014 |
| Eckige Balken | configVegaLite `cornerRadiusEnd: 0` (Default 4) | native (eckig) | vega_lite | 006, 008 |
| Eigene Schrift | theme.typography oder configVegaLite.font; Quelle der Schrift: Hosting-CSP unklar | nur lokal installierte Schriften | @font-face frei | 010, 023, 030 |
| Tastaturnavigation im Diagramm | ab fabric-visuals 4.1.0 (Scaffold pinnt 4.0.0) | Power-BI-Standard (nicht untersucht) | eigene Umsetzung | 017 |
| Cross-Filter zwischen Visuals | Host-Logik über `onInteraction` | native; deneb | eigene Umsetzung | 016, 033 |
