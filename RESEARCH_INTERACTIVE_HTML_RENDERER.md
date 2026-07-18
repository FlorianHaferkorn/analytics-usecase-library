# Research — Interaktiver HTML-Renderer als zusätzliches ALUCA-Target

> Companion zu [`KONZEPT_REPORT_QUALITAET.md`](KONZEPT_REPORT_QUALITAET.md) (§7 „Maximize Power BI"
> ist heute PBIR-zentriert; ALUCA ist aber **viz-tool-agnostisch** — PBIR ist *ein* Renderer). Diese
> Notiz leitet aus einer Deep-Research ab, wie ein **interaktiver, self-contained HTML-Report** als
> alternatives/zusätzliches Compile-Target neben PBIR aussehen könnte — passend zum
> Spec-kompiliert-zu-Renderer-Modell (governte Bracket-Spec: `message`/`so_what`/KPI/Action-Code).
>
> Geteiltes Handwerkswissen mit der Meridian-Initiative (Repo Freelancing) — **getrennte Tools, kein
> Co-Branding.**

| Feld | Wert |
|---|---|
| Stand | 2026-07-13 |
| Methodik | Deep-Research-Harness: 6 Winkel → 25 Quellen → 65 Claims → 25 adversarial verifiziert (3-Stimmen, 2/3-Refute). **25/25 bestätigt, 0 widerlegt.** Nur Primärquellen (Docs/GitHub/License); Listicles (LogRocket/Medium/HackerNoon) fielen als „unreliable" durch. |
| Anlass | Flo-Anfrage: „React HTML / Three React → wirklich interaktive HTML-Reports für unsere beiden Konzepte." |

## 1. Verifiziertes Fundament (Primärquellen)

- **Eine öffenbare Datei** via Build-time-Render + `vite-plugin-singlefile` (inlined Modulgraph JS/CSS
  in ein `dist/index.html`). Caveats: **`public/`-Assets nicht ge-inlined** (alles über Import-Graph
  routen), **Hash-Routing** statt History-API, keine Cookies/Sourcemaps unter `file:///`.
- **Offizieller React-19-Split** = die Interaktivitäts-Grenze:
  `react-dom/static` **`prerender`** (deterministisches SSG, wartet auf alle Daten) als Build-Modus;
  `renderToStaticMarkup` für **statische** Exhibits (nicht hydrierbar); `renderToString`+**`hydrateRoot`**
  als **Hydration-Islands** nur dort, wo Drill-down/Cross-Filter/Tooltip nötig ist.

## 2. Self-Containment-Fallen (belegt)

| Tool | Falle | Konsequenz |
|---|---|---|
| Plotly `to_html` | `'cdn'` braucht Internet; nur `include_plotlyjs=True` inlined ~3 MB → offline | wenn Plotly, dann `True` |
| Dash | inhärent server-gebunden, `dash2html` verliert Interaktivität | ausgeschlossen |
| Highcharts | Client-Export fällt still auf Remote-Server zurück (außer `fallbackToExportServer=false`) | Offline-/Datenschutz-Risiko |
| Observable Plot SSR | headless SVG (JSDOM+`outerHTML`) — degradiert bei Geo/>1000 Elementen | dichte/Geo-Exhibits nicht vorserialisieren |

## 3. WebGL/3D — nur deck.gl gerechtfertigt

deck.gl (MIT) Aggregation-Layers (Hexagon/Grid-Binning, Contour, KDE-Heatmap) sind echte analytische
Transforms; **`@deck.gl/json`** löst eine deklarative JSON-Spec direkt in ein Deck auf → **native
Zielspur für den ALUCA-Compiler** bei großskaligen/geospatialen Exhibits. **Three.js/react-three-fiber:
kein verifizierter analytischer Use-Case** — für Boutique-IBCS-Exhibits dekorativ, draußen lassen.

## 4. Ableitung für ALUCA (Spec-kompiliert-zu-Renderer)

- **HTML-Renderer als zusätzliches Adapter-Target neben PBIR** (viz-tool-agnostisch bleibt gewahrt):
  Bracket-Spec → React-Komponenten → `prerender` + `vite-plugin-singlefile` → eine öffenbare Datei.
- Gros der McKinsey-Exhibits ist **statisch** → `renderToStaticMarkup`; **selektive Hydration-Islands**
  nur für Drill-down/Cross-Filter. Determinismus = Build-Time, reproduzierbar (kein Request-Server) →
  passt zum Golden-Thread-/Generator-Prinzip (referenzieren, nicht neu definieren).
- Der PBIR-Adapter (`products/fabric/powerbi/tooling/adapters/pbip.py`) bleibt unberührt; das
  HTML-Target wäre ein **paralleler Adapter** hinter derselben IR (`tooling/generator_core/ir/`).

## 5. Offene Punkte (vor Bau-Entscheidung)

1. Single-File-Größe bei hydriertem React+Charting-Bundle bzw. inlined plotly.js (~3 MB) — ab wann
   Code-Splitting/Multi-File nötig.
2. Determinismus/Reproduzierbarkeit gehashter Build-Outputs im ALUCA-CI (aktuell Python-zentriert; ein
   Node/Vite-Build-Schritt wäre neu — Kosten/Nutzen vs. PBIR-only).
3. **Per-Library-Matrix unverifiziert** (Recharts/Visx/Nivo/Tremor/ECharts-React: Bundle, A11y, SSR,
   Interaktivitätsmodell) — Listicles durchgefallen. Falls konkrete Chart-Lib festzulegen: enger Zweit-Lauf.

## Quellen (verifiziert, Primär)

vite-plugin-singlefile (github.com/richardtallent/vite-plugin-singlefile) · react-dom/static prerender
(react.dev) · renderToStaticMarkup (react.dev) · RSC/MDX static build (github.com/wooorm/server-components-mdx-demo)
· deck.gl (github.com/visgl/deck.gl · deck.gl/docs · deck.gl/docs/api-reference/layers) · Observable Plot
getting-started (observablehq.com/plot) · Plotly to_html (plotly.com) · Highcharts client-side export
(highcharts.com) · dash2html (pypi.org/project/dash2html) · AG Charts pricing (ag-grid.com/charts/license-pricing).
