---
last-reviewed: 2026-11-12
status: gemessen
---
# Semantikmodell-BPA: offizieller Satz gepinnt, eigene Lückenregeln laufen in Stage 1

Branch `runde/2026-11-12-bpa-offiziell`, Basis `origin/main` @ 59111e11. Auftrag von Florian vom 12.11.2026, Grundlage ist die BPA-Analyse vom selben Tag (Inventar C13).

## Ergebnis

| | vorher | nachher |
|---|---|---|
| Offizieller Regelsatz (microsoft/Analysis-Services `BPARules.json`) | Kopie mit 58 von 71 Regeln (`bpa-rules-semanticmodel.json`, Stand 12.10.2025), ausgewertet wurden davon 3 per Regex | gepinnt, nicht kopiert: `tooling/linters/powerbi/bpa-official.pin.json` (Commit `d3ccb503…`, Raw-URL, sha256, 71 Regel-IDs), Lauf mit Tabular Editor 2.28.0 in `.github/workflows/tabular-bpa.yml` (Windows) |
| Eigene Regeln | 14 DAX-Regeln in `bpa-rules-dax.json` (eigenes Format), 5 eigene Regeln in der Kopie | 16 Regeln in `tooling/linters/powerbi/aluca-bpa-rules.json`, Tabular-Editor-Format, blankes Array |
| Lauf der eigenen Regeln auf Linux | `check_dax_best_practices.ps1` (nur `_Measures.tmdl`, nur DAX) | `tooling/validation/check_bpa.py` in Stage 1 mit `--strict`, alle Objekttypen, alle fünf dist-Modelle |
| Tabular Editor in ALUCA | lief nirgends | Workflow angelegt, noch nicht gelaufen (Entwurfs-PR) |
| Drift des Pins | nicht geprüft (`check_upstream_sources.py` zeigte auf `TabularEditor/BestPracticeRules`) | `check_upstream_sources.py`, neue Art `github_file`: Branch-Kopf per `git ls-remote`, Datei-Hash am Pin und am Kopf |

## Pin des offiziellen Satzes

Gemessen 12.11.2026 auf zwei Wegen: `git ls-remote https://github.com/microsoft/Analysis-Services master` ergibt `d3ccb5032c9029b097276b88412f7b61df6e73b8` und ist damit gleich dem Pin. `BPARules.json` über die Raw-URL am Pin geladen hat sha256 `ddb9cff4…0392` und 71 Regeln. Das ist derselbe Wert, den Freelancing am 30.09.2026 gemessen hat (`research/upstream_pins.yaml`, `bpa-rules-analysis-services`). Das Commit-Datum ist nicht gemessen, weil die GitHub-API für dieses Repo in der Sitzung 403 lieferte.

Der Peer-Test `tooling/tests/test_check_bpa.py::test_windows_workflow_uses_the_pin_and_the_custom_rules` hält Workflow-`env` und Pin-Datei gleich. Der Workflow prüft den Hash mit `sha256sum -c`, bevor Tabular Editor läuft.

## Regeltabelle

Abgleich nach Regel-ID gegen die 71 IDs am Pin. Kein eigener Regelname kollidiert, das prüft `test_custom_ids_do_not_collide_with_pinned_official_set`. Inhaltlich ist je Regel geprüft, ob eine offizielle Regel denselben Verstoß meldet.

### Alte Regeln, die der offizielle Satz abdeckt (nicht übernommen)

| alte Regel | offizielle ID |
|---|---|
| `dax.divide.preferred`, `DAX_USE_DIVIDE` | `USE_THE_DIVIDE_FUNCTION_FOR_DIVISION` |
| IFERROR-Teil von `dax.errorfunctions.avoid` | `AVOID_USING_THE_IFERROR_FUNCTION` |
| `dax.calculate.preferred` | `FILTER_COLUMN_VALUES`, `FILTER_MEASURE_VALUES_BY_COLUMNS` (entscheidbarer Teil; der Rest ist ein Hinweis ohne prüfbare Bedingung) |
| `DAX_FORMATSTRING_REQUIRED`, TMDL-004 | `PROVIDE_FORMAT_STRING_FOR_MEASURES` |
| `META_SUMMARIZE_NONE` | `NUMERIC_COLUMN_SUMMARIZE_BY` |
| TMDL-006 (`///` je Measure) | `OBJECTS_WITH_NO_DESCRIPTION` |
| TMDL-007 | `REDUCE_NUMBER_OF_CALCULATED_COLUMNS` |
| TMDL-008 | `SNOWFLAKE_SCHEMA_ARCHITECTURE` |
| TMDL-009 | `AVOID_EXCESSIVE_BI-DIRECTIONAL_OR_MANY-TO-MANY_RELATIONSHIPS`, `MANY-TO-MANY_RELATIONSHIPS_SHOULD_BE_SINGLE-DIRECTION` |
| übrige 58 Regeln der Kopie | dieselben IDs am Pin |

