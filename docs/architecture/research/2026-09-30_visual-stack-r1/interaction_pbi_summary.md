# Strang interaction_pbi: Konsumenten-Baseline eines Power-BI-Visuals (30.09.2026)

76 Einträge in `interaction_pbi.yaml`, 43 davon `must_have_for_parity: true`. Primärquellen sind Microsoft Learn (über den MCP gelesen) und das npm-Paket `@microsoft/fabric-visuals` 4.0.0/4.1.0 mit `-core` 4.0.0.
`user_value`, `must_have_for_parity` und `vegavisual.status` sind eigene Einschätzungen (inferred). VegaVisual-Status über alle Einträge: 18 native, 11 partial, 37 build, 10 n_a.

## Paritätsbaseline (Must-haves) und VegaVisual-Stand

| Bereich | Must-have (IDs) | VegaVisual heute | Zu bauen |
|---|---|---|---|
| Tooltip | Standard + Zusatzfelder (001, 002), Crosshair Linie (007), Drill-Footer (004) | native: vega-tooltip, Theme, Crosshair, Spaltenformate (4.1.0) | Aktionen im Tooltip |
| Auswahl | Klick = Cross-Filter/-Highlight (010), Strg-Mehrfachauswahl (011), Leerfläche löscht (012) | Self-Highlight + `onInteraction` mit Set-/Range-Prädikaten | Weitergabe an andere Visuals, Highlight-Rendering im Ziel |
| Interaktionsmatrix | Filter/Highlight/None je Ziel (013), Legende wählt Serie (014) | fehlt | Host-Logik, Legend-Binding |
| Kontextmenü | Rechtsklick/Long-Press mit Datenpunktaktionen (017) | fehlt (nur Copy) | Menü |
| Drill | 4 Drill-Aktionen (020), Klickmodus Auswahl vs. Drill (021), Drillthrough + Zurück (022) | fehlt | Hierarchie-State, Spec-Tausch, Routing |
| Header | Header-Icons (030), Focus (031), Show as table (032), Export mit Limits (034), Sortieren (036), Copy mit Caption (038), Filteranzeige (045) | VisualContainer mit Header, nur `copyVisual` | alles außer Copy; `fabric-datagrid` als Tabellenbaustein |
| Filter | Slicer-Stile (050), relative Datumsauswahl mit Anker (051), Bereichsslider (052), Filterbereich (054), Field Parameters (055) | fehlt (RangePredicate-Typ vorhanden) | Host-Komponenten |
| Zustand | Bookmarks/Standardansicht (060) | fehlt | Serialisierung (URL/DB) |
| Chart-Funktionen | Kategorien-Scroll (071), bedingte Farben (073), Referenzlinien (074), Small Multiples (078) | native: Scroll (Schwelle 15, Fenster 10), Vega-Lite condition/rule/facet | Auswahl über Multiples hinweg |
| Barrierefreiheit | 3-Ebenen-Tastatur (090), Tastenkürzel (091), Screenreader (092), Alt-Text datengetrieben (093), SR-Tabelle (094), Hochkontrast (096) | 4.1.0: Overlay mit Pfeil/Enter/Esc/Tab, ARIA; `useCssTheme` forced-colors | Tastaturauswahl an `onInteraction`, Kürzel, generierter Alt-Text, HTML-Tabelle |
| Mobil | Long-Tap-Tooltip mit Drill (100), Hoch-/Querformat (102) | nicht belegt | Long-Press, responsives Seitenlayout |

Gemessen (lokal, Paketinhalt): 4.1.0 bringt die Tasten ArrowUp/Down/Left/Right, Enter, Escape und Tab im Bundle mit (String-Suche im Bundle).
Hergeleitet, nicht gemessen: ob die Enter-Taste eine Auswahl über `onInteraction` meldet. Ein Browser-Test steht aus.

## Wo wir Power BI schlagen können (hergeleitet)
- Eine Datentabelle für Maus und Screenreader zugleich: Power BI hat hier zwei Wege, einer davon ist nicht screenreadertauglich (094).
- Deterministische Varianzzerlegung statt „Explain the increase“. Das Power-BI-Feature fällt in Apps, bei Embedding, RLS und DirectQuery weg (042).
- Datengetriebener Aussagesatz als Alt-Text und Untertitel statt eines nichtdeterministischen Copilot-Texts (044, 093).
- Vega-Lite-Parameter rechnen What-if ohne Server-Roundtrip und ohne die Grenze von 1.000 Werten (056).

## Lücken
- Für VegaVisual gibt es keine Microsoft-Learn-Doku. Suchen nach „Fabric apps visuals“, „VegaVisual“ und „fabric-visuals“ liefern nur Rayfin-Backend-Seiten (117).
- `fabric-visuals-core` kennt kein Hover-Event („TODO: User hovered over a data point“). Es gibt keine Drill-API und keine eingehende Highlight-API; der Weg führt nur über die Vega-View im Handle (115, inferred).
- Die Rechteckauswahl in Standard-Visuals ist nur indirekt belegt, über den Hinweis „in Small Multiples deaktiviert“ (016).
- Für die Learn-Seiten fehlt `date_published`: `ms.date` war nicht lesbar, weil der Proxy blockiert.

## Widersprüche
- Die Export-Limits unterscheiden sich je Seite. Die Power-BI-Seite nennt csv 30.000 / xlsx 150.000 / Live-xlsx 500.000. Die JS-API-Seite „Export data from a visual“ nennt pauschal 30.000 und behauptet „Export is not available on visuals using model or report measures“, was der Hauptseite widerspricht. Die Hauptseite gilt als maßgeblich.
- Zu Alerts auf Report-Visuals widersprechen sich die Seiten. Die Power-BI-Seite (Vorschau) nennt den Weg über das Kontextmenü am Visual. Die Fabric-Activator-Seite verlangt die Bearbeitungsansicht und Edit-Recht. Die Reading-View-Seite sagt, Alerts gelten nur für Dashboard-Kacheln (040).
- Zur Auswahl: Laut dem Visual-Interactions-Artikel lassen sich Linie und Scatter nur cross-filtern, nicht highlighten. Die Small-Multiples-Seite beschreibt dagegen Cross-Highlight über einen Linienpunkt (013 vs. 007/015).
- Zu fabric-visuals 4.0.0: Der CHANGELOG datiert die Version auf den 09.09.2026, die npm-Registry auf den 15.09.2026.

## Blockiert
- Direkter Abruf von learn.microsoft.com per curl: CONNECT 403 (Egress-Proxy). Die Inhalte kamen vollständig über den Learn-MCP.
- npmjs.com-Paketseite per WebFetch: HTTP 403. Ausweg über registry.npmjs.org und den Tarball 4.1.0.

## Bewusst nicht gemacht
- Keinen Browser-Test des 4.1.0-Overlays gefahren. Der Auftrag war Recherche, und das Ergebnis gehört in eine eigene Messrunde.
- Keine Autorenfunktionen erfasst (Edit interactions UI, Format-Pane-Details), nur ihre Wirkung beim Leser.
- Dashboard-Kacheln, Paginated Reports und Matrix-/Tabellen-Visual-Interaktionen nicht vertieft. Scope ist das Chart-Visual.
