# Power BI Modeling MCP — Setup and Developer Loop

The **Power BI Modeling MCP** server (Microsoft, server id `powerbi-modeling-mcp`) lets an
MCP-capable agent or client read and edit semantic models (TMDL, measures, tables,
relationships) — either this repo's PBIP output or a model open in Power BI Desktop.
When to use MCP vs. file edits / REST: see [`fabric-powerbi-authoring.md`](fabric-powerbi-authoring.md)
(MCP for fine-grained measure/column edits; not for structural changes such as new tables or partitions).

## One authoring server, two deployments (Learn, read 29.09.2026)

Microsoft Learn now calls it the **Power BI Authoring MCP server**
([power-bi-authoring-mcp](https://learn.microsoft.com/power-bi/developer/mcp/power-bi-authoring-mcp)):

| | Local — **generally available** | Hosted — **preview** |
|---|---|---|
| What | this npm package, `stdio` | `https://api.fabric.microsoft.com/v1/mcp/powerbi/authoring`, Streamable HTTP |
| Reaches | Power BI Desktop, PBIP/TMDL on disk, Fabric workspaces | Fabric workspaces only |
| Auth | Entra interactive sign-in or **service principal** | Entra, as the signed-in user; tenant setting *Users can use the Power BI Model Context Protocol server endpoint* |
| Transactions / AS traces | yes | no |
| macOS | not supported | works |

This repo uses the **local** server: its models are PBIP/TMDL files under `dist/`, which the
hosted server cannot reach. Learn advises against registering both at once (overlapping tool
sets). For **end users asking questions of a model**, Learn recommends the **Fabric IQ MCP**
server, not the authoring server ([mcp-servers-overview](https://learn.microsoft.com/power-bi/developer/mcp/mcp-servers-overview)).

## Installation: npm package, pinned (since 29.09.2026)

The server ships as the npm package `@microsoft/powerbi-modeling-mcp` with native binaries for
`linux-x64`, `linux-arm64`, `win32-x64`, `win32-arm64` and `darwin-arm64` (npm metadata,
`npm view @microsoft/powerbi-modeling-mcp optionalDependencies`, 29.09.2026). The former route —
unpacking the VS Code VSIX by hand to a Windows `.exe` (version 0.1.9) — is obsolete.

**Pinned version: `1.0.0`** (`npm view @microsoft/powerbi-modeling-mcp version` → `1.0.0`,
29.09.2026). The pin is tracked for drift in Freelancing `research/upstream_pins.yaml`
(id `powerbi-modeling-mcp`). Raise it in one place — [`.mcp.json`](../../../../../.mcp.json) — and
note the measurement below again.

### Claude Code: project configuration

The repo root carries [`.mcp.json`](../../../../../.mcp.json) (Claude Code project scope; Claude
Code asks once per user before it starts a project server):

```json
{
  "mcpServers": {
    "powerbi-modeling-mcp": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@microsoft/powerbi-modeling-mcp@1.0.0", "--start"],
      "env": {}
    }
  }
}
```

Other MCP clients take the same `command`/`args`. Without `--start` the package does not serve
MCP: it prints a registration hint and waits for a key press (on a redirected console it ends
with `System.InvalidOperationException: Cannot read keys…`, measured 29.09.2026).

### Licence (EULA) — deliberately not accepted in the repo

Every tool call answers with *"The Power BI Authoring MCP EULA must be accepted before using this
tool"* until the EULA is accepted (measured 29.09.2026, three tools, all `isError: true`). The
committed configuration does **not** pass `--accept-eula`: accepting the licence is the user's
decision, not the repository's. Three ways, per the server's own message: call the server's
`accept_eula` tool in the session, set `PBI_MODELING_MCP_ACCEPT_EULA=true` in your own
environment, or add `--accept-eula` in a local, uncommitted client configuration. Licence text:
https://go.microsoft.com/fwlink/?LinkId=2381247.

### Measured under Linux (29.09.2026)

Environment: Linux x86_64, Node 22.22.2, `npx -y @microsoft/powerbi-modeling-mcp@1.0.0 --start`,
driven by a small stdio JSON-RPC client (initialize → tools/list → tools/call); EULA accepted via
`PBI_MODELING_MCP_ACCEPT_EULA=true` for the measurement only.

| Step | Result |
|---|---|
| `initialize` | answer after 2.3 s, `serverInfo.name = powerbi-authoring-local`, version `1.0.0` |
| `tools/list` | 21 tools (`connection_operations`, `database_operations`, `model_operations`, `table_operations`, `measure_operations`, `relationship_operations`, `dax_query_operations`, …) |
| `ConnectFolder` + `table_operations List` + `measure_operations List`, `dist/*.SemanticModel` | **3 of 5 load**: Commercial 19 tables / 54 measures / 22 relationships, Finance 23/69/30, Operations 16/53/15 |
| same, Experience and SupplyChain | **fail**: `'database.tmdl' not found` — both `definition/` folders carry no `database.tmdl` (the other three do) |

Second measurement for the three loading models: the counts equal the files on disk
(`ls definition/tables | wc -l`, `grep -c '^\s*measure '` over `tables/`, `grep -c '^relationship '`
over `definition/`) — 19/54/22, 23/69/30, 16/53/15.

What this does **not** show: the Power BI Desktop connection (Windows only), `dax_query_operations`
(needs a running engine — Desktop or a Fabric workspace; an offline TMDL folder has none), and
`ConnectFabric`/`DeployToFabric` (need a tenant and sign-in). Changes made through `ConnectFolder`
stay in memory until `database_operations ExportToTmdlFolder` — and `dist/` is generator output,
so the MCP is for reading and trying out; lasting changes go into the generators.

### Options

| Goal | Change |
|------|--------|
| Read-only (no model edits) | Add `"--readonly"` to `args`. |
| Skip confirmation prompts | Add `"--skipconfirmation"` to `args`. Use only if you trust the operations and have backups. |
| Fabric workspace auth | Set `"PBI_MODELING_MCP_ACCESS_TOKEN": "<token>"` in `env` of a **local** configuration (never commit a token). |

## Connecting to this repo's models

- **PBIP semantic model (TMDL):** connect via `connection_operations` → `ConnectFolder` with the
  path to the `.SemanticModel` folder or its `definition` subfolder (the server looks for
  `database.tmdl` in both), absolute path, e.g.
  `products/fabric/powerbi/dist/Commercial.SemanticModel`. Loads today: `Commercial`, `Finance`,
  `Operations`; `Experience` and `SupplyChain` lack `database.tmdl` (see measurement above).
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
