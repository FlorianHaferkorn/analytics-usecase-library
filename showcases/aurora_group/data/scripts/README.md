# Aurora gold data generators

## Showdaten holen (seit 29.09.2026, Meridian D-578)

Die Gold-Daten (`gold/dimensions/`, `gold/facts/`, `gold/security_user_org/`: Parquet +
`_delta_log`) liegen **nicht mehr in Git**. Ein Befehl stellt sie her:

```bash
python showcases/aurora_group/data/showdaten.py holen      # Release laden, SHA-256 pruefen, entpacken
python showcases/aurora_group/data/showdaten.py pruefen    # 0 da · 1 weicht vom Lock ab · 2 fehlt
```

`showdaten.lock.json` hält Tag, Asset, SHA-256 des Archivs und jede Datei mit Größe und
SHA-256. Ohne Daten melden `scripts/check_showcase_delta.py` und
`tooling/validation/check_data_model.py` Exit 2 „nicht gelaufen", die datenabhängigen Tests
stehen mit „nicht gelaufen: … holen mit …" im Skip-Grund (`pytest -rs`),
`tooling/validation/check_model_vs_gold.py --strict` endet mit Exit 2 „nicht geprüft".

`holen` lädt immer per `gh release download` (Token aus `GH_TOKEN`, nie als Argument). Fehlt
der Release oder das Asset, endet es mit Exit 2 und nennt Tag, Asset und die Zeile zum
Hochladen. Die CI (`stage1.yml`, Jobs `python-checks` und `stage1`) holt vor den Tests; ein
fehlgeschlagenes Holen macht den Job rot (Schritt „Showdaten vorhanden", dazu das Gold-Tor),
die datenunabhängigen Tests laufen trotzdem.

**Datenstand im Lock** (`showdaten-aurora-2026-09-29c`): Gold aus `origin/main` 011478f8
(nach #535: `dim_date` über das Delta-Log neu geschrieben — das Log von 29b nannte eine falsche
Dateigröße und kannte `CalendarYearMonth`/`MonthNumber`/`Week` nicht, `deltalake` brach ab;
sonst gleich 29b: nach #522 10 Modellspalten, XYZ-Klasse), 460 aktive Dateien, 614,4 MB
Inhalt, Archiv 615,1 MB. `29b` wurde nie veröffentlicht. Gebaut mit `git archive origin/main showcases/aurora_group/data/gold` in einen
Scratch-Ordner und `packen --gold <ordner>`; zweimal gepackt, bytegleich (SHA-256 gleich).
Net Sales 12/2024 (aktive Dateien `fact_sales`, `DateKey` 20241201–20241231, DuckDB; gegen
pyarrow über die Partition `Fiscal Year=2024/Fiscal Month=12` gestellt): 439.447.179,34 in
198.303 Zeilen, gleich im ersten Paket, in `origin/main` und im entpackten neuen Paket.

**Warum ein Archiv und kein Generator-Neulauf** (gemessen 29.09.2026, Methode: die ganze
Kette in einer Kopie von `HEAD` ohne Daten gefahren, `deltalake==1.6.2` –
`generate_gold_layer_contract_v2.py`, `generate_aurora_gold.py`, `generate_gapfill_gold.py`,
`generate_security_user_org.py`, `generate_fact_action_outcome.py`, zusammen 13 min 8 s –, dann
je Tabelle Zeilenzahl, Spaltenmenge und eine reihenfolgeunabhängige Prüfsumme über alle Zellen
per DuckDB, nur aktive Dateien laut `_delta_log`): von 66 Tabellen sind **47 logisch gleich**,
11 haben gleiche Zeilen und Spalten, aber andere Werte (u. a. `fact_sales` 9.353.179 Zeilen,
`dim_customer` in `Channel Preference`/`Tenure Bucket`, `fact_sales_budget`, `fact_gl_journal`),
5 andere Zeilenzahlen (`fact_plan_sales` 6.000.000 → 1.500.000, `fact_customer_value`
144.171 → 571.907, `fact_customer_events`, `fact_action_log`, `fact_customer_interactions`),
3 hat kein aktiver Generator (`fact_complaints`, `fact_quality_costs`, `fact_supplier_risk`
stammen aus `internal/archive/showcases/gold_maintenance/generate_missing_facts.py`).
Ursache: der eingecheckte Stand ist über Februar bis August 2026 aus mehreren Generatorständen
gewachsen (laut `_delta_log`: `delta-rs` 1.4.0, 1.5.1, 1.6.2); spätere Codeänderungen, etwa die
`dim_product`-Korrektur vom 11.08.2026, verschieben die Zufallsfolge für alles danach, und
`fact_sales` schrieb zuletzt ein Transform (`aluca-plan-variance-transform`, 16.07.2026), der
nicht im Repo liegt. Die alten Generatorstände sind nicht in der Git-Historie. Ein Neulauf ist
damit ein **neuer** Datensatz, keine Wiederherstellung. Zusätzlich lässt der Neulauf
`dim_date` und `dim_org` inkonsistent zurück: `generate_dims.py` schreibt `part-00000.parquet`
neben einen `_delta_log`, dessen aktive Datei fehlt (`check_showcase_delta.py` rot; in
Power BI die spaltenlose Tabelle). Ob die heutige Kette mit sich selbst deterministisch ist
(zwei Läufe gleich), ist nicht gemessen.

**Archiv bauen** (Owner, einmal je Datenstand; ein Release ist nach außen sichtbar und wird
nicht automatisch angelegt):

```bash
python showcases/aurora_group/data/showdaten.py packen --aus-dir /tmp/showdaten \
  --tag showdaten-aurora-2026-09-29c [--gold <ordner mit dimensions/facts/security_user_org>]
cp /tmp/showdaten/showdaten.lock.json showcases/aurora_group/data/showdaten.lock.json
gh release create showdaten-aurora-2026-09-29c /tmp/showdaten/aurora_gold_2026-09-29c.tar \
  --repo FlorianHaferkorn/analytics-usecase-library --title "Aurora-Showdaten showdaten-aurora-2026-09-29c"
```

Ein neuer Datenstand bekommt einen neuen Tag (Asset-Name folgt aus dem Tag); ein Release wird
nicht überschrieben, der Lock pinnt den SHA-256 des Archivs.

Das Archiv enthält nur aktive Dateien (letzte Log-Aktion `add`) plus die Logs; es ist
bytegleich reproduzierbar (feste Reihenfolge, `mtime` 0, Besitzer 0).

## Generatoren

A single entry point generates all synthetic gold-layer parquet for the Aurora showcase. Output is written to `showcases/aurora_group/data/gold/` (dimensions and facts). Contract-compliant per framework data contracts; table names match Aurora domain semantic models (and gold layer) (e.g. `dim_case_queue`, `fact_support_cases`, `fact_accounts_payable`, `fact_cash_position`, `fact_cash_flow`).

**Run from repo root:**

```powershell
# All domains (operations, supply_chain, experience, finance, commercial)
py showcases/aurora_group/data/scripts/generate_aurora_gold.py

# Selected domains only
py showcases/aurora_group/data/scripts/generate_aurora_gold.py --domain operations
py showcases/aurora_group/data/scripts/generate_aurora_gold.py --domain supply_chain,experience,finance
```

**Domains:** `commercial`, `operations`, `supply_chain`, `experience`, `finance` (default: all).

**Prerequisites:** Python with `pandas`, `pyarrow`, and `deltalake==1.6.2` (e.g. `pip install pandas pyarrow deltalake==1.6.2`). **Pin nötig** (gemessen 29.09.2026): `deltalake` 1.6.6 schreibt Partitionspfade im `_delta_log` URL-kodiert (`Fiscal%20Year=…`); `fn_DeltaCurrentFiles` findet die Dateien dann nicht (spaltenlose Tabelle), siehe `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md`. Ein Neulauf überschreibt die geholten Showdaten mit einem neuen Datensatz (siehe oben). Delta Lake format is optional but recommended for date-partitioned facts. The script reads existing gold dimensions (dim_org, dim_date, dim_product, dim_customer) when present to align keys.

**Location:** `showcases/aurora_group/data/scripts/` — orchestrator; output in sibling folder `gold/`. Operations and supply_chain are delegated to `gold/generate_operations_gold.py` and `gold/generate_supply_chain_gold.py` (realistic names, seasonality, full 2020–2024). For RLS, run `py showcases/aurora_group/data/gold/generate_security_user_org.py` (generates `security_user_org` from company org chart).

**Verifying fact coverage:** From repo root run `py showcases/aurora_group/data/gold/check_fact_coverage.py` to report row counts, date ranges (2020–2024), parquet file counts, and format (Delta/Parquet) per fact. Facts marked SPARSE (e.g. supply_chain with only 60 month-ends) can be refreshed by re-running the orchestrator or `--domain supply_chain`. Facts with multiple parquet files (MULTI) must use `Table.Combine` in the semantic model M partition (e.g. fact_sales, fact_experience).

## Data Format

**Delta Lake format:** Date-partitioned facts (fact_sales, fact_accounts_payable, fact_accounts_receivable, fact_cash_position, fact_cash_flow, fact_inventory, fact_cogs, fact_fulfillment, fact_stockout, fact_forecast, fact_ops, fact_ops_failures, fact_maintenance, fact_quality, fact_experience) are written as Delta Lake when `deltalake` package is available. This enables partition pruning and better query performance.

**Fiscal Year partitioning:** All date-partitioned facts use `partition_by=["Fiscal Year"]`, creating folder structure `Fiscal Year=2020/`, `Fiscal Year=2021/`, etc. The `Fiscal Year` column is derived from `DateKey` (first 4 characters) automatically by `write_fact_delta()`.

**TMDL pattern:** Semantic model uses `Table.Combine` pattern for all Delta-partitioned facts to read all parquet files under the fact folder (including subfolders like `Fiscal Year=YYYY/`). Example pattern:

```m
ParquetTables = Table.AddColumn(FilteredFiles, "Parquet", each Parquet.Document([Content])),
Combined = Table.Combine(ParquetTables[Parquet])
```

**Plain parquet facts:** fact_promo (no date dimension) and dimensions remain as single parquet files. These do not benefit from partitioning due to small size or lack of date dimension.

## Quick Reference

### Regenerate specific fact(s)

```powershell
# Single domain
py showcases/aurora_group/data/scripts/generate_aurora_gold.py --domain experience

# Multiple domains
py showcases/aurora_group/data/scripts/generate_aurora_gold.py --domain operations,supply_chain

# All domains
py showcases/aurora_group/data/scripts/generate_aurora_gold.py
```

### Verify fact format and coverage

```powershell
# Check all facts (rows, dates, format)
py showcases/aurora_group/data/gold/check_fact_coverage.py

# Full validation: coverage + optional regeneration + Stage 1 (run from repo root)
.\showcases\aurora_group\data\validate_delta_migration.ps1
.\showcases\aurora_group\data\validate_delta_migration.ps1 -Regenerate -Domain experience
.\showcases\aurora_group\data\validate_delta_migration.ps1 -Regenerate -SkipStage1
```

### Verify Delta format manually

```powershell
# Check if fact is Delta (has _delta_log folder)
Test-Path "showcases/aurora_group/data/gold/facts/fact_experience/_delta_log"

# List all Delta facts
Get-ChildItem "showcases/aurora_group/data/gold/facts" -Directory | 
    Where-Object { Test-Path (Join-Path $_.FullName "_delta_log") } | 
    Select-Object Name
```

### Troubleshooting

**Issue:** Fact shows as "Parquet" but should be Delta

- **Solution:** Ensure `deltalake` package is installed: `pip install deltalake==1.6.2` (pinned, see Prerequisites)
- Regenerate the fact: `py showcases/aurora_group/data/scripts/generate_aurora_gold.py --domain <domain>`

**Issue:** TMDL partition fails to load fact data

- **Solution:** Verify fact uses `Table.Combine` pattern (check fact_*.tmdl partition source)
- Ensure fact folder contains parquet files (check `Fiscal Year=YYYY/` subfolders for Delta)

**Issue:** Relationship missing in semantic model

- **Solution:** Check relationships.tmdl for the relationship
- Verify corresponding data contract documents the relationship
