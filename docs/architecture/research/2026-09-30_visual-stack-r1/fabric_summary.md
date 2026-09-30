# R1d fabric — Zusammenfassung (30.09.2026)
## Kernaussagen
1. **Vega-Lite ist der gemeinsame Nenner.** VegaVisual nimmt volle Vega-Lite-6-Specs (layer, facet,
   params, transforms), aber **kein Vega** (Typ-Union VL | Flint, fabric-001). Deneb spricht Vega
   und Vega-Lite. 21 von 30 Idiomen haben eine Deneb-VL-Spur (Registry) → eine VL-Spec für alle drei Ziele.
2. **Eigene Wege je Ziel brauchen:** `sankey` (Fabric: custom_svg, PBIR: Deneb/Vega),
   `decomposition_tree` (Fabric/HTML: custom, PBIR: nativ), Matrix-Idiome mit Mini-Grafik
   (Fabric: DataGrid-cellRenderer, PBIR: svg_measure bzw. tableEx.sparklines).
3. **Flint ist bequem, aber nicht steuerbar:** `chartProperties` wird in 4.0.0 und 4.1.0 ignoriert
   (d.ts), obwohl der Template-Skill sie dokumentiert. Donut, 100 %-Stapel, Wasserfall-Totals,
   Histogramm-Bins daher über Vega-Lite. Flint braucht semanticType je Spalte.
4. **VegaVisual verändert Specs zur Laufzeit** (15 capability-Flags: kompakte Zahlen, Mindest-
   balken, Scroll ab 15 Kategorien, Self-Highlight, Crosshair, Stapel-Labels). Eine Library, die
   ein IBCS-Bild zusagt, muss diese Flags explizit setzen; sonst weicht das Fabric-Bild vom
   Deneb-/HTML-Bild derselben Spec ab. `config` im Spec wird überschrieben → nur `configVegaLite`.
5. **Theming:** `useCssTheme` liest 8 Farbvariablen + `--color-data-1..10`, **keine Schrift** (Segoe-Stack, bis `theme.typography`/`configVegaLite.font` greift).
6. **Schraffur:** Weder Vega-Lite noch Power-BI-Kernvisuals haben Musterfüllung. Vega-Lite nimmt
   aber jeden Farbstring; der SVG-Renderer (VegaVisual rendert SVG) schreibt ihn als fill-Attribut,
   also sollte `url(#id)` mit eigenem `<pattern>` im DOM greifen. Das ist Deneb's Mechanismus;
   für Fabric **nicht gerendert, ANNAHME**. PBIR nativ: Umriss-Balken (fillTransparency + border)
   und Strichlinien ja, Schraffur nein.
7. **Barrierefreiheit:** Diagramm-Tastaturnavigation erst ab fabric-visuals **4.1.0** (23.09.2026);
   Scaffold 1.36.0 pinnt 4.0.0 (Bundle ohne Keydown-Handler, grep = 0). DataGrid: aria-sort, Tastatur.
8. **Interaktion:** nur `select`/`clear` mit Prädikaten, Cross-Filter baut der Host, Hover fehlt
   (TODO im Typ). Deneb: Tooltip, Kontextmenü, Cross-Filter, Cross-Highlight.
9. **Power BI nativ:** Fehlerbalken (Balken/Säulen/Linie/Kombi), Fehler- und Prognoseband in
   lineChart, Small Multiples in 14 Typen, Sparklines in Tabelle/Matrix (Katalog 0.1.1).

## Webfont / CSP (Antwort)
- **Microsoft Learn dokumentiert keine CSP-Header für das Fabric-Apps-Hosting.** Belegt sind nur:
  ZIP ≤ 100 MB, `assetAccess` protected/public, Einbettung als verschachteltes iframe im Portal.
- Der Microsoft-Template-Skill (`app-design/SKILL.md`) weist an, Schriften per Google-Fonts-`<link>`
  zu laden — das spricht dafür, dass externe Schriften geladen werden dürfen, ist aber eine
  Anleitung, keine CSP-Zusage. Die Existenz von `EmbeddableVegaVisual` und die Wahl von `VegaVisual`
  im Scaffold deuten darauf, dass `unsafe-eval` im Hosting erlaubt ist (ANNAHME, ungeprüft).
- **Selbst gehostete Schriften** (woff2 im `dist/`, `@font-face` same-origin) sind der robustere Weg:
  kein Drittanbieter-Request aus Kundentenant (DSGVO), unabhängig von einer späteren CSP-Verschärfung.
  Funktion auf dem Host: **ANNAHME, ungeprüft** — messbar erst mit einem echten `rayfin up`
  (Response-Header `Content-Security-Policy` der Hosting-URL lesen).
- PBIR: keine Webfonts (Schrift muss installiert sein); Deneb zertifiziert lädt keine URLs;
  SVG-Measures als `<img>` laden keine externen Ressourcen (ANNAHME) → nur Systemschriften.

## Widersprüche zwischen Quellen
- `chartProperties`: d.ts/README „ignoriert“ vs. Skill `flint-authoring.md` dokumentiert sie.
- Schrift: `formatting.md` nennt `--font-base` als Chart-Stellschraube; der Code liest sie nicht.
- 4.0.0-CHANGELOG „Add Data Navigator library … for accessible overlay“ vs. Bundle ohne Import
  (erst 4.1.0 „Integrate accessible overlay with VegaVisual“).
- Deneb-Version: GitHub-Tag 2.0.0.0 (03.09.2026) vs. Suchtreffer „aktuell 1.8“ (alte Doku).

## Lücken / offene Fragen
- CSP-Header des Fabric-Apps-Hostings: nicht dokumentiert, nicht gemessen (kein Deployment vorhanden;
  die Hosting-URLs im Repo sind Beispiele).
- `url(#pattern)`-Schraffur in VegaVisual: nicht gerendert. Prüfbar headless mit `renderVisualToSvg`
  (4.1.0) + `<defs>` im Host-Dokument.
- Offizielle Deneb-Musterliste und -Doku (deneb.guide, deneb-viz.github.io) und vega.github.io waren
  per Egress-Proxy gesperrt; Musternamen nur aus Community-Beitrag (sekundär).
- SVG-Measure-Längengrenze: 32.766 gilt belegt nur für geladenen Text; die oft genannte 32k-Grenze je
  Measure ist nicht offiziell belegt.
- Bundle-Größe VegaVisual nicht gemessen (nur Ordnergrößen: dist 192 KB, vega 3,6 MB, vega-lite 8,3 MB).
- awesome-rayfin (existiert) nicht im Detail gelesen; PBI-Tastaturnavigation nicht untersucht.