TMDL-001 (Tabs) und TMDL-002 (`description:`) sind Syntax, kein BPA-Thema. Sie bleiben in `check_tmdl_syntax.ps1` und `bpa-rules-tmdl.json`.

### Eigene Regeln (`aluca-bpa-rules.json`)

| Regel | Severity | Herkunft | offiziell abgedeckt |
|---|---|---|---|
| `ALUCA_DAX_VAR_RETURN` | 2 | `dax.var_return.required` | nein |
| `ALUCA_DAX_FORMAT_IN_MEASURE` | 3 | `dax.format.forbidden` | nein |
| `ALUCA_DAX_REMOVEFILTERS` | 2 | `dax.removefilters.preferred` | nein |
| `ALUCA_DAX_IF_NESTING` | 2 | `dax.ifnesting.avoid` | nein |
| `ALUCA_DAX_BLANK_DENSIFICATION` | 1 | `dax.blank.handling` | nein |
| `ALUCA_DAX_TIME_INTELLIGENCE_NATIVE` | 1 | `dax.timeintelligence.native` | nein |
| `ALUCA_DAX_ISINSCOPE` | 1 | `dax.isinscope.totals` | nein |
| `ALUCA_DAX_ITERATOR_SINGLE_COLUMN` | 2 | `dax.iterators.only_when_needed` | nein |
| `ALUCA_DAX_SHORTENED_CALCULATE` | 2 | `dax.calculate.shortened.forbidden` | nein |
| `ALUCA_DAX_EARLIER` | 2 | `dax.earlier.prefer_var` | nein |
| `ALUCA_DAX_DIVIDE_ALTERNATE_ZERO` | 2 | `dax.divide.avoid_alternate_zero` | nein. `USE_THE_DIVIDE_FUNCTION_FOR_DIVISION` prüft nur `/` |
| `ALUCA_DAX_ISERROR` | 2 | ISERROR-Teil von `dax.errorfunctions.avoid` | nein. `AVOID_USING_THE_IFERROR_FUNCTION` prüft nur IFERROR |
| `ALUCA_DAX_LY_TIME_INTELLIGENCE` | 1 | `DAX_TIME_INTELLIGENCE_LY` | nein |
| `ALUCA_MEASURE_DISPLAY_FOLDER` | 1 | TMDL-005, `DAX_DISPLAYFOLDER_SUGGESTED` | nein |
| `ALUCA_M_TABLE_LITERAL_NEEDS_LET` | 3 | TMDL-003 | nein. `MINIMIZE_POWER_QUERY_TRANSFORMATIONS` prüft Transformationen, nicht die Form |
| `ALUCA_LINEAGE_TAG` | 1 | TMDL-010 | nein |

Gezählt sind das 16 eigene Regeln und 71 gepinnte offizielle Regeln.

Drei Regeln haben eine andere Bedingung als ihre Vorlage:

- `dax.timeintelligence.native` und `dax.isinscope.totals` hatten in `bpa-rules-dax.json` nur ein `suggest` und keine Bedingung. `check_dax_best_practices.ps1` überspringt solche Regeln, also haben sie nie gemeldet. Die neue Fassung legt den Verstoß fest. Bei der ersten Regel ist das ein von Hand verschobenes Jahr (`DATE(YEAR(..)-1, ..)`, `EDATE(.., -12)`) ohne native Zeitfunktion. Bei der zweiten ist es HASONEVALUE oder HASONEFILTER ohne ISINSCOPE.
- `dax.iterators.only_when_needed` meldete jeden Iterator in einem Ausdruck ohne `VAR`. Die neue Regel meldet nur Iteratoren, deren Ausdruck eine bloße Spaltenreferenz ist, also `SUMX(T, T[c])`. Das ist der Fall, in dem SUM nachweislich reicht.
- `DAX_TIME_INTELLIGENCE_LY` nutzte die Eigenschaft `DaxExpression`, die Tabular Editor nicht kennt. Neu ist es `Expression`.

