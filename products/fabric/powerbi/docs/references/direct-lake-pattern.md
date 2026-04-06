# Direct Lake Pattern — Semantic Model Authoring

> Reference for generating and managing Direct Lake semantic models in TMDL.  
> Companion to: `tmdl-advanced-features.md`, `fabric-api-core.md`

---

## What Direct Lake Is

Direct Lake is a partition mode where Power BI reads Delta tables directly from OneLake without importing or caching data. It combines Import-mode query speed with Direct Query-mode freshness.

**Requirements:**
- Fabric Premium or Trial capacity (not Pro)
- Delta tables in a Fabric Lakehouse (Gold layer, `dbo` schema)
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
- `schemaName` = always `dbo` for Fabric Lakehouse
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
| Schema is always `dbo` | Fabric Lakehouse exposes all tables under the `dbo` schema. |
| Calculated tables are Import | `_Measures` and `_ActionReady_Logic` remain as Import-mode M partitions. |
| Fabric capacity required | Direct Lake requires Fabric Premium/Trial. Falls back to DirectQuery on Pro capacity (much slower). |

---

## Fallback to DirectQuery

If Direct Lake can't read a partition directly (e.g., too many Delta files, unsupported type), Fabric automatically falls back to DirectQuery via the Lakehouse SQL endpoint. This is slower but transparent. To avoid fallback:
- Run `OPTIMIZE` on large Delta tables to compact files
- Keep Delta log clean (run `VACUUM` periodically)
- Monitor fallback via Fabric monitoring hub

---

## Relationship to Import Mode

Measures, relationships, RLS, and calculation groups are **identical** between Import and Direct Lake. Only the partition block differs. The `_Measures` table pattern works unchanged.

*End of reference*
