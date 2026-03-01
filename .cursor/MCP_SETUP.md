# Power BI Modeling MCP — Cursor Setup

This project is configured to use the **Power BI Modeling MCP** server so the Cursor agent can work with semantic models (TMDL, measures, relationships) and PBIP output.

## One-time install (Microsoft Power BI Modeling MCP)

1. **Download the MCP server** (VSIX from Marketplace):
   - URL pattern: `https://marketplace.visualstudio.com/_apis/public/gallery/publishers/analysis-services/vsextensions/powerbi-modeling-mcp/<version>/vspackage?targetPlatform=win32-x64`
   - Or install the [Power BI Modeling MCP VS Code extension](https://aka.ms/powerbi-modeling-mcp-vscode) and locate the extension folder.
2. **Extract:** Rename the downloaded `.vsix` to `.zip`, unzip to a folder (e.g. `C:\MCPServers\PowerBIModelingMCP`). The result is a versioned subfolder (e.g. `analysis-services.powerbi-modeling-mcp-0.1.9@win32-x64`).
3. **Exe path:** The server executable is at `...\<versioned-folder>\extension\server\powerbi-modeling-mcp.exe`. This project’s config uses the 0.1.9 win32-x64 path; if you use another version, update `.cursor/mcp.json`.
4. **If your path is different:** Edit `.cursor/mcp.json` and set `command` to your `powerbi-modeling-mcp.exe` path (use double backslashes in JSON).

## Config in this repo

- **MCP config:** `.cursor/mcp.json` — defines the `powerbi-modeling-mcp` server (command, args, env).
- **Restart Cursor** after changing `mcp.json` so the server is loaded.

## MCP developer loop (nach Implementierung)

**„Implementierung“** = Änderungen mit dem Power BI Modeling MCP (ConnectFolder, measures, tables, …), manuelle Edits an PBIP/TMDL/Report, **oder** ein Lauf der Pipeline (z. B. `orchestrate_full_model.ps1` oder `products/fabric/powerbi/orchestrator/orchestrate_full_model.ps1`). Nach jedem dieser Schritte gilt:

**Wenn du eine Implementierung abgeschlossen hast**, ist der nächste Schritt immer derselbe:

1. **Validierung ausführen und auf Ergebnis warten** (von Repo-Root):
   ```powershell
   .\tooling\pbi_validate_after_impl.ps1 -IncludeDesktopLogMinutes 10 -ResultFile .cursor/pbi_validate_result.json
   ```
   Ausgabe: JSON mit `success`, `errors[]`, `sources[]`. Exit-Code 0 = keine Fehler, 1 = Fehler.

2. **Entscheidung:**
   - **success === true:** Entwicklung beenden; Nutzer kurz bestätigen („Validierung bestanden“). Optional: Report in Power BI Desktop zur finalen Prüfung öffnen.
   - **success === false:** Fehler aus `errors` beheben (MCP und/oder Datei-Edits). **Learning Loop:** Jede neue Fehlerklasse als Zeile (Symptom | Cause | Fix) in [KNOWN_ERRORS_AND_FIXES.md](../internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md) eintragen. Danach Schritt 1 erneut ausführen. Wiederholen bis `success === true` oder max. Iterationen (z. B. 5).

3. **Nicht überspringen:** Die Implementierung gilt erst als abgeschlossen, wenn die Validierung bestanden ist oder du nach max. Iterationen abbrichst und den Nutzer informierst.

Details und gleicher Ablauf: [.cursor/rules/fabric-expert.mdc](rules/fabric-expert.mdc) (Abschnitt „Post-Implementation“).

## Knowledge base for error resolution (MCP workflow)

When the agent uses the Power BI Modeling MCP to fix model/report errors (e.g. after a Desktop error in `.cursor/pbi_errors.log` or a pipeline failure):

- **Load:** [internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md](../internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md) — errors and solutions (Symptom | Cause | Fix). Read it first to match known patterns.
- **Update:** After applying a fix for a **new** error class, add one row to the appropriate section of that file so the solution is persisted and the MCP workflow can reuse it next time.

## Using the MCP from the Cursor agent (learning loop)

For Fabric/Power BI development, the agent should use the registered MCP:

- **Server ID for `call_mcp_tool`:** `powerbi-modeling-mcp`
- **Typical tools:** `connection_operations` (ConnectFolder to PBIP definition path), `model_operations` (Get, ExportTMDL), `measure_operations` (List, Create, Update, ExportTMDL), `table_operations`, `relationship_operations`.
- **Before calling:** Read the tool schema from `mcps/` (e.g. `mcps/project-0-analytics-usecase-library-powerbi-modeling-mcp/tools/<tool_name>.json`) to get the correct `request` shape.
- **Rule:** [.cursor/rules/fabric-expert.mdc](rules/fabric-expert.mdc) instructs the agent to use this MCP for semantic model work.

## Using it with this project’s PBIP output

After running the pipeline (e.g. `.\tooling\powerbi_mcp\orchestrate_full_model.ps1 -UseCase COM-001`), you can connect the MCP to this repo’s semantic models:

- **PBIP semantic model (TMDL):**  
  In Cursor/Copilot chat, use the MCP’s **ConnectToPBIP** prompt (or equivalent) and pass the path to the **definition** folder of the PBIP, e.g.:
  - `products/fabric/powerbi/dist/Commercial.SemanticModel/definition`
  - Or the full absolute path to that folder on your machine.

- **Power BI Desktop:**  
  If you open a `.pbip` in Power BI Desktop, you can connect with:  
  `Connect to '[Report or Model Name]' in Power BI Desktop`

## Optional: customize `.cursor/mcp.json`

| Goal | Change |
|------|--------|
| Read-only (no model edits) | Add `"--readonly"` to `args`. |
| Skip confirmation prompts | Add `"--skipconfirmation"` to `args`. Use only if you trust operations and have backups. |
| Fabric workspace auth | Set `"PBI_MODELING_MCP_ACCESS_TOKEN": "<token>"` in `env`. |

## References

- [Power BI Modeling MCP (GitHub)](https://github.com/microsoft/powerbi-modeling-mcp)
- [Power BI MCP (Microsoft Learn)](https://learn.microsoft.com/en-us/power-bi/developer/mcp/)
- Project orchestration: `tooling/powerbi_mcp/README.md`  
- Implementation cheatsheet (MCP tools): `products/fabric/powerbi/orchestrator/IMPLEMENTATION_CHEATSHEET.md`