Jede eigene Regel hat ein Fixture-Paar unter `tooling/tests/fixtures/bpa_custom/<ID>/`. `verstoesst` muss melden, `besteht` darf nicht melden. Der Test prüft zusätzlich, dass das bestehende Modell Objekte im Geltungsbereich der Regel hat. Ein leerer Treffer zählt also nicht als bestanden. Das sind 32 Testfälle, alle grün.

## Lauf auf Linux: `check_bpa.py`

- Liest die Regeldatei, die auch Tabular Editor lädt, und keine zweite Fassung. Ein kleiner Interpreter wertet genau die Ausdrucksformen aus, die die eigenen Regeln nutzen: `RegEx.IsMatch`, `string.IsNullOrWhitespace`, `.EndsWith`, `.StartsWith`, `.Contains`, `.ToString()`, Vergleiche, `and`, `or`, `not` und Klammern. Eine Regel mit anderer Form wird nicht geraten. Sie wird als `nur_windows` gezählt und ausgewiesen. Das gilt auch für Muster mit einem Inline-Flag mitten im Muster, die .NET erlaubt und Python nicht. Heute sind 16 von 16 Regeln in Python auswertbar.
- Das Modell liest der vendorte Meridian-TMDL-Parser (`_meridian_vendor.load_tmdl_parser()`, sha256-geprüft). Es gibt keinen zweiten Parser. Nur `lineageTag` liest ein Zeilen-Scan nach, weil der Parser ihn nicht führt.
- Exit 0 heißt gelaufen. Die Ausgabe nennt die Zahl der Modelle, die Objekte je Typ und die Befunde je Regel. Exit 1 gibt es mit `--strict` bei einem Befund mit Severity 3. Exit 2 heißt nicht gelaufen. Das ist der Fall, wenn keine Modelle da sind, die Regeldatei unlesbar ist, eine Regel nicht auswertbar ist oder der Parser Objekte verloren hat. Den letzten Fall prüft die Parse-Parität: Tabellen, Spalten und Measures werden roh gezählt und mit den gelesenen verglichen.

## Befunde auf den dist-Modellen

**Methode vorher:** Die beiden alten Läufer liefen mit `pwsh` 7.4.6 auf `origin/main` @ 59111e11, bevor etwas gelöscht wurde. Das war `tooling/validation/validate_semanticmodel.ps1 -TmdlPath <Modell>/definition` je Modell und `products/fabric/powerbi/tooling/validation/check_dax_best_practices.ps1` auf `products/fabric/powerbi/dist`. Tabular Editor lief in ALUCA nicht. Für den offiziellen Satz gibt es deshalb keinen Vorher-Wert.

| Läufer (vorher) | Modelle | Befunde |
|---|---:|---|
| `validate_semanticmodel.ps1` | 5 | 5 Info, je Modell `ENSURE_TABLES_HAVE_RELATIONSHIPS` mit 23, 14, 25, 16 und 17 Tabellen. Das sind alle 95 Tabellen, obwohl die Modelle 112 `relationship`-Deklarationen haben (`grep '^relationship '`: 28, 11, 33, 15, 25). Der Läufer liest den Ordner `relationships/` nicht, alle Befunde sind falsch-positiv. |
| `check_dax_best_practices.ps1` (CI) | 5 | 228 Zeilen, 0 error: `calculate.preferred` 69, `removefilters.preferred` 58, `ifnesting.avoid` 50, `var_return.required` 26, `iterators.only_when_needed` 25 |

**Methode nachher:** `python tooling/validation/check_bpa.py --strict --json …` auf dem Kopf des Branches. Er lief mit Exit 0 über 5 Modelle mit 95 Tabellen, 95 Partitionen, 562 Datenspalten und 291 Measures. Die Parse-Parität ist für alle 5 Modelle gleich.

