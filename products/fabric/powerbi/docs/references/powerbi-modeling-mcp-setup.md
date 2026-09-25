# Power BI Modeling MCP — Setup and Developer Loop

The **Power BI Modeling MCP** server (Microsoft, server id `powerbi-modeling-mcp`) lets an
MCP-capable agent or client read and edit semantic models (TMDL, measures, tables,
relationships) — either this repo's PBIP output or a model open in Power BI Desktop.
When to use MCP vs. file edits / REST: see [`fabric-powerbi-authoring.md`](fabric-powerbi-authoring.md)
(MCP for fine-grained measure/column edits; not for structural changes such as new tables or partitions).

## One-time install (Windows)

1. **Download the server** (VSIX from the Visual Studio Marketplace):
   `https://marketplace.visualstudio.com/_apis/public/gallery/publishers/analysis-services/vsextensions/powerbi-modeling-mcp/<version>/vspackage?targetPlatform=win32-x64`
   — or install the [Power BI Modeling MCP VS Code extension](https://aka.ms/powerbi-modeling-mcp-vscode)
   and locate its extension folder.
2. **Extract:** rename the `.vsix` to `.zip` and unzip it, e.g. to `C:\MCPServers\PowerBIModelingMCP`.
   The result is a versioned subfolder, e.g. `analysis-services.powerbi-modeling-mcp-0.1.9@win32-x64`.
3. **Executable:** `<versioned-folder>\extension\server\powerbi-modeling-mcp.exe`.
4. **Register** the server in your MCP client's local configuration (location depends on the client;
   the file is machine-specific and is not committed). Reload/restart the client afterwards.

### Example configuration

Standard `mcpServers` JSON (adjust the path to your version; use double backslashes in JSON):

```json
{
  "mcpServers": {
    "powerbi-modeling-mcp": {
      "command": "C:\\MCPServers\\PowerBIModelingMCP\\analysis-services.powerbi-modeling-mcp-0.1.9@win32-x64\\extension\\server\\powerbi-modeling-mcp.exe",
      "args": ["--start"],
      "env": {}
    }
  }
}
```

### Options

| Goal | Change |
|------|--------|
| Read-only (no model edits) | Add `"--readonly"` to `args`. |
| Skip confirmation prompts | Add `"--skipconfirmation"` to `args`. Use only if you trust the operations and have backups. |
| Fabric workspace auth | Set `"PBI_MODELING_MCP_ACCESS_TOKEN": "<token>"` in `env` (never commit a token). |

## Connecting to this repo's models

- **PBIP semantic model (TMDL):** connect via `connection_operations` → `ConnectFolder` (or the
  server's *ConnectToPBIP* prompt) with the path to the model's **definition** folder, e.g.
  `products/fabric/powerbi/dist/Commercial.SemanticModel/definition` (absolute path also works).
  Other domains: `Experience`, `Finance`, `Operations`, `SupplyChain`.
- **Power BI Desktop:** with a `.pbip` open in Desktop, connect with
  `Connect to '[Report or Model Name]' in Power BI Desktop`.
- **Typical tools:** `connection_operations` (ConnectFolder, ListConnections), `model_operations`
  (Get, ExportTMDL), `measure_operations` (List, Create, Update, ExportTMDL), `table_operations`,
  `relationship_operations`.
- **Before calling a tool,** read its input schema as exposed by your MCP client — request shapes
  differ per operation.

The PBIP output is produced by the pipeline, e.g.
`.\products\fabric\powerbi\orchestrator\orchestrate_full_model.ps1 -UseCase COM-001`.

## Developer loop after implementation

**"Implementation"** = changes made via the Power BI Modeling MCP (ConnectFolder, measures,
tables, …), manual edits to PBIP/TMDL/report files, **or** a pipeline run
(`products/fabric/powerbi/orchestrator/orchestrate_full_model.ps1`). After each of these:

1. **Run validation and wait for the result** (from repo root):
   ```powershell
   .\products\fabric\powerbi\tooling\run_fabric_checks.ps1
   ```
   Exit code 0 = no errors, 1 = errors. If core artifacts or cross-references changed as well,
   run `.\tooling\quality\run_quality_gate.ps1` (Stage 1 + Fabric checks in one pass).
2. **Decide:**
   - **Passed:** finish; confirm briefly to the user ("Validierung bestanden"). Optionally open the
     report in Power BI Desktop for a final visual check.
   - **Failed:** fix the reported errors (MCP and/or file edits). **Learning loop:** add every new
     error class as a row (Symptom | Cause | Fix) to
     [`internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md`](../../../../../internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md),
     then repeat step 1 — until it passes or a maximum of ~5 iterations; on abort, tell the user
     which errors remain.
3. **Do not skip:** an implementation is only complete once validation passes, or after an
   explicit abort with the open errors reported.

**Local outputs** (Desktop error log, validation result JSON, etc.) go to the git-ignored
`.local/` directory at the repo root, e.g. `.local/pbi_errors.log`, `.local/pbi_validate_result.json`.
The former post-implementation wrapper `pbi_validate_after_impl.ps1` (JSON with `success`,
`errors[]`, `sources[]`, optional Desktop-log scan) is archived under
`internal/archive/phase2_experiments/tooling_scripts/`; if it is reactivated, write its result to
`.local/pbi_validate_result.json`.

## Knowledge base for error resolution

When using the MCP to fix model/report errors (e.g. a Desktop error in `.local/pbi_errors.log`
or a pipeline failure):

- **Load first:** `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` (Symptom | Cause | Fix) —
  match known patterns before analysing.
- **Update:** after fixing a **new** error class, add one row to the appropriate section so the
  solution is reused next time. Routing rules: `docs/agent/rules/learning-routing.md`.

## References

- [Power BI Modeling MCP (GitHub)](https://github.com/microsoft/powerbi-modeling-mcp)
- [Power BI MCP (Microsoft Learn)](https://learn.microsoft.com/en-us/power-bi/developer/mcp/)
- Implementation cheatsheet (MCP tools): `products/fabric/powerbi/orchestrator/IMPLEMENTATION_CHEATSHEET.md`
- Agent rule: `docs/agent/rules/fabric-expert.md`; skill: `docs/agent/skills/fix-pbi-report-errors.md`
