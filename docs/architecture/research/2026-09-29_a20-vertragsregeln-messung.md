# A-20: `quality_rules` der Datenverträge, gezählt und gegen Aurora-Gold ausgeführt

Stand 29.09.2026. Nur gemessen; die Messskripte liefen außerhalb des Repos (lokaler Arbeitsbereich der Sitzung) und sind bewusst nicht eingecheckt — ein zweiter DQ-Ausführer neben Meridians `emit_dq_gates` wäre Option B, gegen Tool-Reuse. Methode und Regexe stehen vollständig unten.

**Quellen**
- **Verträge:** AUL `origin/main` @ `0c91641583d644c0f249e6f1c4c9970a4d9fc28f`, gelesen per `git show`.
- **Freelancing:** `origin/main` @ `a93ecca7`.

**Skripte (lokal, nicht eingecheckt)**
- `a20_delta.py`: liest Delta-Tabellen. Es spielt `_delta_log` nach (add/remove, Checkpoint) und liest nur die aktiven Parquet-Dateien.
- `a20_messung.py`: zählt, parst und führt die Regeln aus. Das Ergebnis steht in `a20_ergebnis.json`.
- `a20_auswertung.py`: baut die Tabellen, Ausgabe in `a20_auswertung.txt`.
- Aufruf: `python a20_messung.py <contracts> <gold1> <gold2>` (duckdb 1.5.6).

## 0. Abweichungen von Auftrag und Ledger