| Regel | Befunde |
|---|---:|
| `ALUCA_LINEAGE_TAG` | 605 (370 Spalten, 225 Measures, 10 Tabellen) |
| `ALUCA_DAX_VAR_RETURN` | 66 |
| `ALUCA_DAX_IF_NESTING` | 50 |
| `ALUCA_DAX_REMOVEFILTERS` | 44 |
| `ALUCA_DAX_ITERATOR_SINGLE_COLUMN` | 13 |
| übrige 11 Regeln | 0 |
| **gesamt** | **778** (error 0, warning 173, info 605) |

**Gegenprobe gegen den alten DAX-Läufer** (Measure-Namen verglichen):

- `IF_NESTING` meldet dieselben 50 Namen wie vorher.
- `VAR_RETURN` meldet 50 Namen statt 23, alle 23 alten sind dabei. Der alte Läufer suchte `CALCULATE(` ohne Leerzeichen, der Generator schreibt aber `CALCULATE (`.
- `REMOVEFILTERS` meldet 44 statt 58 Befunde. Die 14 fehlenden sind `Action_*_Text`-Measures, die `VALUES (` enthalten. Die Ausnahme der Regel griff vorher wegen desselben Leerzeichenfehlers nicht.
- `ITERATOR_SINGLE_COLUMN` hat 13 Befunde, die einzeln geprüft sind, z. B. `SUMX ( fact_ops_failures, fact_ops_failures[Downtime Minutes] )` in `Unplanned Downtime %`.

Der Leerzeichenfehler ist als neue Fehlerklasse in `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` (Abschnitt DAX) eingetragen.

**Offizieller Satz auf den dist-Modellen:** nicht gemessen. Er läuft nur in `tabular-bpa.yml`, und der Entwurfs-PR startet keine CI.

## Entfernte Dateien

| Datei | Grund | Aufrufer umgestellt |
|---|---|---|
| `tooling/linters/run_bpa.ps1` | fest auf `COM-001.SemanticModel`, das es in `dist/` nicht gibt | Doku: `docs/agent/rules/tmdl-dax.md`, `products/fabric/powerbi/tooling/TMDL_Testing_Guide.md` |
| `tooling/linters/lint_dax.ps1` | Standard-Regelpfad existiert nicht, der Lauf endet mit Exit 0 | `tooling/README.md` |
| `tooling/linters/lint_encoding.ps1` | kein Aufrufer. Mojibake prüft `check_mojibake.ps1`, die ASCII-Regel wird nirgends verlangt | `tooling/README.md` |
| `tooling/validation/validate_semanticmodel.ps1` | 3 Regex-Regeln, alle offiziell vorhanden, alle Befunde falsch-positiv (s. o.) | `tooling/run_all_checks.ps1` (19d jetzt Verweis), `tooling/validation/README.md`, `products/open_source_stack/ARCHITECTURE.md` |
| `tooling/linters/powerbi/bpa-rules-semanticmodel.json` | veraltete Kopie, ersetzt durch den Pin | `tooling/quality/check_upstream_sources.py`, `tooling/quality/tooling_manifest.yaml` (daraus `docs/architecture/quality-tooling-map.md` neu erzeugt), `tooling/linters/powerbi/README.md`, `internal/project_mgmt/FABRIC_FABCON_EU_2026_PLAN.md` (W5.15, BPA-Teil erledigt) |

In VS-Code-Tasks, `.claude/settings.json`, Skills und Workflows gab es keinen Aufrufer der vier Skripte. Das ist per `git grep` geprüft.

## Gelaufene Tore

| Tor | Ergebnis |
|---|---|
| `python -m pytest tooling/tests/test_check_bpa.py tooling/tests/test_upstream_sources_pins.py` | 52 passed |
| `python scripts/check_index.py --strict` | 0 harte Befunde, 9 Warnungen (9 auch auf der Basis) |
| `python scripts/check_lint_ratchet.py` | OK, 2.490 wie eingefroren |
| `python scripts/check_plattform.py` | OK |
| `python scripts/check_workflows.py` | OK, 6 Workflow-Dateien |
| Stage 1 (`pwsh tooling/run_stage1_checks.ps1`, Aurora-Showdaten 460 Dateien laut Lock geprüft, `npm ci` in `tooling/validation`) | grün, 0 FAIL, `check_bpa.py` darin OK |
| `python -m pytest tooling/tests/ products/ -q` | siehe PR-Beschreibung (Lauf am Ende der Runde) |
| `python tooling/quality/check_upstream_sources.py --summary` | `bpa.analysis_services` up_to_date. Exit 1 kommt von zwei anderen, schon vorher offenen Quellen (`skills_for_fabric` v0.3.21, `fntk` 0.0.1a12) |

