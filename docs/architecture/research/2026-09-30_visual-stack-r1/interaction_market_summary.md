# Strang market: Interaktionsmuster jenseits Power BI (Stand 30.09.2026)

40 Einträge in `interaction_market.yaml`: 18 fetched (Primärdateien über raw.githubusercontent.com), 22 nur
Suchauszug (Seite per Egress gesperrt, `evidence: null`). `vegalite_native`: 15 yes, 16 partial, 9 no.
`beyond_pbi`: 28 true, 12 false. `beyond_pbi` und `user_value` sind durchgehend eigene Ableitung; in diesem
Strang wurde keine Power-BI-Quelle gelesen.

## Top 10 "besser als Power BI" (Nutzwert x Machbarkeit in Vega-Lite)

| Rang | Muster (id) | VL | Quelle |
|---|---|---|---|
| 1 | Szenario-Schalter AC vs. PL/PY/FC, Abweichungen rechnen neu (market-029) | yes | Zebra BI Charts; VL `bind` (docs/bind.html) |
| 2 | Polarität/Invert: Kosten-KPIs drehen die Abweichungsfarbe (market-028) | yes | Zebra BI KB "invert and rename groups" |
| 3 | Hover-Rebasing: Zeigerpunkt wird Index 0 (market-001) | yes | VL-Galerie interactive_index_chart |
| 4 | Querschnitt-Tooltip aller Reihen + Pointing nur auf x-Achse (market-006, -011) | yes | VL interactive_multi_line_pivot_tooltip; Plot pointerX |
| 5 | Datenverankerte Annotationsschicht als Aussageträger (market-040, -013) | yes | IEEE VIS 2023 Annotation-Studie; VL layer_falkensee; Plot tip |
| 6 | Top N + "Übrige" summiert, auch nach Abweichung (market-009, -027) | yes | VL window_top_k_others; Zebra BI Top N |
| 7 | Brush-Mittelwert: markierter Zeitraum, Referenzlinie neu (market-002) | yes | VL selection_layer_bar_month |
| 8 | Datengebundene Kommentare je Periode als Marker + Tooltip (market-030) | partial | Zebra BI Charts |
| 9 | Geteiltes Crosshair über alle Charts einer Seite (market-032) | partial | Grafana Dashboard-Einstellungen (fetched) |
| 10 | Drill-Menü mit Absichten + kuratierten Drill-Feldern je Measure (market-020, -023) | partial/no | Metabase Drill-through (fetched); Omni drill_fields |

Reihenfolge: 1–2 IBCS-Kern, reine Spec-Logik; 3–7 nativ mit Galerie-Vorlage; 8–10 hoher Nutzwert, aber Host.

## Was in den Host (Fabric-App-Shell) gehört statt in die Spec

- **Signal-Bus zwischen Charts:** geteiltes Crosshair (032), Zeitbereich-Brush als Seitenfilter (025, 033).
  In einer concat-Spec nativ; über getrennt eingebettete Charts nur per `view.addSignalListener`/`view.signal`.
- **Neuabfrage bei Drill:** Drill anywhere/Drill by/Break out by (018–022). Die Spec liefert den geklickten
  Datensatz, Menü und Abfrage sind Host. Drill-Spalten gehören als Feld in den KPI-Katalog (Omni-Muster, 023).
- **Kommentarspeicher:** Erfassen/Speichern (030); die Anzeige ist ein Text-/Marker-Layer.
- **Breakpoints:** responsive Annotationen (038) und Layoutwechsel (031); VL kann nur `width: "container"`.
  Alternative: je Breakpoint eine generierte Spec-Variante.
- **Zonen ein-/ausblenden nach Klick** (017), Viz-in-Tooltip-Overlay (014), Scrollytelling-Schritte (039),
  Insight-Berechnung à la Pulse (015; Pipeline berechnet, Spec zeigt Karte + Satz).

## Erkenntnisse

- Die meisten "Beyond"-Muster sind Pointer-Semantik (nearest, nur x-Achse, Querschnitt) und keine neuen
  Chart-Typen. Vega-Lite deckt sie vollständig ab; Power BI verlangt dafür das Treffen eines Datenpunkts.
- Stärkstes IBCS-Signal: Zebra BI (Custom Visual *in* Power BI). Szenario-Schalter, Invert, Top N + Others,
  Kommentare = Lücken des Power-BI-Standards (inferred).
- Der Drill ohne Hierarchie (ThoughtSpot, Sigma, Superset, Metabase, Hex) ist marktweit Standard, aber
  ausschließlich Host plus semantisches Modell. Mit Vega-Lite allein nicht zu lösen.

## Lücken, Widersprüche, offene Fragen

- `beyond_pbi` ist ungeprüft gegen die aktuelle Power-BI-Doku (z. B. ob Rechteckauswahl auf Linien seit
  2024/25 existiert, market-025). Dieser Abgleich gehört in den Strang fabric, bevor das Feld belastet wird.
- FT: keine Interaktionsquelle gefunden. Der Visual Vocabulary ist Auswahllogik, keine Interaktion, und
  wurde deshalb nicht aufgenommen. NYT nur über Sekundärquellen (IEEE-VIS-Studie).
- Apple (WWDC21) liegt außerhalb 2024–2026, nur als Barrierefreiheits-Referenz. Zahlen aus Suchauszügen (Omni 10 Spalten, 72 Charts in der IEEE-Studie) sind nicht am Original geprüft.
- Galerie-URLs sind aus dem Beispielindex `examples.json` (fetched) plus dem URL-Muster gebildet. Die
  Galerieseite selbst war gesperrt. Für market-028 gibt es keine Galerie-Vorlage (null).
- Offen: Soll der Szenario-Schalter ein Leser-Widget in der Spec sein oder ein Seitenzustand des Hosts
  (Konsistenz über alle Charts)? Das entscheidet, ob 029 "yes" bleibt oder an den Signal-Bus wandert.

Bewusst nicht gemacht: Tableau "Ask Data" nicht erfasst, weil keine Quelle geladen wurde (Status des Features
ungeprüft). Spotter/Copilot-NL nicht als eigener Eintrag, weil Power BI Copilot Parität
hat. shadcn-Tooltip-Indikator ausgelassen, weil schon in product.yaml. Keine Commits (Vorgabe).
