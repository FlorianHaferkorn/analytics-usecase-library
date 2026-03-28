# Fabric Expert (Power BI / Microsoft Fabric adapter)

When editing under `products/fabric/powerbi/` or Fabric TMDL/DAX artifacts, you are in **Fabric adapter** context. This product is the reference implementation of the adapter contract.

## Adapter contract

- See [products/adapters/README.md](products/adapters/README.md): build, validate, deploy. This adapter consumes IR (and Core ABI); it does not parse `core/` directly during build.

## PBI error knowledge base (MCP / agent)

When diagnosing or fixing PBI/PBIP errors (from `.cursor/pbi_errors.log`, `build_errors.json`, or MCP operations):

- **Read first:** [internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md](../../internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md) — single source for known errors and solutions (Symptom | Cause | Fix).
- **After fixing a new error class:** Add a row to the appropriate table in that file so the solution is stored and the MCP workflow can reuse it.

## Power BI Modeling MCP (development)

Use the **Power BI Modeling MCP** registered in Cursor (`.cursor/mcp.json`, server: `powerbi-modeling-mcp`) for semantic model work.

**Nach Abschluss einer Implementierung (MCP oder manuell):** Als nächsten Schritt immer die Post-Implementation-Validierung ausführen (Abschnitt „Post-Implementation“ unten). Implementierung erst als fertig betrachten, wenn Validierung bestanden oder nach max. Iterationen abgebrochen.

- **Connect to PBIP:** Before model/measure/table operations, connect to the repo’s dist output via `connection_operations` with `operation: "ConnectFolder"` and `folderPath` = path to the **definition** folder (e.g. `products/fabric/powerbi/dist/Commercial.SemanticModel/definition` or absolute path).
- **Tools:** Prefer MCP where applicable: `model_operations` (Get, ExportTMDL), `measure_operations` (List, Create, Update, ExportTMDL), `table_operations`, `relationship_operations`, `connection_operations` (ConnectFolder, ListConnections). Always read the tool schema in `mcps/<server>/tools/<name>.json` before calling `call_mcp_tool`.
- **Ref:** [.cursor/MCP_SETUP.md](.cursor/MCP_SETUP.md), [products/fabric/powerbi/orchestrator/IMPLEMENTATION_CHEATSHEET.md](products/fabric/powerbi/orchestrator/IMPLEMENTATION_CHEATSHEET.md).

## Rules and skills

- **TMDL and DAX:** Follow [tmdl-dax.mdc](.cursor/rules/tmdl-dax.mdc) (tabs only, measure syntax, diagram layout).
- **Skill:** fabric-powerbi-validation — use when changing measures, TMDL, or report layout.

## Post-Implementation: Validierung, Loop, Learning

**„Implementierung“** = Nutzung des Power BI Modeling MCP (z. B. ConnectFolder, measure_operations), manuelle Änderungen an PBIP/TMDL/Report, **oder** ein Lauf der Orchestrator-Pipeline (z. B. `orchestrate_full_model.ps1`). Nach jedem dieser Schritte:

**Nach Abschluss einer Implementierung** gilt:

1. **Validierung ausführen und auf Ergebnis warten:**
   ```powershell
   .\tooling\pbi_validate_after_impl.ps1 -IncludeDesktopLogMinutes 10 -ResultFile .cursor/pbi_validate_result.json
   ```
   Das Skript liefert JSON (stdout + optional ResultFile): `success`, `errors[]`, `sources[]`. Exit-Code 0 = keine Fehler, 1 = Fehler.

2. **Auswertung:**
   - **success === true:** Entwicklung beenden; Nutzer kurz informieren („Validierung bestanden, Implementierung abgeschlossen“). Optional hinweisen: Report in Power BI Desktop öffnen zur finalen Prüfung.
   - **success === false:** Fehler aus `errors` auswerten; mit MCP und/oder Datei-Edits beheben. **Learning Loop:** Jede neue Fehlerklasse als Zeile (Symptom | Cause | Fix) in [KNOWN_ERRORS_AND_FIXES.md](../../internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md) in der passenden Sektion eintragen. Anschließend Schritt 1 erneut ausführen (Validierung). Wiederholen bis `success === true` oder maximale Iterationen (z. B. 5); bei Abbruch Nutzer informieren und offene Fehler nennen.

3. **Nicht überspringen:** Diese Validierung und die Entscheidung (Loop vs. Ende) sind Teil des Implementierungsabschlusses; nicht „nur“ Fabric-Checks manuell laufen lassen, sondern das Ergebnis explizit auswerten und ggf. nachfixen.

## After making changes (single run)

Run Fabric validation from repo root:

```powershell
.\products\fabric/powerbi\tooling\run_fabric_checks.ps1
```

Stage 1 (`. \tooling\run_stage1_checks.ps1`) still applies for any changes that touch core or cross-references; for Fabric-only artifact edits, Fabric checks are the primary gate.

## Scope

- `products/fabric/powerbi/` — tooling, dist, reports, semantic models.
- Future tool adapters (e.g. Tableau, Looker) get their own expert rules under `.cursor/rules/<tool>-expert.mdc`.
