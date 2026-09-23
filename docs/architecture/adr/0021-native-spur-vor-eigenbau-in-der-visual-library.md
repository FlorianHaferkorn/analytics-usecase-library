# ADR-0021 — Die native Spur hat Vorrang, und jede Lücke trägt einen Grund

| Feld | Wert |
|---|---|
| Status | **Accepted** (07.09.2026) |
| Entscheider | Florian Haferkorn |
| Kontext | Flos Vorgabe vom 07.09.2026 („Visual sowie Report Library fertigstellen") mit fünf Vorlagen, davon eine wörtlich mit „Native Sparklines" überschrieben |
| Betrifft | `tooling/visual_library/registry.json` · `core/templates/page_templates/visual_library/*.yaml` · `core/templates/page_templates/visual_library/index.yaml` · `tooling/visual_library/acceptance/validation_matrix.json` |
| Bezug | ADR-0018 (Visualtyp-Vokabular) · Meridian Charter §3.3 / D-156 (Official-First) · Meridian D-236 (Visual-Katalog als Orakel) · Meridian D-346 (eine Lücke ist eine Behauptung mit Datum) |

## 1. Kontext

Die Visual Library führt 30 Idiome. **13 davon tragen keine `powerbi_native`-Spur**
(gemessen 07.09.2026 an `tooling/visual_library/registry.json`, Feld `tools`): `boxplot`,
`bullet`, `dumbbell`, `histogram`, `kpi_card_bullet`, `kpi_card_spark`, `kpi_card_sparkbar`,
`lollipop`, `matrix_bullet`, `matrix_delta_pill`, `matrix_sparkline`, `sankey`,
`small_multiples`.

Für zwei davon ist das nachweislich falsch. Gemessen am selben Tag gegen den offiziellen
Katalog `@microsoft/powerbi-core-visual-schema` (gepinnt 0.1.1, gelesen über
`core.pbi_engine.oracle.visual_catalog`, `catalog_available() == True`, 59 Visual-Typen):

| Idiom | Registry sagt | Katalog sagt |
|---|---|---|
| `matrix_sparkline` | `tools: [powerbi_svg_dax]`, `native_visual_type: null` | `visual_objects("tableEx")` enthält **`sparklines`**; `pivotTable` ebenso |
| `small_multiples` | `tools: [deneb_vegalite]`, `native_visual_type: null` | **14** Typen tragen **`smallMultiplesLayout`**: `areaChart`, `barChart`, `cardVisual`, `clusteredBarChart`, `clusteredColumnChart`, `columnChart`, `hundredPercentStackedAreaChart`, `hundredPercentStackedBarChart`, `hundredPercentStackedColumnChart`, `lineChart`, `lineClusteredColumnComboChart`, `lineStackedColumnComboChart`, `ribbonChart`, `stackedAreaChart` |

Wir bauen also mit SVG-in-DAX und Deneb nach, was die Plattform selbst kann. Das ist der
Official-First-Verstoß, den Meridians Charter §3.3 benennt: Eigenbau nur, wenn das eigene
Produkt **in allem** besser ist und eine Erweiterung nicht möglich ist. Für diese beiden ist
weder das eine noch das andere geprüft worden.

**Der schärfere Teil des Befundes: das Wissen lag im Repo und wurde nicht benutzt.** Beide
nativen Projektionen sind in den eigenen Referenzen beschrieben, seit sie dort stehen:

- `products/fabric/powerbi/docs/references/pbir-rename-cascade.md:281-306` — das Format des
  Sparkline-Metadaten-Selektors,
  `SparklineData(<MeasureTable>.<MeasureName>_[<GroupingTable>.<Hierarchy>.<Level>])`.
- `products/fabric/powerbi/docs/references/pbir-visual-json.md:347-351` — „Enable small
  multiples by adding a `SmallMultiples` query projection".

Das ist keine Wissenslücke, sondern eine ungenutzte Referenz. Dieselbe Klasse wie ein Tor, das
jemand von Hand aufrufen muss: vorhanden, korrekt, und im Ablauf nicht verdrahtet.

## 2. Entscheidung

**1. Wo der offizielle Katalog die Fähigkeit trägt, ist die native Spur die Erstwahl.**
Ein Idiom bekommt `powerbi_native` in `tools` und einen `native_visual_type`, sobald der
Katalog das tragende Visual-Objekt führt. Die vorhandene SVG- oder Deneb-Spur wird **nicht**
abgebaut — sie verliert den Rang der Erstwahl und bleibt für die Fälle, die nativ nicht
gehen.

**2. Jedes Idiom ohne native Spur trägt einen Grund mit Datum.**
Ein leeres `native_visual_type` ist keine Aussage. Nach D-346 ist eine Lücke eine Behauptung,
und eine Behauptung braucht Methode und Datum. Das Idiom-YAML bekommt dafür ein Feld, das
sagt: gegen welchen Katalogstand geprüft, mit welchem Ergebnis.

**3. Der Katalog ist das Orakel, nicht die Erinnerung.**
Die Prüfung läuft gegen `visual_catalog.visual_objects(<typ>)` beim gepinnten Stand, nicht
gegen das, was jemand über Power BI weiß. Pins steigen nur nach Re-Validierung (D-236); ein
Bump kann eine bisher begründete Lücke schließen und wird dann hier nachgetragen.

## 3. Was das kostet, benannt statt geglättet

Die native Spur ist **die einzige, die sich nicht headless beweisen lässt**.
`tooling/visual_library/acceptance/CHECKLIST.md` sagt das selbst: Deneb rendert über
vl-convert, SVG-DAX über `svg_to_png`, Recharts über einen echten React-Lauf — PBIR ist eine
Visual-*Konfiguration*, und einen Renderer dafür gibt es nicht. Wer native Spuren hinzufügt,
vergrößert genau den Teil der Bibliothek, für den kein Bild entsteht.

Das ist der Preis und keine Nebenbemerkung. Der Ersatz ist die Offline-Ladeprobe aus
`.claude/rules/connect-pbid.md`: TMDL→TOM über
`TmdlSerializer.DeserializeDatabaseFromFolder`, danach Tabellen und Measures aufzählen und
prüfen, dass jede Referenz auflöst. Das fängt die spaltenlose Klasse ohne laufende Engine.
Es ersetzt kein Bild und wird auch nicht so geführt.

Zweiter Preis, kleiner: `powerbi_native` bindet an eine Fassung von Power BI Desktop. Eine
SVG-Spur ist davon unabhängig. Wo ein Kunde eine ältere Fassung fährt, bleibt die
Fallback-Spur der unterstützte Weg — die Kundenseiten-Grenze aus Official-First gilt
unverändert.

## 4. Abgrenzung

- **ADR-0018 bleibt gültig und meint etwas anderes.** Dort geht es um
  `visual_registry.yaml` — das Vokabular der Slot-Typen. Hier geht es um
  `tooling/visual_library/registry.json`, die Idiom-Bibliothek mit ihren Werkzeugspuren. Zwei
  Register, zwei Zwecke; dieses ADR fasst das Vokabular nicht an.
- **Kein Idiom wird gelöscht.** Auch keines, dessen SVG-Spur nach diesem ADR zweite Wahl ist.
- **Die Entscheidung gilt der Bibliothek, nicht den Kundenlaufzeiten.** Was ein Kunde
  installieren muss, ändert sich durch dieses ADR nicht: die Deliverables bleiben
  PBIR/TMDL-Dateien.

## 5. Verifikation

| Prüfung | Erwartung |
|---|---|
| `visual_catalog.visual_objects("tableEx")` enthält `sparklines` | ja (gemessen 07.09.2026, Pin 0.1.1) |
| Typen mit `smallMultiplesLayout` | 14 (gemessen 07.09.2026, Pin 0.1.1) |
| Idiome mit `powerbi_native` nach V-1/V-2/V-3 | 17 → **20** von 30 (gemessen 08.09.2026 an den YAMLs) |
| Idiome ohne native Spur, deren Grund Datum **und** Methode nennt | 10 von 10 (Test `test_every_missing_native_track_carries_a_dated_measurement`) |
| Native Goldens, deren Typ/Rollen/Objekte der Katalog kennt | 20 von 20 (Test `test_native_goldens_only_name_things_the_official_catalog_knows`; vor der Korrektur 16 von 20) |
| Idiome ohne native Spur **und** ohne Grund | 0 |
| `python scripts/check_index.py --strict` | 0 harte Befunde |
| Golden je Spur je Idiom | vollständig; `validation_matrix.json` trägt den Stand |
| `pytest tooling/visual_library/tests/` | 80 passed, **0 skipped** (08.09.2026; vorher 66 passed / 13 skipped, weil `vl-convert-python` und `altair` in keinem Workflow installiert waren) |

## 6. Nachtrag 08.09.2026 — die Regel hat vier eigene Fehler gefunden

Beim Prüfen der KPI-Karten gegen den Katalog fiel auf, dass **vier der zwanzig nativen
Goldens Namen trugen, die es nicht gibt**: `stackedColumnChart` ist kein Visualtyp (das
gestapelte Säulendiagramm heißt `columnChart`), `scatterChart` kennt keine Rolle `Details`
(sondern `Category`), der Zerlegungsbaum heißt seine Rollen `Analyze`/`ExplainBy`, und
`sortDefinition` stand in drei Idiomen **innerhalb** von `queryState`, wo es als fünfte
Datenrolle liest — in PBIR ist es ein Geschwister davon unter `query`, so auch in jedem
ausgelieferten Report des Repos.

Alle vier sind behoben. Interessanter als die Fehler ist, warum sie so lange standen: der
vorhandene Test `test_native_goldens_have_pbir_structure` zählt Projektionen und liest keine
Namen — das falsch platzierte `sortDefinition` half ihm sogar durch, weil es ein Dict ohne
`projections` ist. Und Power BI ignoriert Unbekanntes still, es gibt also keine Meldung, an
der es auffiele. Ein Strukturtest, der Formen zählt statt Namen zu prüfen, misst die Syntax
und nicht die Sprache.

Der Regress-Schutz ist ein **eingefrorener Katalogauszug** statt eines Imports:
`tooling/visual_library/catalog_facts.json` (12 Visualtypen, deren Rollen und die
Eigenschaftsnamen der benutzten Formatierungsobjekte) plus `catalog_facts.py` mit
`check`/`write` und dem Drei-Wege-Vokabular 0/1/2 (deckungsgleich / Drift / konnte nicht
vergleichen). Grund für den Auszug: der Katalog liegt als npm-Paket in Meridian, ALUCAs CI
hat ihn nicht — ein importierender Test wäre hier ein Dauer-Soft-Skip und könnte „nichts
gefunden" nicht von „nicht gelaufen" unterscheiden.

## 7. Offene Punkte

- ~~**Ob `cardVisual` mit `smallMultiplesLayout` für die KPI-Karten aus Bild 1 taugt.**~~
  **Beantwortet 08.09.2026, anders als vermutet.** Der Träger der Karten-Anatomie ist nicht
  `cardVisual`, sondern das `kpi`-Visual: es führt die Rollen `Indicator`/`TrendLine`/`Goal`
  und die Objekte `trendline`, `indicator`, `goals`, `status`, `lastDate`. `cardVisual` hat
  33 Objekte und **kein** `sparklines` — der alte Grund war insoweit richtig und beantwortete
  nur die falsche Frage. Neun der elf Slots aus Bild 1 sind damit belegt; die Abbildung steht
  als Kopfkommentar in `kpi_card_spark.yaml`. Handlungsaufruf und Aktualisierungszeitpunkt
  sind bewusst **keine** Kartenslots: das eine ist ein Navigations-Steuerelement, das andere
  gilt dem Modell und stünde sonst sechsmal auf einer Seite.
- ~~**Die übrigen 11 Idiome**~~ **erledigt (V-4).** Zehn Idiome bleiben ohne native Spur, jedes
  mit Datum und Methode im Grund; ein Test hält das. Die beiden neu entschiedenen:
  `kpi_card_bullet` fällt, weil kein Kartentyp die Erreichung als **Länge** zeichnet
  (`goals` und `referenceLabel*` zeigen den Zielwert als Zahl) — eine native Spur hätte den
  Rang-2-Kanal weggelassen. `kpi_card_sparkbar` fällt, weil `kpi.trendline` genau `show` und
  `transparency` führt: die native Trendspur ist eine Linie und lässt sich nicht in Säulen
  umschalten, und genau die Linie verbietet dieses Idiom unter
  `line_when_periods_are_discrete`.
- **Ob eine native Spur eine SVG-Spur je ablöst.** Heute nicht entschieden und heute auch
  nicht nötig: beide stehen nebeneinander, die Rangfolge genügt.
