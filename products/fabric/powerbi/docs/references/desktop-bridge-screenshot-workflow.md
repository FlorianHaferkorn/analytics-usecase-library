# Desktop Bridge Screenshot Workflow (R4.1)

> Implements `UMSETZUNGSPLAN_REPORT_EXZELLENZ.md` Cut C4 / **R4.1 Bridge-Workflow**.
> Closes the gap the plan calls out explicitly: structural PBIR validation
> (Tier 0/1 checks, the fab-inspector BPA rules, the report scorecard) proves a
> report is *well-formed* — it cannot prove a report *renders correctly*
> (overlap, truncation, illegible text). Only a real Power BI Desktop render
> can prove that.

## Status: maintainer action required, not yet executed

This workflow is **built but not yet run**. The Power BI Desktop Bridge is a
local-only, named-pipe IPC server hosted inside the Desktop process — there is
**no remote access**, so it cannot be exercised from CI, this repo's
agent sandbox, or any headless environment. R1.6 already confirmed this (see
`UMSETZUNGSPLAN_REPORT_EXZELLENZ.md` ledger, R1.6 row). The script and this
doc are built directly from Microsoft's own official documentation (cited
below) — every command is copied verbatim from an official source, nothing is
guessed — but **the script itself has never been executed**, because doing so
requires Windows + a running Power BI Desktop, neither of which this session
has. The DoD for R4.1 (*"vom Maintainer einmal erfolgreich ausgeführt —
COM-002-Screenshot liegt vor"*) is explicitly a maintainer action.

## Prerequisites (one-time, on the maintainer's Windows workstation)

1. **Windows**, Power BI Desktop installed and running.
2. **Enable the bridge preview feature** in Desktop: `File` → `Options and
   Settings` → `Options` → `Preview Features` → check **"Enable external tool
   access to Power BI Desktop through secure local APIs"**. Restart Desktop.
3. **Node.js 20+** (the script installs the CLI itself if missing, but Node
   must already be present).

## One-liner

From the repo root, in PowerShell 7 (`pwsh`), with the target report already
open (or not — the script opens it):

```powershell
.\products\fabric\powerbi\tooling\desktop_bridge_screenshot.ps1 `
  -PbipPath "products\fabric\powerbi\dist\COM-002_Margin_Price_Performance.Report"
```

The script:

1. Installs `@microsoft/powerbi-desktop-bridge-cli` (`powerbi-desktop` on
   PATH) if not already present.
2. `powerbi-desktop open "<path>"` — opens the report in Desktop.
3. `powerbi-desktop status` — prints running Desktop instances; you enter the
   PID for the target report (the exact `status` output shape isn't verified
   from this session, so the script asks rather than guessing a parse).
4. `powerbi-desktop reload --pid <pid> --wait-seconds 60` — applies the
   current on-disk PBIR state.
5. `powerbi-desktop screenshot-all --pid <pid> --output-dir <dir>` — captures
   every page as PNG into
   `internal/metrics/desktop_screenshots/<ReportName>/<timestamp>/`
   (gitignored — see below).

## What to do with the screenshot

`internal/metrics/desktop_screenshots/` is **not committed** (binary PNGs
don't belong in git history). For the R4.1 DoD, attach or paste the COM-002
screenshot into the PR description or the plan ledger entry as proof of
execution, then update `UMSETZUNGSPLAN_REPORT_EXZELLENZ.md`'s R4.1 row with
the date and a link/reference to where the screenshot lives.

## Troubleshooting

Copied from Microsoft's official `powerbi-report-authoring` skill (see
References below):

| Symptom | Cause | Fix |
|---|---|---|
| "Bridge not_connected" | No Desktop instance found | Run `powerbi-desktop open` or start Desktop manually; confirm the preview feature is enabled. |
| `AMBIGUOUS_DESKTOP_INSTANCE` | Multiple Desktop windows open | Rerun `powerbi-desktop status`, identify the correct PID, pass `-ProcessId <pid>` explicitly. |
| `hasUnsavedChanges: true` in status | Unsaved changes block reload | Save or discard the Desktop UI changes, rerun status, then retry. |
| Timeout on reload/screenshot | Exceeded retry budget | Confirm `bridgeStatus: "connected"` via status; retry once; raise `-WaitSeconds`. |
| `ReportDefinitionValidationFailed` | Desktop rejected the PBIR | Fix with `powerbi-report-author validate` (see `powerbi-report-author-cli.md`), then reload. |

## Follow-ups (not in R4.1's scope)

- **17/17 rollout**: this script targets one report per invocation
  (matches the plan's "Dokumentierter Einzeiler" DoD). Looping it across all
  17 reports is a natural R5.1-adjacent follow-up once the single-report flow
  is confirmed working for real — premature to build blind before the first
  real run.
- **R4.2 (LLM-Judge-Abnahme)** consumes these screenshots as its input.

## References

| Source | What it gave us |
|---|---|
| [Power BI Desktop Bridge overview (Microsoft Learn)](https://learn.microsoft.com/power-bi/developer/agentic/power-bi-desktop-bridge-overview) | Preview feature toggle, named-pipe/JSON-RPC protocol, `bridge.manifest` discovery, official reference `Test-DesktopBridge.ps1` (raw protocol, not used directly here — the npm CLI wraps it) |
| [microsoft/skills-for-fabric — powerbi-report-authoring SKILL.md](https://github.com/microsoft/skills-for-fabric/blob/main/skills/powerbi-report-authoring/SKILL.md) | The exact `powerbi-desktop` CLI command surface (`open`, `status`, `reload --pid`, `screenshot`/`screenshot-all --pid --output-dir`), recommended operation order, troubleshooting table |
| `powerbi-report-author-cli.md` (this folder) | The companion offline validation CLI (Tier 1 oracle, R3.1/R3.2) — run before reload per the recommended operation order |
| `UMSETZUNGSPLAN_REPORT_EXZELLENZ.md` | R4.1 task definition, R1.6 prior finding that the bridge exists but is sandbox-inaccessible |
