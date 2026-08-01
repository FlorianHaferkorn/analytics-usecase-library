# PBIR-CLI 0.1.4 — Triage der 694 Befunde

**Stand:** 01.08.2026 · **Anlass:** D-157-Re-Validierung vor einer Pin-Anhebung
0.1.1 → 0.1.4 · **Ergebnis der Re-Validierung: nicht bestanden** (694 Fehler über
17 Reports). Dieses Dokument trennt echte Defekte von zusätzlicher Strenge, damit
die Anhebung eine Arbeitsliste hat statt einer Zahl.

## Erste Reduktion: 694 Vorkommen sind 46 Befunde

Alle 17 Reports tragen dieselbe generierte Theme-Datei. Dedupliziert man nach
(Diagnose, Pfad, Visualtyp), bleiben **46 verschiedene Befunde**. Die 694 ist eine
Multiplikation, kein Umfang.

| Diagnose | Vorkommen | verschieden |
|---|---:|---:|
| `PBIR_THEME_VISUAL_PROP_UNKNOWN` | 527 | 31 |
| `PBIR_FORMATTING_OBJECT_UNKNOWN` | 104 | 7 |
| `PBIR_THEME_VISUAL_PROP_ENUM_INVALID` | 34 | 2 |
| `PBIR_PLATFORM_MISSING` | 17 | 1 |
| `PBIR_ROLE_MAX_EXCEEDED` | 11 | 4 |
| `PBIR_FORMATTING_PROP_UNKNOWN` | 1 | 1 |

## Methode — warum das Urteil nicht vom Prüfer selbst stammt

Den Prüfer zu fragen, ob er recht hat, ist zirkulär. Zwei unabhängige Referenzen:

1. **Naher Treffer im offiziellen Katalog** (`powerbi-report-author formatting
   describe-object`, D-236). Existiert auf demselben Objekt ein Property mit fast
   gleichem Namen, ist der Befund ein Schreibfehler — kein Zuständigkeitsstreit.
2. **Microsofts eigenes JSON-Schema**, im Repo unter
   `tooling/schemas/pbir/fetch_cache/` gecacht
   (`.../report/definition/visualConfiguration/2.3.0/schema.embedded.json`).
   Es enthält `spaceBelowSubTitle`, `shadowBlur`, `fontFamily` — und **nicht**
   `spaceBelowSubtitle`, `blur`, `fontFace`. Damit entscheidet Microsoft, nicht die CLI.

Für Objekte, die unter `*` fehlen, wurde zusätzlich geprüft, ob sie auf einem
konkreten Visualtyp existieren (`barChart`, `lineChart`, `tableEx`, `pivotTable`).

## A — Echte Defekte: falsch geschriebener Name (≈15) — **ERLEDIGT**

> **Umgesetzt am 01.08.2026.** 35 Theme-Dateien, 525 Einzeländerungen, ausschließlich
> innerhalb von `visualStyles`. Gemessen: **694 → 439 Fehler**; die Diagnose
> `PBIR_THEME_VISUAL_PROP_ENUM_INVALID` ist vollständig verschwunden. Testsuite
> 1343 passed. Was übrig bleibt, ist Gruppe B und C — die Zahl fällt hier nicht
> weiter, ohne dass eine Entscheidung fällt.
>
> Zwei Fälle waren **keine** Umbenennungen und wurden nicht dazu gebogen:
> `backgroundShow: false` ist ein Bool ohne Gegenstück (`title.background` ist ein
> Fill) — entfernt, `false` war ohnehin der Default. `dropShadow.Options: "Custom"`
> ist unter keiner Schreibweise ein Property und ein Zwilling von `position` —
> entfernt; `position` steht jetzt auf `"Outer"`, wie es das Repo in seinem eigenen
> `shadowCustom` bereits tut.
>
> **Nicht angefasst:** `textClasses.*.fontFace` (4×). Das ist die Alt-Theme-Vokabel
> und dort korrekt — Microsofts eigene Basis-Themes (`CY25SU10`,
> `Base_Theme_Template_V1`) schreiben es genauso. Nur unter `visualStyles` ist
> `fontFace` falsch. Ein globales Suchen-und-Ersetzen hätte diese vier mitgerissen.


