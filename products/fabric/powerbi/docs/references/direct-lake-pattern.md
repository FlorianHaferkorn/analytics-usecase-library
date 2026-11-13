# Direct Lake Pattern — Semantic Model Authoring

> Reference for generating and managing Direct Lake semantic models in TMDL.  
> Companion to: `tmdl-advanced-features.md`, `fabric-api-core.md`

---

## What Direct Lake Is

Direct Lake is a partition mode where Power BI reads Delta tables directly from OneLake without importing or caching data. It combines Import-mode query speed with Direct Query-mode freshness.

**Requirements:**
- A Fabric capacity (F SKU, Premium P SKU or Trial). There is no Direct Lake on Pro or PPU workspaces.
- Delta tables in a Fabric Lakehouse (Gold layer). With a schema-enabled Lakehouse the table can sit in any schema; `dbo` is only the default schema.
- Tables must exist in Lakehouse before the semantic model can refresh

---

## TMDL Structure for Direct Lake

### `definition/expressions.tmdl` — the Lakehouse connection

```
expression DL_Lakehouse =
 let
  Source = AzureStorage.DataLake("https://onelake.dfs.fabric.microsoft.com/<WorkspaceId>/<LakehouseId>", [HierarchicalNavigation = true, Timeout = Duration.From(null)])
 in
  Source
 lineageTag: <guid>
 annotation PBI_NavigationStepName = DL_Lakehouse
 annotation PBI_ResultType = Table
```

- One named expression per model (not per table)
- `WorkspaceId` and `LakehouseId` are Fabric GUIDs — get them via `fab get` or Fabric portal URL
- Expression name `DL_Lakehouse` is convention; matches `expressionSource` in every partition

### `definition/tables/<table>.tmdl` — entity partition

```
table fact_sales
 lineageTag: <guid>

 column DateKey
  dataType: Int64
  sourceColumn: DateKey
  summarizeBy: none

 partition fact_sales = entity
  mode: directLake
  source
   entityName: fact_sales
   schemaName: dbo
   expressionSource: DL_Lakehouse
```

**Rules:**
- `entityName` = Delta table name in Lakehouse (usually same as TMDL table name)
- `schemaName` = the Lakehouse schema that holds the table. Lakehouses without schemas expose every table as `dbo`; schema-enabled Lakehouses (required for materialized lake views) use the real schema name, for example `sales_mlv`.
- `expressionSource` = name of the named expression in `expressions.tmdl`
- No `source =` block — entity partition uses `source` (no `=`)
- No M transforms — Direct Lake tables cannot have Power Query transformations

### `definition/model.tmdl` — no special Direct Lake config needed

`defaultPowerBIDataSourceVersion: PowerBI_V3` is required as usual. Direct Lake has no extra model-level flags.

---

## Generating Direct Lake Models with `table_ops.ps1`

### Option A — New model from data contract

Add `storage_mode`, `workspace_id`, `lakehouse_id` to the contract's `settings`:

```yaml
settings:
  storage_mode: DirectLake
  workspace_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  lakehouse_id: "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
```

Then run `CreateFromContract` with `-StorageMode DirectLake`:

```powershell
.\table_ops.ps1 -Operation CreateFromContract `
    -DataContractPath .\contracts\commercial.yaml `
    -TableName fact_sales `
    -StorageMode DirectLake `
    -DefinitionPath products\fabric\powerbi\dist\Commercial.SemanticModel\definition
```

The first table also writes `expressions.tmdl` automatically when IDs are resolved.

### Option B — Write the named expression explicitly

```powershell
.\table_ops.ps1 -Operation WriteDirectLakeExpression `
    -DefinitionPath products\fabric\powerbi\dist\Commercial.SemanticModel\definition `
    -WorkspaceId "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" `
    -LakehouseId "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
```

### Option C — Patch an existing Import-mode model to Direct Lake

Converts all Import-mode M partitions to entity partitions in one pass. Also rewrites `expressions.tmdl`.

```powershell
.\table_ops.ps1 -Operation PatchPartitionSourceToDirectLake `
    -DefinitionPath products\fabric\powerbi\dist\Commercial.SemanticModel\definition `
    -WorkspaceId "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" `
    -LakehouseId "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
```

