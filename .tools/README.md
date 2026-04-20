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

## .NET Runtime

The `dotnet/` folder is populated by `dotnet-install.ps1`. Required by pbi-tools on environments without .NET 8 in PATH.

## Ignored paths

`.gitignore` excludes:
- `.tools/pbi-tools/` (extracted binaries)
- `.tools/dotnet/` (.NET runtime)
- `.tools/*.zip` (downloaded archives)
