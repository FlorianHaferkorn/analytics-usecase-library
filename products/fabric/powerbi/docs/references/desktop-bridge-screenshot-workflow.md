# Desktop Bridge Screenshot Workflow (R4.1)

> Implements `UMSETZUNGSPLAN_REPORT_EXZELLENZ.md` Cut C4 / **R4.1 Bridge-Workflow**.
> Closes the gap the plan calls out explicitly: structural PBIR validation
> (Tier 0/1 checks, the fab-inspector BPA rules, the report scorecard) proves a
> report is *well-formed* — it cannot prove a report *renders correctly*
> (overlap, truncation, illegible text). Only a real Power BI Desktop render
> can prove that.

## Status: real Desktop runs in progress, DoD not yet met

The Power BI Desktop Bridge is a local-only, named-pipe IPC server hosted
inside the Desktop process — there is **no remote access**, so it cannot be
exercised from CI, this repo's agent sandbox, or any headless environment.
R1.6 already confirmed this (see `UMSETZUNGSPLAN_REPORT_EXZELLENZ.md` ledger,
R1.6 row). The script and this doc are built from Microsoft's own official
documentation plus the shipped CLI source where the docs don't cover it —
nothing here is guessed, but every claim about real Desktop behavior is only
as good as the maintainer's actual runs. As of the latest real run
(2026-07-15): the bridge CLI installs and connects correctly, opening
COM-002 no longer hits the `PFE_TM_COLUMN_SORTED_BY_INVALID` TOM error
(R1.6's `dim_pvm_driver.tmdl` fix confirmed working in real Desktop), and the
script now uses a per-page `screenshot` workflow instead of `reload` +
`screenshot-all` (see below for why). The DoD for R4.1 (*"vom Maintainer
einmal erfolgreich ausgeführt — COM-002-Screenshot liegt vor"*) is not yet
met — a screenshot has not yet been produced and attached.

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
4. Reads the report's own `definition/pages/pages.json` (`pageOrder`) to get
   the exact page ids — no bridge call needed, it's already on disk.
5. `powerbi-desktop screenshot <page-id> --pid <pid> --output <file> --wait-seconds 60`
   — once per page — captures each page as PNG into
   `internal/metrics/desktop_screenshots/<ReportName>/<timestamp>/`
   (gitignored — see below).

**Why not `reload` + `screenshot-all`** (Microsoft's own documented order):
both depend on the CLI's `resolveReportDir()`, which only finds a **sibling**
`<Name>.Report` folder next to a `.pbip` file — it never checks whether the
`.pbip`'s own parent directory *is* the `.Report` folder. This repo's
documented PBIP layout (`PBIP_REPORT_STRUCTURE.md`) nests `Report.pbip`
*inside* `<UseCase>.Report/`, so `resolveReportDir()` always returns `null`
here and both commands fail with `REPORT_DIR_REQUIRED` — confirmed against
the shipped CLI source (`dist/index.js`), and there is no flag to override
it. Restructuring the repo's PBIP layout to match the CLI's assumption is
out of scope (would touch all 17 reports plus every tool that depends on the
current layout). The singular `screenshot <page-id>` command never calls
`resolveReportDir()`, so it works regardless of layout. Practical
consequence: this script never calls `reload`, so if you edit PBIR locally
while Desktop is already open against a report, close and reopen Desktop for
it before rerunning the script — reload cannot be made to work here.

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
| Timeout on `screenshot` | Exceeded retry budget | Confirm `bridgeStatus: "connected"` via status; retry once; raise `-WaitSeconds`. |
| `ReportDefinitionValidationFailed` | Desktop rejected the PBIR | Fix with `powerbi-report-author validate` (see `powerbi-report-author-cli.md`), then reopen Desktop for this report and rerun the script. |
| `powerbi-desktop open` fails with "Power BI Desktop executable was not found" even though Desktop is installed and running | The CLI's own executable auto-discovery only checks traditional MSI/EXE install roots -- it never checks the Microsoft Store package path pattern (`...\WindowsApps\Microsoft.MicrosoftPowerBIDesktop_<version>_x64__8wekyb3d8bbwe\bin\PBIDesktop.exe`), so Store installs aren't found. Confirmed by inspecting the shipped `@microsoft/powerbi-desktop-bridge-cli` source directly (undocumented in the public docs); the CLI honors `$env:PBI_DESKTOP_PATH` first, before its own discovery. | The script now auto-detects a Store install and sets `$env:PBI_DESKTOP_PATH` before calling `open`. If your install lives somewhere else entirely, set `$env:PBI_DESKTOP_PATH` to the real `PBIDesktop.exe` path yourself before running the script. |
| `reload`/`screenshot-all` fail with `REPORT_DIR_REQUIRED` ("reload requires the selected Desktop instance to have a PBIP/PBIR current file") even though `status` shows a valid `.pbip` `currentFilePath` | The CLI's `resolveReportDir()` only looks for a sibling `<Name>.Report` folder next to a `.pbip`; this repo nests `Report.pbip` inside `<UseCase>.Report/`, so it always returns `null` here. Confirmed against the shipped CLI source; no override flag exists. | Not applicable to this script anymore -- it uses per-page `screenshot <page-id>` instead, which bypasses `resolveReportDir()` entirely. If you're calling the CLI directly outside this script, use `screenshot <page-id> --pid <pid> --output <file>` per page from `definition/pages/pages.json`'s `pageOrder`, not `reload`/`screenshot-all`. |

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
| `@microsoft/powerbi-desktop-bridge-cli` shipped source (`dist/index.js`, decompiled from the published npm tarball) | Ground truth for behavior the public docs don't cover: `$env:PBI_DESKTOP_PATH` executable override, `resolveReportDir()`'s sibling-folder-only logic (and why it fails against this repo's nested PBIP layout), and the singular `screenshot <page-id>` command's full flag set (`--pid`, `--output`, `--scale`, `--wait-seconds`) |
| `powerbi-report-author-cli.md` (this folder) | The companion offline validation CLI (Tier 1 oracle, R3.1/R3.2) — run before opening in Desktop per the recommended operation order |
| `UMSETZUNGSPLAN_REPORT_EXZELLENZ.md` | R4.1 task definition, R1.6 prior finding that the bridge exists but is sandbox-inaccessible |
