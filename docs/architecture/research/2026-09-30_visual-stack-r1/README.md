# Visual-Stack R1 — Referenzkorpus aus Primärquellen (30.09.2026)

Grundlage für die Runden R2–R6 des gemeinsamen Visual-Stacks (Ledger A-31, Freelancing D-603):
Profile (Stil-/Notationsachse), neue Idiome, Auswahllogik Frage → purpose → Idiom, IBCS 1:1.
Jede Aussage trägt eine Quelle; was nur als Suchauszug vorlag, ist so markiert.

## Inhalt

| Datei | Strang | Einträge | Zugang |
|---|---|---|---|
| `ibcs.yaml` + `ibcs_summary.md` | IBCS Standards 2.0 / ISO 24896 (Regeln mit `rule_id` und `test`) | 34 | alle Suchauszüge von ibcs.com (`evidence_access: search_index`) |
| `editorial.yaml` + `editorial_summary.md` | FT Visual Vocabulary, BBC, Urban, ONS, UK Analysis Function, Observable Plot, Reuters, NYT | 56 | FT, Urban, BBC, afcharts, Plot gelesen; ONS, Datawrapper, Economist nur Suchauszug |
| `product.yaml` + `product_summary.md` | shadcn/ui, Tremor, Carbon, Fluent UI, Radix, Vercel, Apple HIG, Power BI | 51 | 49 aus Quellcode/Doku gelesen (`retrieval: fetched`), 2 Suchauszüge |
| `fabric.yaml` + `fabric_summary.md` + `fabric_matrix.md` | Machbarkeit je Idiom auf Fabric App, PBIR, HTML | 36 | Typdefinitionen fabric-visuals 4.0.0/4.1.0, flint-chart 0.5.1, vega-lite 6.4.3 (lokal gelesen) |
| `entscheidungsvorlage.yaml` | Widersprüche W-1…W-6, Lücken L-1…L-3, Kandidaten für Purposes, Idiome, Profile | — | Synthese; alle zitierten IDs existieren (geprüft per Skript) |
| `FORMAT.md` | gemeinsames Eintragsformat | — | — |

## Befunde, die R2–R6 steuern

1. **IBCS ist Rollen, keine Farben.** AC solide dunkel, PY heller solide, PL hohl umrandet, FC schraffiert; Rot/Grün nur für Abweichungen gut/schlecht; keine abgeschnittenen Achsen; Direktbeschriftung statt Legende. Hex-Werte nennt die Quelle nicht (W-1, W-3).
2. **Vielfalt über Profile, nicht über Formen.** Kandidaten: `house_default` (shadcn/Tremor), `fluent`, `editorial`, `minimal`, `ibcs`, `print_safe`. Widersprüche zwischen Quellen (Legende, Nullbasis bei Linien, Gitter) werden Profilparameter, keine globale Regel (W-5, W-6).
3. **Neue Idiome mit Steuerungsnutzen:** `variance_pin`, `multi_tier_column`, `table_variance_bars_pins` (IBCS), `range_band`, `surplus_deficit_line`, `diverging_stacked_bar` (FT/Plot), `paired_time` statt zweier Achsen (W-4).
4. **Fabric App begrenzt die Mittel:** kein Vega (Sankey und Zerlegungsbaum als eigene Komponente), Flint ignoriert `chartProperties`, `VegaVisual` verändert Specs über Flags, keine native Schraffur, Schrift nur über `configVegaLite`, Tastaturnavigation erst ab fabric-visuals 4.1.0. Schriften selbst hosten (CSP für Fabric-Hosting ist nicht dokumentiert).
5. **Kundentexte:** „folgt der IBCS-Notation“, nie „IBCS-konform/zertifiziert“ (Terms of use, `ibcs-033`).

## Grenzen

Der Egress-Proxy der Arbeitsumgebung sperrte am 30.09.2026 u. a. ibcs.com, datawrapper.de, ons.gov.uk,
ui.shadcn.com, tremor.so, carbondesignsystem.com, fluent2.microsoft.design, vega.github.io und
deneb-viz.github.io. Einträge mit Suchauszug bekommen keine Test-Autorität, bevor sie am Original
geprüft sind (L-1, L-3). Heruntergeladene Quelltexte und der Extraktionsskript liegen nicht im Repo.