Skips `_Measures` and `_ActionReady_Logic` (calculated tables — no data partition).

---

## Getting WorkspaceId and LakehouseId

```bash
# Workspace ID
WS_ID=$(fab get "MyWorkspace.Workspace" -q "id" | tr -d '"')

# Lakehouse ID
LH_ID=$(fab get "MyWorkspace.Workspace/CommercialGold.Lakehouse" -q "id" | tr -d '"')

echo "workspace_id: $WS_ID"
echo "lakehouse_id: $LH_ID"
```

Or from Fabric portal URL:
```
https://app.fabric.microsoft.com/groups/<WorkspaceId>/lakehouses/<LakehouseId>
```

---

## Import → Direct Lake Migration Sequence

```
1. Ensure Delta tables exist in Lakehouse (same names as TMDL table names)
2. Get WorkspaceId + LakehouseId (fab or portal)
3. Run PatchPartitionSourceToDirectLake
4. Validate TMDL: run validate_tmdl_style.sh
5. Import to Fabric: fab import "ws.Workspace/Model.SemanticModel" -i ./dist/Model.SemanticModel -f
6. Trigger full refresh: fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{"type":"Full"}'
7. Verify via DAX: fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/executeQueries" -X post -i '{"queries":[{"query":"EVALUATE ROW(\"RowCount\", COUNTROWS(fact_sales))"}]}'
```

---

## Constraints

| Constraint | Notes |
|---|---|
| No Power Query transforms | Entity partitions cannot have M query steps. Transformations must happen in the Lakehouse (notebooks/dataflows). |
| No `dataType: binary` | Binary columns are not supported in Direct Lake. |
| Delta tables must exist | A DirectLake model will fail to refresh if the Delta table doesn't exist in the Lakehouse. |
| Schema must match the Lakehouse | `schemaName` names the schema that holds the table. Only Lakehouses without schemas expose everything as `dbo`. |
| Calculated tables are Import | `_Measures` and `_ActionReady_Logic` remain as Import-mode M partitions. |
| Fabric capacity required | Direct Lake needs a Fabric capacity (F, P or Trial). A Pro or PPU workspace cannot host a Direct Lake model at all; there is no fallback to DirectQuery there. |
| No SQL views | Direct Lake on OneLake reads Delta tables only. Replace a view with a materialized lake view (GA September 2026) or keep that table in Import mode. |

---

## Fallback to DirectQuery

Fallback depends on the Direct Lake flavour, which is set by the source expression:

| Flavour | Source expression | Fallback |
|---|---|---|
| Direct Lake on OneLake (the pattern in this document) | `AzureStorage.DataLake("https://onelake.dfs.fabric.microsoft.com/<WorkspaceId>/<LakehouseId>")` | **None.** A query that exceeds a guardrail or hits an unframed table fails instead of falling back. |
| Direct Lake on SQL endpoint | `Sql.Database("<SQL endpoint connection string>", "<SQL endpoint ID>")` | Falls back to DirectQuery through the SQL endpoint when a guardrail is exceeded, when the source is a SQL view, or when SQL-side RLS/OLS/masking applies. Controlled by the model property `DirectLakeBehavior` (`Automatic`, `DirectLakeOnly`, `DirectQueryOnly`). |

To stay inside the guardrails of the capacity SKU (rows per table, model size in memory):
- Run `OPTIMIZE` on large Delta tables to keep the number of files and row groups low
- Run `VACUUM` periodically to keep the Delta log clean
- For Direct Lake on SQL endpoint, monitor fallback (for example with a DAX query trace or Performance Analyzer); with Direct Lake on OneLake, monitor failed queries instead

Sources (Microsoft Learn, checked 21.10.2026): [Direct Lake overview](https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview), [How Direct Lake works](https://learn.microsoft.com/fabric/fundamentals/direct-lake-how-it-works).

---

## Relationship to Import Mode

Measures, relationships, RLS, and calculation groups are **identical** between Import and Direct Lake. Only the partition block differs. The `_Measures` table pattern works unchanged.

*End of reference*