| # | Erwartet | Gemessen |
|---|---|---|
| 0.1 | „AUL #498 hat die Showdaten aus Git genommen“ | #498 ist ein **offener Entwurf** und nicht gemergt (GitHub-API, `state: open, draft: true`). `origin/main` 0c916415 trackt noch 906 Dateien unter `showcases/aurora_group/data/gold` (`git ls-tree -r`). |
| 0.2 | Die Arbeitskopie eines Nebenbaums (Branch i21-w0) | Sie ist inhaltlich gleich `origin/main`: `git diff --stat <w0-HEAD> origin/main -- …/data/gold` ist leer, und `git status` meldet 0 Zeilen. Sie ist deshalb **Lauf 1 (maßgeblich)**. |
| 0.3 | Neulauf der Generatoren (lokal) | Das ist ein Neulauf der Generatoren (der PR-Text von #498 sagt dazu: „ein Neulauf ergibt einen neuen Datensatz“). In `dim_date` und `dim_org` verweist der Delta-Log auf gelöschte Dateien, damit haben beide 0 aktive Dateien. So bestätigt sich der in #498 beschriebene Fehler von `generate_dims.py`. Außerdem fehlen `fact_complaints`, `fact_quality_costs` und `fact_supplier_risk`. Dieser Lauf ist nur **Lauf 2 (Gegenmessung)**. |
| 0.4 | `scripts/check_validate_data_contracts.py` | Die Datei liegt unter `tooling/validation/check_validate_data_contracts.py`. Sie prüft nur `domain`/`dimension`/`fact` und `name`; `quality_rules` liest sie nicht. |
| 0.5 | Die Verträge beschreiben Gold | Die README der Verträge sagt: „Define the **Silver layer**“. Die Verträge gegen Gold zu prüfen ist eine **Herleitung**, keine Vertragsaussage. |
| 0.6 | Ledger A-20: „257 Freitext-Regeln“ | **Bestätigt.** Es sind 257 Einträge (siehe 1). |

## 1. Zählung und Parsbarkeit (gemessen)

**Methode**
- **Zählung:** `yaml.safe_load` je Vertrag. Ein Eintrag ist ein Listenelement; bei `freshness_sla` ist es ein Schlüssel des Dicts (ein Skalar zählt als 1 Eintrag).
- **Zerlegung:** Jeder Eintrag wird mit den Regexen unten in **Atome** zerlegt, ein Atom ist eine Prüfung aus Tabelle, Spalte und Prädikat.
  - Getrennt wird an `;` und an ` and `, aber nicht innerhalb von `()` oder `[]`.
  - Ein Schlusskommentar `(…)` und ein angehängtes `when (both) present` werden vorher entfernt.
- **Klassen je Eintrag:**
  - *parsebar*: alle Teilsätze erkannt
  - *teilweise*: einige Teilsätze erkannt
  - *nicht*: kein Teilsatz erkannt
  - *doku*: Erlaubnisaussage, aus der keine Prüfung folgt

**Regexe**, so wie sie in `a20_messung.py` stehen:
```
Präfix     ^(?P<tab>fact_\w+)\.(?P<cols>[^:]+?):\s*(?P<body>.+)$
not null   ^never null$
unique     ^(?:(?P<subj>[A-Za-z][\w %]*?)\s+)?unique per row$
Bereich    ^(?P<int>integer\s+)?in \[(?P<lo>-?\d+(?:\.\d+)?);\s*(?P<hi>-?\d+(?:\.\d+)?)\]$   |  ^(lo)\.\.(hi)$
Enum       ^in \[(?P<vals>[^\];]+)\]$
Vergleich  ^(?:(each)\s+|(?:must be)\s+|(?P<subj>[A-Z][\w %\-]*?)\s+)?(?P<op>>=|<=|!=|>|<|=)\s*(?P<rhs>Zahl|Spaltenname)$
           (rhs mit " + " / " - " → nicht parsebar; Spaltenliste mit +*/ → nicht parsebar)
RI         ^(?:(?P<tab>fact_\w+)\.)?(?P<col>[A-Za-z][\w ]*?)\s*→\s*(?P<dim>dim_\w+)(?:\s*\((?P<mode>[^)]*)\))?$
           Präfix "All facts:" → alle Fakten des Vertrags mit dieser Spalte; Modus aus eigener
           Klammer, sonst aus der letzten Klammer des Eintrags, sonst "unspezifiziert"
Doku       ^(?:[A-Z][\w ]*?\s+)?(may be negative|nullable|no (range|floor) (restriction|constraint))\b(?!.*\bonly\b)
```

### T1: Einträge je Vertrag und Kategorie (parsebar oder doku / gesamt)

| Vertrag | freshness_sla | key_nullability | value_ranges | referential_integrity | Summe |
|---|---|---|---|---|---|
| commercial_sales | 1/1 | 5/5 | 6/6 | 9/9 | 21/21 |
| efficiency | 3/3 | 3/3 | 4/4 | 2/3 | 12/13 |
| esg | 5/5 | 3/3 | 5/5 | 2/2 | 15/15 |
| executive | 3/3 | 5/5 | 6/8 | 2/5 | 16/21 |
| experience | 3/3 | 4/4 | 5/5 | 6/6 | 18/18 |
| finance | 8/8 | 7/7 | 7/9 | 5/5 | 27/29 |
| governance | 6/6 | 6/6 | 8/10 | 6/6 | 26/28 |
| growth | 3/3 | 3/3 | 6/6 | 2/3 | 14/15 |
| operations | 8/8 | 6/6 | 7/9 | 9/9 | 30/32 |
| people | 3/3 | 4/4 | 10/10 | 5/5 | 22/22 |
| risk | 3/3 | 3/3 | 4/4 | 3/3 | 13/13 |
| supply_chain | 10/10 | 4/4 | 9/9 | 7/7 | 30/30 |
| **Summe** | **56/56** | **53/53** | **77/85** | **58/63** | **244/257** |

### T2: Status je Kategorie

| Kategorie | parsebar | doku | teilweise | nicht |
|---|---|---|---|---|
| freshness_sla | 56 (nur die Struktur Tabelle → Takt; ausführbar sind sie nicht, siehe 2.4) | 0 | 0 | 0 |
| key_nullability | 51 | 2 | 0 | 0 |
| value_ranges | 74 | 3 | 4 | 4 |
| referential_integrity | 58 | 0 | 0 | 5 |

**Atome:** 369 ausführbare, davon 360 verschieden (die Regeln zu `fact_output` stehen doppelt in key_nullability und value_ranges). Dazu kommen 9 Doku-Atome.

| Atom-Art | Anzahl |
|---|---|
| notnull | 176 |
| cmp | 97 |
| ri | 78 |
| range | 14 |
| unique | 2 |
| enum | 2 |

**Nicht oder nur teilweise parsebar (13 Einträge):**
- 3 × `Source: …`: Lineage-Prosa, keine Regel.
- `fact_exec_summary must align with fact_finance … within rounding tolerance`
- `fact_kpi_snapshot.KpiId and fact_risk_weights.KpiId share a common KPI catalogue …`
- `Revenue Amount: may be negative only for credit/reversal entities`
- `KPI Delta: = Post KPI Value - Pre KPI Value`
- `Outcome Status: Successful requires …`
- `Scrap Units + Rework Units: <= Total Units`
- Teilweise (Summen- und Arithmetikklauseln): `sum of buckets = AR Amount`, `= AR 31-60 + …`, `>= Internal Failure Cost + External Failure Cost`, `weights … should sum to 1`

**Hergeleitet, aber gegengeprüft:** Alle 176 notnull-Atome und alle 78 RI-Atome sind in den Vertragsspalten **schon strukturiert** hinterlegt:
- Die Spalte trägt kein `nullable: true`.
- Sie trägt ein `ref: dim_x`.

Methode: Abgleich (Vertrag, Tabelle, Spalte) gegen `fact[].columns[]`. Es gab 0 Treffer „Spalte nicht im Vertrag“ und 0 Widersprüche im Modus (required gegen nullable).

Die Verträge führen daneben:
- 208 `ref`
- 235 `nullable`
- 69 `allowed_values`
- 73 `role: key`

Die Prosa in `quality_rules` doppelt also 254 der 369 Atome. Neu gegenüber den strukturierten Feldern sind nur die Wertebereiche und Vergleiche (113 Atome) und `freshness_sla`.

## 2. Ausführung gegen Aurora-Gold

**Methode**
- duckdb auf die aktiven Delta-Dateien.
- Tabellen- und Spaltennamen werden exakt verglichen; mit `difflib` (Schwelle 0,6) steht der ähnlichste Name als Hinweis dabei.
- **SQL je Prädikat:**
  - notnull: `count(*) where c is null`
  - unique: `count(*) - count(distinct c)`
  - Bereich, Vergleich, Enum: `where c is not null and not (…)`, d. h. NULL besteht
  - RI: verwaiste Nicht-NULL-Schlüssel, bei required zusätzlich die NULLs. Der Dim-Schlüssel ist die Spalte mit `role: key` im Vertrag, sonst die gleichnamige Spalte.

**Gegenprobe:** Absichtlich verschärfte Regeln müssen Verletzungen melden, und das tun sie in beiden Läufen:
- NPS in [0;5]: 634 von 900
- Net Sales > 1e9: 9.353.179 von 9.353.179
- Run Time > Planned Time: 73.080 von 73.080
- fact_sales.CustomerKey → dim_promo: 9.343.777 verwaist

„0 verletzt“ heißt also „gelaufen, nichts gefunden“.

### T3: Ergebnis je Kategorie (Lauf 1 = origin/main-Datenstand; in Klammern Lauf 2 = regen)

| Kategorie | Atome | gehalten | verletzt | nicht prüfbar: Tabelle fehlt | Spalte fehlt | Dim/Schlüssel fehlt |
|---|---|---|---|---|---|---|
| key_nullability | 185 | 76 (74) | **0 (0)** | 99 (101) | 10 (10) | 0 (0) |
| value_ranges | 106 | 42 (41) | **0 (0)** | 49 (54) | 15 (11) | 0 (0) |
| referential_integrity | 78 | 32 (23) | **0 (0)** | 29 (29) | 16 (16) | 1 (10) |
| **Summe** | **369** | **150 (138)** | **0 (0)** | 177 (184) | 41 (37) | 1 (10) |

Nur **150 von 369 Atomen (41 %) sind prüfbar**, und sie halten alle. Sie verteilen sich auf 145 verschiedene Atome in 32 Faktentabellen. 219 Atome (59 %) sind nicht prüfbar, weil die Showcase-Daten die Vertragsobjekte nicht haben.

### T4: Je Vertrag, Lauf 1 (gehalten / verletzt / nicht prüfbar)

| Vertrag | gehalten | verletzt | nicht prüfbar |
|---|---|---|---|
| commercial_sales | 24 | 0 | 7 |
| efficiency | 0 | 0 | 24 |
| esg | 0 | 0 | 22 |
| executive | 0 | 0 | 23 |
| experience | 22 | 0 | 4 |
| finance | 26 | 0 | 9 |
| governance | 1 | 0 | 46 |
| growth | 0 | 0 | 21 |
| operations | 31 | 0 | 15 |
| people | 12 | 0 | 22 |
| risk | 0 | 0 | 21 |
| supply_chain | 34 | 0 | 5 |

Fünf Verträge sind gegen den Showcase **gar nicht prüfbar**: efficiency, esg, executive, growth und risk. Ihre Faktentabellen fehlen alle.

### 2.1 Befund: Namensabgleich Vertrag gegen Daten (Lauf 1)

**Tabellen, die in den Daten fehlen:** Die Verträge nennen 105 verschiedene Tabellen (136 Vorkommen über 12 Verträge). **49 davon fehlen** in den Daten.

Fehlende Tabellen, die von Regeln betroffen sind (26):
`fact_action_governance, fact_audit, fact_compliance, fact_control_effectiveness, fact_cost_per_unit, fact_customer_acquisition, fact_di, fact_dq, fact_emissions, fact_energy, fact_exec_summary, fact_hr, fact_it, fact_kpi_snapshot, fact_labor_productivity, fact_process_efficiency, fact_product_launch, fact_projects, fact_revenue_growth, fact_risk_incidents, fact_risk_register, fact_risk_weights, fact_safety, fact_security, fact_survey, fact_water_waste`. Dazu kommt die RI-Dimension `dim_supplier`: sie fehlt, und die Daten führen `SupplierKey` ohne Dimension.

**Spalten, die in vorhandenen Tabellen fehlen:** 41 Atome sind davon betroffen. Die Umbenennungen sind wahrscheinlich, weil `difflib` einen ähnlichen Namen findet:

| Vertrag | Daten | Bemerkung |
|---|---|---|
| `fact_promo.Promo Cost Amount` | `Promo Cost` | |
| `fact_support_cases.IssueTypeKey` | `IssueKey` | Auch `dim_issue_type` heißt in den Daten `IssueKey`/`IssueType`, im Vertrag `IssueTypeKey`/`Issue Type`/`Issue Category`. |
| `fact_action_outcome.Outcome Status` | `outcome_status` | Die Daten sind snake_case; 9 von 15 Vertragsspalten fehlen. |
| `fact_ops_failures.CauseCodeKey` | `Cause Code` | Text statt Schlüssel |

Ganz ohne Gegenstück in den Daten sind:
- `fact_promo`: ProductKey, DateKey, OrgKey, Cannibalized Sales Amount
- `fact_accounts_receivable`: die 5 Aging-Buckets
- `fact_cost`: Actual Cost Amount, CostCategoryKey
- `fact_forecast`: Naive, Statistical und Actual Units, ForecastabilityKey
- `fact_quality_costs`: Prevention, Appraisal, Internal und External Failure Cost
- die Schlüssel `LossTypeKey`, `FailureModeKey`, `DefectModeKey`, `CarrierLaneKey`, `SlaPolicyKey`, `ShrinkageCategoryKey`, `AgentSkillKey`

28 vorhandene Tabellen haben mindestens eine fehlende Vertragsspalte; die Liste steht in `a20_auswertung.txt`.

**Datentabellen ohne Vertrag:** `dim_account, dim_currency, fact_action_log, fact_customer_interactions, fact_gl_journal, fact_inventory_snapshot, fact_sales_budget, fact_supplier_risk, fact_working_capital`.

### 2.2 Befund: Semantik von „nullable“ gegen den unbekannten Eintrag

Die Regel `fact_sales.PromoKey → dim_promo (nullable; absent = non-promotional transaction)` gilt als gehalten, aber nicht so, wie der Vertrag es sagt:
- In den Daten ist PromoKey **nie NULL**.
- 8.761.794 Zeilen tragen `-1`, und `dim_promo` hat die Zeile `-1 'NONE' 'No Promotion'`.

Gemessen: `count(*) filter (where PromoKey<=0)` und `select … from dim_promo where PromoKey<=0`.

Der Vertrag sagt „absent = NULL“, die Daten benutzen einen unbekannten Eintrag. Das Meridian-Gate (`emit_dq_gates`) geht ausdrücklich vom unbekannten Eintrag aus („Orphans carry the explicit unknown member …, never NULL“). Der Vertragstext widerspricht damit der Konvention des Ausführers.

### 2.3 Gegenmessung (Lauf 2, regen)

Es gibt ebenfalls 0 Verletzungen. Wegen der fehlenden `dim_date`/`dim_org` (siehe 0.3) sind weniger Atome prüfbar: 138 statt 150.

Die Aussage „nichts verletzt“ ist in beiden Datenständen gleich. Die Zahl der prüfbaren Atome hängt am Datenstand.

### 2.4 freshness_sla (hergeleitet, nicht gemessen)

Die 56 Einträge lassen sich strukturell parsen (Tabelle → daily/monthly/…). Gegen statische Showcase-Daten ist Aktualität aber nicht messbar: es gibt keine Ladezeitstempel-Spalte, und die Daten enden 2024.

Die Delta-`commitInfo.timestamp` wäre eine mögliche Quelle (Beispiel: `fact_action_log` 1770307924738 ms). Das ist UNKLAR, weil es nicht geprüft wurde.

Meridian `provision_dq.freshness_proposals` lässt Freshness bewusst als Vorschlag stehen, weil `loaded_at_field` unbekannt ist.

## 3. Tool-Reuse und Official-First

### T5: Kandidaten

| Kandidat | Was er tut (gelesen) | Führt er `quality_rules` aus? |
|---|---|---|
| Freelancing `core/dataarch_engine/blueprint/provision_dq.py` (`emit_ingress_dq`), in AUL gespiegelt nach `tooling/superversion/vendor/meridian_dataarch/provision_dq.py` | Erzeugt dbt-`schema.yml`-Tests für die **Ingress**-Seite. **Eingang:** `schemas_by_source: {source → [{"name": tabelle, "properties": [{"name", "required": bool, …}]}]}` (Quell-Introspektion über `INFORMATION_SCHEMA`/OpenAPI) plus `confirmed_keys`. **Ausgang:** `not_null` für `required`, `unique` nur für bestätigte Einzelschlüssel, Freshness nur als Vorschlag. Der Docstring sagt ausdrücklich, er sei „supplier number two“ zu `emit_dq_gates` und „not a second DQ engine“. | Nein. Er ist quellseitig, und die Quell→Gold-Zuordnung wird bewusst **nicht** geraten. Der Vertrag lässt sich nicht sinnvoll auf diesen Eingang abbilden: Die Vertragstabellen sind Silver/Gold und keine Quellen, `properties.required` deckt nur notnull ab, und für Bereiche, Vergleiche und RI gibt es kein Feld. |
| Freelancing `provision_transforms.emit_dq_gates(blueprint, column_tests=…)` | Das **eigentliche** DQ-Tor, dbt-`schema.yml` je Gold-Produkt. **Eingang `column_tests`:** `{produkt: [{"name": spalte, "tests": ["not_null", "unique", {"relationships": {"to": "ref('gold_dim')", "field": key}}]}]}`. Ohne Lieferant schreibt es `TODO(contract:<silver-contract>)` mit dem Text „business rules live in the silver data contract“. Lieferant 1 ist das SAP-Paket (`sap_dq.sap_dq_column_tests`), Lieferant 2 ist `provision_dq`. | Nein, aber **es wartet ausdrücklich auf den Vertrag**. Der Platzhalter zeigt genau auf die AUL-Verträge. |
| Freelancing `provision_transforms.emit_mlv` | Erzeugt Fabric-MLV-DDL mit `CONSTRAINT … CHECK (key IS NOT NULL) ON MISMATCH DROP/FAIL`. Den Schlüssel liest es aus dem governed catalog (`key`, `column_types`). | Nein. Heute nur NOT NULL auf dem Schlüssel. |
| AUL `tooling/superversion/arch_targets/fabric.py` | Ruft `emit_ingress_dq`, sofern Introspektionsantworten vorliegen. `emit_dq_gates` und `emit_mlv` sind **nicht** in der Spiegel-API (`_dataarch_vendor.py` exportiert aus `provision_transforms` nur `emit_transforms`). | Nein |
| AUL `tooling/generator/export_governed_catalog.py` | **Die bestehende Brücke** Vertrag → Meridian (`meridian/governed-catalog/v1`). Sie exportiert je Tabelle nur `name, kind, domain, columns`; `ref`, `nullable`, `role: key`, `allowed_values` und `quality_rules` gehen verloren. | Nein |
| AUL `tooling/validation/check_validate_data_contracts.py` | Prüft nur die Struktur (siehe 0.4). | Nein |
| `git grep quality_rules origin/main -- '*.py'` | Alle Treffer gehören zu *anderen* `quality_rules`-Feldern (Visual-Registry, use_case_delivery, Action-Codes), keiner zu den Datenverträgen. | Das bestätigt A-20. |

Ein **lokaler Ausführer** der erzeugten `schema.yml` ließ sich weder in Freelancing noch in AUL finden (`git grep "dbt test"` findet nur Doku-Text). Die Tore setzen dbt oder einen dbt-kompatiblen Läufer voraus. Ob es irgendwo einen ungesuchten Läufer gibt, ist UNKLAR.

### Official-First (Microsoft Learn, gelesen am 29.09.2026)

- **Fabric Materialized Lake Views, Constraints.** Quellen: <https://learn.microsoft.com/fabric/data-engineering/materialized-lake-views/data-quality> und <https://learn.microsoft.com/fabric/data-engineering/materialized-lake-views/create-materialized-lake-view>.
  - `CONSTRAINT name CHECK (<bool-expr>) ON MISMATCH DROP|FAIL` wird je Zeile ausgewertet, mit eingebauten Spark-Funktionen.
  - Verstöße erscheinen in der Lineage und im MLV-DQ-Report.
  - **Hergeleitet:** Damit sind notnull, Bereich, Vergleich zwischen Spalten und Enum ausdrückbar, zusammen 289 von 369 Atomen.
  - RI und unique brauchen einen Join bzw. ein Aggregat. Ob MLV-CHECK Unterabfragen zulässt, ist UNKLAR, weil die Fabric-Seite es nicht sagt. Bei Databricks-Expectations sind Unterabfragen und Aggregate ausdrücklich verboten.
- **Microsoft Purview Unified Catalog, Data Quality.** Quellen: <https://learn.microsoft.com/purview/unified-catalog-data-quality-rules>, <https://learn.microsoft.com/purview/unified-catalog-data-quality-fabric-lakehouse> und <https://learn.microsoft.com/purview/unified-catalog-data-quality-troubleshooting>.
  - Regeltypen: Freshness, Unique, Empty/blank, Table lookup (RI), Format, Data type, Custom. Fabric-Lakehouse-Delta wird unterstützt.
  - **Hindernisse:**
    - „The current version doesn't support column names with spaces“ (Troubleshooting, Profiling). Die Vertragsspalten heißen durchgehend `Net Sales Amount` usw.
    - Die Purview-MSI braucht die Rolle Contributor im Workspace.
    - Die Regeln leben im Purview-Portal und nicht in Git.
  - Lizenz- und Kostenfolgen: UNKLAR.

## 4. Umsetzungsoptionen

| | Option A: Lieferant 3 für `emit_dq_gates` und MLV-CHECK | Option B: AUL-eigener duckdb-Prüfer | Option C: Purview DQ |
|---|---|---|---|
| **Wo** | Freelancing `core/dataarch_engine/blueprint/` (neues `contract_dq.py` nach dem Muster von `sap_dq.py`), gespiegelt nach AUL; AUL erweitert `export_governed_catalog.py` um `key`, `ref`, `nullable`, `allowed_values` und strukturierte Checks | AUL `tooling/validation/`, als Erweiterung von `check_validate_data_contracts.py` oder `check_showcase_delta.py` | Purview-Portal oder -API |
| **Ausführung** | dbt-`schema.yml` (not_null, unique, relationships, accepted_values) und `emit_mlv`-CHECKs für Bereiche und Vergleiche; beides läuft im Kunden-Fabric | lokal und in CI gegen die Showcase-Daten | Purview-Scan |
| **Pro** | Kein neues Silo: dieselbe DQ-Oberfläche, der dritte Lieferant schließt den vorhandenen `TODO(contract:…)`. Official-First über MLV. 254 von 369 Atomen lassen sich ohne Prosa-Parser aus den **schon strukturierten** Feldern (`nullable`, `ref`) erzeugen. | Schnell, und es liefert sofort einen CI-Nachweis. Das Messskript hier ist ein Prototyp. | Offizielles Werkzeug mit Scores und Fehlerzeilen |
| **Contra** | Änderung über zwei Repos plus Spiegel-Sync. Kein lokaler Nachweis in AUL-CI ohne dbt oder MLV. Bereiche und Vergleiche brauchen im Vertrag ein strukturiertes Format; die Prosa zu parsen wäre ein Merksatz und kein Vertrag. | Zweite DQ-Engine neben Meridian: das verstößt gegen die Tool-Reuse-Pflicht. Parst Prosa, und 59 % der Regeln sind gegen den Showcase nicht prüfbar. | Leerzeichen in Spaltennamen blockieren das Profiling. Die Regeln liegen außerhalb von Git und driften vom Vertrag weg. Braucht MSI-Rechte und Lizenz. |

**Empfehlung: Option A**, in drei Schritten.

1. **Vertrag strukturieren (AUL).** Den Prosa-Block `quality_rules` durch strukturierte Spaltenfelder ersetzen, zum Beispiel `checks: [{gte: 0}, {lte_column: "Output Units"}]`. notnull und RI stehen schon als `nullable` und `ref` da. Freshness geht in ein Tabellenfeld mit `loaded_at_field`. Die 13 Prosa-Regeln bleiben als Beschreibung stehen. `check_validate_data_contracts.py` prüft dann das Schema der neuen Felder.
2. **Brücke erweitern (AUL).** `export_governed_catalog.py` exportiert die Felder `key`, `refs`, `not_null`, `accepted_values` und `checks`. `emit_mlv` liest `key` bereits aus diesem Katalog.
3. **Ausführung in Meridian.** Ein neuer Lieferant `contract_dq_column_tests(governed_catalog)` → `emit_dq_gates(column_tests=…)`. Dazu erzeugt `emit_mlv` CHECK-Constraints aus `checks`. Beide werden gespiegelt, und `emit_dq_gates`/`emit_mlv` kommen in die Spiegel-API von `fabric.py`. Für den Showcase-Nachweis in AUL-CI führt ein kleiner Läufer die **erzeugten** Artefakte auf duckdb aus, statt Prosa zu lesen. Er gehört als Werkzeug zu Meridian, damit es nur eine Semantik gibt.

**Vorbedingung** (gemessen, siehe 2.1): Solange 49 Vertragstabellen und 41 Regelspalten im Showcase fehlen und `PromoKey` den unbekannten Eintrag statt NULL nutzt, bleibt jedes Tor gegen den Showcase zu 59 % „nicht gelaufen“. Die Namensabweichungen (`IssueKey`/`IssueTypeKey`, `Promo Cost`/`Promo Cost Amount`, snake_case in `fact_action_outcome`) gehören als eigener Ledger-Punkt entschieden: Welche Seite ist die Wahrheit?
