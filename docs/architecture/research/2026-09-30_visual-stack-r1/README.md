# Visual-Stack R1 — Referenzkorpus aus Primärquellen (30.09.2026)

Grundlage für die Runden R2–R6 des gemeinsamen Visual-Stacks (Ledger A-31, Freelancing D-612):
Profile (Stil-/Notationsachse), neue Idiome, Auswahllogik Frage → purpose → Idiom, IBCS 1:1.
Jede Aussage trägt eine Quelle; was nur als Suchauszug vorlag, ist so markiert.

## Inhalt

| Datei | Strang | Einträge | Zugang |
|---|---|---|---|
| `ibcs_v2.yaml` + `ibcs_abgleich.md` | IBCS Standards 2.0 aus dem Original (Mitglieder-PDF, 169 S.): alle Regeln der Ebene 2 mit `rule_id`, Seite, `test`, `testbar` | 105 + 4 Meta | Original; jedes Zitat wörtlich auf der angegebenen Seite (Skriptprüfung) |
| `ibcs.yaml` + `ibcs_summary.md` | erster Stand aus Suchauszügen, **abgelöst** durch `ibcs_v2.yaml` | 34 | Suchauszüge von ibcs.com |
| `editorial.yaml` + `editorial_summary.md` | FT Visual Vocabulary, BBC, Urban, ONS, UK Analysis Function, Observable Plot, Reuters, NYT | 56 | FT, Urban, BBC, afcharts, Plot gelesen; ONS, Datawrapper, Economist nur Suchauszug |
| `product.yaml` + `product_summary.md` | shadcn/ui, Tremor, Carbon, Fluent UI, Radix, Vercel, Apple HIG, Power BI | 51 | 49 aus Quellcode/Doku gelesen (`retrieval: fetched`), 2 Suchauszüge |
| `fabric.yaml` + `fabric_summary.md` + `fabric_matrix.md` | Machbarkeit je Idiom auf Fabric App, PBIR, HTML | 36 | Typdefinitionen fabric-visuals 4.0.0/4.1.0, flint-chart 0.5.1, vega-lite 6.4.3 (lokal gelesen) |
| `entscheidungsvorlage.yaml` | Widersprüche W-1…W-6, Lücken L-1…L-3, Kandidaten für Purposes, Idiome, Profile | — | Synthese; alle zitierten IDs existieren (geprüft per Skript) |
| `FORMAT.md` | gemeinsames Eintragsformat | — | — |

## Befunde, die R2–R6 steuern

1. **IBCS ist Rollen, keine Farben** (Original geprüft). AC solide dunkel, PY heller solide, PL/BU nur umrandet, FC umrandet und schraffiert (UN 3.2); Abweichungen gut hellgrün, schlecht dunkelrot, neutral blau, ausdrücklich ohne Farbcodes (UN 4.1); keine abgeschnittenen Achsen außer bei indexierten Daten (CH 1.1); Direktbeschriftung bevorzugt, Legende erlaubt (UN 2.3). Zahlenwerte legt das Profil fest, Tests prüfen Relationen (W-1, W-3).
2. **Vielfalt über Profile, nicht über Formen.** Kandidaten: `house_default` (shadcn/Tremor), `fluent`, `editorial`, `minimal`, `ibcs`, `print_safe`. Widersprüche zwischen Quellen (Legende, Nullbasis bei Linien, Gitter) werden Profilparameter, keine globale Regel (W-5, W-6).
3. **Neue Idiome mit Steuerungsnutzen:** `variance_pin`, `multi_tier_column`, `table_variance_bars_pins` (IBCS), `range_band`, `surplus_deficit_line`, `diverging_stacked_bar` (FT/Plot), `paired_time` statt zweier Achsen (W-4).
4. **Fabric App begrenzt die Mittel:** kein Vega (Sankey und Zerlegungsbaum als eigene Komponente), Flint ignoriert `chartProperties`, `VegaVisual` verändert Specs über Flags, keine native Schraffur, Schrift nur über `configVegaLite`, Tastaturnavigation erst ab fabric-visuals 4.1.0. Schriften selbst hosten (CSP für Fabric-Hosting ist nicht dokumentiert).
5. **Kundentexte:** „folgt der IBCS-Notation“, nie „IBCS-konform/zertifiziert“; IBCS® ist eine eingetragene Marke des IBCS Institute (Original S. ii; Terms of use `ibcs-033`). Chart-Templates C01–C13 und die Software-Zertifizierung stehen nicht im Standard selbst.

## Grenzen

Der Egress-Proxy der Arbeitsumgebung sperrte am 30.09.2026 u. a. ibcs.com, datawrapper.de, ons.gov.uk,
ui.shadcn.com, tremor.so, carbondesignsystem.com, fluent2.microsoft.design, vega.github.io und
deneb-viz.github.io. Einträge mit Suchauszug bekommen keine Test-Autorität, bevor sie am Original
geprüft sind (L-3; L-1 am 30.09.2026 mit dem Original geschlossen). Die Mitglieder-PDF ist persönlich lizenziert und liegt nicht im Repo. Heruntergeladene Quelltexte und der Extraktionsskript liegen nicht im Repo.