Von Microsofts Schema bzw. dem Katalog belegt. Der Fix ist eine Umbenennung.

| im Theme | korrekt | Beleg |
|---|---|---|
| `title.fontFace`, `subTitle.fontFace` | `fontFamily` | MS-Schema |
| `legend.fontFace`, `valueAxis.fontFace`, `categoryAxis.fontFace` | `fontFamily` | Katalog (auf `barChart`) |
| `spacing.spaceBelowSubtitle` | `spaceBelowSubTitle` | MS-Schema (Groß-T) |
| `dropShadow.blur` | `shadowBlur` | MS-Schema |
| `dropShadow.distance` | `shadowDistance` | Katalog (`dropShadow`-VCO) |
| `border.weight` (advancedSlicerVisual, pageNavigator) | `border.width` | Katalog (`border`-VCO: color/radius/show/width) |
| `title.backgroundShow` | `background` | Katalog |
| `subTitle.backgroundShow` | `show` | Katalog |
| `dropShadow.Options` | — kein Property (Groß-O) | Katalog |

**Enum-Werte** (Power-BI-Theme-JSON ist hier case-sensitiv):

| im Theme | zulässig |
|---|---|
| `lineStyles.markerShape: "Circle"` | `circle` (u. a.) |
| `dropShadow.position: "Custom"` | `Outer`, `Inner` |

## B — Echte Defekte, aber anderer Fixpfad (8)

| Befund | Sachlage |
|---|---|
| `PBIR_PLATFORM_MISSING` ×17 | Der Emitter schreibt `.platform` seit PR #416. Die eingecheckten `dist/`-Reports wurden seither nicht neu erzeugt. Fix = Regenerierung, nicht Code. |
| `PBIR_ROLE_MAX_EXCEEDED`: `waterfallChart` Rolle `Y` mit 2–5 Projektionen, max 1 | Echter Modellierungsfehler. **Gleiche Wurzel wie der Scorecard-Knock-out `mixed-scale` auf `Main_3`**: mehrere Measures unterschiedlicher Skalenfamilie auf einer Achse. Zwei Prüfer, ein Defekt. |
| `calloutValue` auf `cardVisual`, `dataLabels` auf `clusteredBarChart` | Formatierungsobjekt am falschen Visualtyp — vor einem Fix je Visual zu prüfen. |
| `text.text` auf `textbox` | Property-Struktur der Textbox; einzeln zu prüfen. |

## C — Zusätzliche Strenge, kein Defekt dieses Repos (≈15)

Chart-Objekte, die das Theme global unter `visualStyles.*.*` setzt: `legend`,
`valueAxis`, `categoryAxis`, `lineStyles`, `smallMultiplesLayout`, `columnHeaders`,
`rowHeaders` — dazu die Alt-Objekte `outspace` und `header` (auf `shape`,
`actionButton`, `pageNavigator`, `bookmarkNavigator`).

Gemessen: diese Objekte **existieren** auf konkreten Visualtypen (`legend` auf
`barChart`, `columnHeaders` auf `tableEx`, `rowHeaders` auf `pivotTable`,
`lineStyles` auf `lineChart`) — nur nicht unter dem Platzhalter `*`. 0.1.4 prüft `*`
allein gegen die geteilten Visual-Container-Objekte. Der globale Selektor ist
dokumentierte Power-BI-Theme-Praxis; hier irrt der Prüfer bzw. sein Katalog ist für
diesen Fall unvollständig.

**Achtung, Teilmenge:** Innerhalb dieser Gruppe sind die *Property-Namen* teils
trotzdem falsch (`legend.fontFace` → `fontFamily`). Der Objektbefund ist Strenge,
der Property-Befund darunter ein echter Defekt. Beides steht deshalb in A und C.