## Offene Punkte

- ⚠️ UNKLAR: Kontingent für den Windows-Lauf. Freelancing hat etwa 38 Minuten je Lauf hergeleitet, und Windows-Minuten zählen doppelt. Der Workflow läuft bei nicht-Entwurfs-PRs, die dist-Modelle, Regeln, Pin oder den Workflow selbst ändern, und per `workflow_dispatch`. Annahme: das ist so gewollt. Bitte bestätigen oder auf `workflow_dispatch` allein beschränken.
- ⚠️ UNKLAR: ob Tabular Editor 2.28.0 die Eigenschaft `LineageTag` in BPA-Ausdrücken kennt. Belegt ist nur, dass `LineageTag` in TE2 `TOMWrapper/Interfaces.cs` vorkommt (Codesuche); in TE2 ausgeführt wurde die Regel nicht. Annahme: ja. Der erste Windows-Lauf zeigt es: eine nicht kompilierbare Regel meldet TE2 im Protokoll.
- Zwei Regeln widersprechen einer ALUCA-Entscheidung. `ALUCA_DAX_LY_TIME_INTELLIGENCE` und `ALUCA_DAX_TIME_INTELLIGENCE_NATIVE` empfehlen SAMEPERIODLASTYEAR und DATEADD. Der Generator bildet Vorjahre aber bewusst über einen Monatsindex, weil `dim_date` nicht als Datumstabelle markiert ist (Beschreibung von `CLV (Customer Lifetime Value) PY`). Heute melden beide 0, weil die Measures `PY` heißen und kein `DATE(YEAR()-1)` nutzen. Beide stehen als Hinweis (Severity 1). Ob sie bleiben, entscheidet Florian.
- `ALUCA_LINEAGE_TAG` meldet 605 Objekte ohne `lineageTag`. Das ist ein Befund am Generator, nicht an der Regel, und hier nicht behoben.

## Bewusst nicht gemacht

- `validate_dax.ps1`, `validate_tmdl.ps1` und `run_all_checks.ps1` sind nicht entfernt, laut Auftrag. Sie brauchen eine Portierung: der Auto-Fix gehört in den Generator, die 14 Governance-Prüfungen gehören nach Stage 1.
- `check_dax_best_practices.ps1` und `bpa-rules-dax.json` bleiben, weil `validate_dax.ps1` dieselbe Datei liest und die CI den Läufer ruft. Damit stehen die DAX-Regeln bis zur Portierung zweimal im Repo, im alten Format und in `aluca-bpa-rules.json`. Nach der Doktrin ist das ein Doppel. Es ist hier benannt und in `tooling/linters/powerbi/README.md` als offen vermerkt. Den Leerzeichenfehler im alten Läufer habe ich nicht repariert, weil der Läufer abgelöst werden soll.
- `bpa-rules-tmdl.json` ist unverändert, weil `validate_tmdl.ps1` die Datei mit Auto-Fix in der Generierung nutzt.
- Den offiziellen Satz habe ich nicht in Python nachgebaut. Official-First heißt: Er läuft mit dem Werkzeug des Herstellers. Ein Python-Nachbau wäre eine zweite, ungeprüfte Fassung.
- Die dist-Modelle sind nicht korrigiert. Die Befunde sind informativ, und Severity 3 hat heute 0 Befunde.
- `lint.rules.yaml` hat keinen Leser, auch vorher nicht. `fix_mojibake.ps1` ist ein Reparaturwerkzeug ohne Aufrufer. Beide bleiben, beides lag außerhalb des Auftrags.
- Die schon vorhandenen Ruff-Befunde in `check_upstream_sources.py` (F401 `sys`, E501) sind nicht angefasst. Die Sperrklinke ist unverändert.
- Die CI ist nicht gestartet. Der PR ist ein Entwurf, also sind `tabular-bpa.yml` und Stage 1 auf GitHub-Runnern nicht gelaufen.
