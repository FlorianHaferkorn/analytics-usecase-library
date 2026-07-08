# .tools — External Tool Binaries

Binaries are **not committed**. Download them via the scripts below before running the Fabric validation pipeline.

## pbi-tools (Windows only)

Required version: **1.2.0** (see `pbi-tools.lock` for SHA-256).

```powershell
# Download pbi-tools and .NET runtime (run from repo root)
.\.tools\dotnet-install.ps1
# pbi-tools ZIP will be extracted to .tools/pbi-tools/
Invoke-WebRequest -Uri "https://github.com/pbi-tools/pbi-tools/releases/download/1.2.0/pbi-tools.core.1.2.0_win-x64.zip" `
  -OutFile ".tools\pbi-tools.core.1.2.0_win-x64.zip"
Expand-Archive ".tools\pbi-tools.core.1.2.0_win-x64.zip" -DestinationPath ".tools\pbi-tools\" -Force
```

The CI pipeline (`run_fabric_checks.ps1`) validates the binary hash against `pbi-tools.lock` before use and aborts if it mismatches.

## fab-inspector (cross-platform, PBI-Inspector V2)

Required version: **v3.4.0** (see `fab-inspector.lock`; `sha256` is a placeholder
until the first real CI download populates it — update it then, mirroring the
`pbi-tools.lock` bootstrap). Runs our own JSON-Logic BPA rules
(`products/fabric/powerbi/tooling/validation/fab-inspector-rules.json`) via
`check_fab_inspector.ps1`. See
`docs/architecture/r3-2-fab-inspector-integration.md` for why this tool was
chosen over the Windows-only, closed-source `pbir-cli`.

```powershell
# Download and extract (run from repo root; adjust RID for your platform,
# e.g. linux-x64-FabInspCLI.zip on Linux/CI, osx-x64/osx-arm64 on macOS)
Invoke-WebRequest -Uri "https://github.com/NatVanG/fab-inspector/releases/download/v3.4.0/win-x64-FabInspCLI.zip" `
  -OutFile ".tools\fab-inspector.zip"
Expand-Archive ".tools\fab-inspector.zip" -DestinationPath ".tools\fab-inspector\" -Force
```

`check_fab_inspector.ps1` resolves the binary from `$env:FAB_INSPECTOR_EXE`
(CI), then PATH, then `.tools/fab-inspector/**/*.exe`, and skips gracefully
(exit 0) when none is found locally — unless `ENABLE_FAB_INSPECTOR_CHECKS=1`.

## .NET Runtime

The `dotnet/` folder is populated by `dotnet-install.ps1`. Required by pbi-tools on environments without .NET 8 in PATH.

## Ignored paths

`.gitignore` excludes:
- `.tools/pbi-tools/` (extracted binaries)
- `.tools/fab-inspector/` (extracted binaries)
- `.tools/dotnet/` (.NET runtime)
- `.tools/*.zip` (downloaded archives)