Nicht in C, sondern offen: `legend.alignment` und `smallMultiplesLayout.spacing`
existieren **auch auf dem konkreten Visualtyp nicht**. Das sind Kandidaten für A,
aber ohne nahen Treffer — Einzelfallprüfung nötig.

## Was das für die Pin-Anhebung heißt

Der Weg zu 0.1.4 ist nicht „694 Fehler beheben", sondern:

1. **A abarbeiten** — rund 15 Umbenennungen im Theme-Erzeuger. Mechanisch, belegt.
2. **B klären** — `.platform` kommt mit der `dist/`-Regenerierung; der
   `waterfallChart`-Y-Befund ist dieselbe Arbeit wie der Scorecard-Knock-out.
3. **C entscheiden** — bleibt rot, solange 0.1.4 den `*`-Selektor so prüft. Entweder
   das Theme verzichtet auf globale Chart-Objekte (Wirkungsverlust), oder diese
   Diagnosen werden für `check-pbir-strict` unterdrückt, oder die Anhebung wartet auf
   eine CLI-Fassung, die `*` korrekt auflöst. **Das ist eine Entscheidung, keine
   Aufgabe** — und der eigentliche Grund, warum der Pin heute nicht steigt.

Bis dahin: Pin bleibt 0.1.1, und die Installation in `superversion.yml` ist daran
gebunden (vorher ungepinnt — genau daraus entstand der Ausfall).

## Nachtrag 01.08.2026 — Gruppe B abgearbeitet, soweit sie ableitbar war

**Erledigt:**

* `.platform` für alle 17 Reports ergänzt (Form aus `targets/pbir.py`, Null-`logicalId`).
* Evidenz-Sortierung gesetzt: `knockout-unsorted-evidence` **16 → 2**. Keine
  Design-Entscheidung nötig — alle 21 Brackets deklarieren `component_300s.sort_by`
  bereits governt; die `dist/`-Reports waren nur nie danach neu erzeugt.

**Nicht erledigt, und zwar aus einem inhaltlichen Grund — `knockout-mixed-scale` (10).**

`Main_3` trägt in den betroffenen Reports die ganze KPI-Bande (4 Measures, gemischte
Skalenfamilien) statt eines Measures. COM-002 — der migrierte Referenz-Report
(`intent_rules_version: 2`) — trägt dort **genau eines**, passend zu seinem
deklarierten `component_30s[2]`, und besteht den Check. Der Unterschied ist also
nicht Zufall, sondern der Migrationsstand.

Gemessen, wie weit sich das ableiten lässt:

| | Anzahl | ableitbar? |
|---|---:|---|
| Bracket deklariert `component_30s[2]` | 2 | nur formal — das deklarierte Measure ist im Visual gar nicht vorhanden, ein Fix wäre Hinzufügen + Entfernen, kein Korrigieren |
| Bracket deklariert nichts für `Main_3` | 12 | **nein** |

Für zwölf Use Cases gibt es **keine governte Vorgabe**, welche Measures auf diese
Achse gehören. Sie zu wählen hieße, Report-Inhalt zu erfinden — genau das, was der
Golden Thread untersagt. Das ist die R2.4-Kuratierung je Use Case, die das Repo
bereits als Aufgabe führt; COM-002 ist die Vorlage.

**Konsequenz:** `knockout-mixed-scale` bleibt rot, bis die zwölf Brackets ihr
`component_30s` für `Main_3` deklariert haben. Das ist Fachentscheidung pro Use Case,
keine Generator-Arbeit.

Ebenfalls offen, aus demselben Grund benannt statt geraten: `OPS-001` sortiert laut
Bracket nach einem Measure, das seine Evidenztabelle nicht projiziert; `XD-004`
deklariert `sort_by.measure: impact_value`, was keine KPI-ID ist.
