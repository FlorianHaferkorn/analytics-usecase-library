<#
.SYNOPSIS
  Export a customer-safe package from the monorepo.
.DESCRIPTION
  Produces a curated output that excludes maintainer-only areas (`tooling/`, `internal/`, `.local/`).
  Intended for maintainers/delivery teams. Run from repository root.
#>
Param(
  [string]$OutDir = "dist/customer_exports",
  [string[]]$IncludeProducts = @("fabric/powerbi"),
  [switch]$IncludeShowcases,
  [switch]$Zip
)

$ErrorActionPreference = "Stop"

function Ensure-Dir { param([string]$Path) if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Path $Path -Force | Out-Null } }

$repoRoot = (Get-Location).Path
$stamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$targetRoot = Join-Path $repoRoot $OutDir
Ensure-Dir $targetRoot

$pkgName = "actionready_package_$stamp"
$pkgDir = Join-Path $targetRoot $pkgName
Ensure-Dir $pkgDir

Write-Host "Exporting customer package to: $pkgDir" -ForegroundColor Cyan

# Core (tool-agnostic SSOT)
Copy-Item -Recurse -Force (Join-Path $repoRoot "core") (Join-Path $pkgDir "core")

# Docs entry (public navigation)
Copy-Item -Recurse -Force (Join-Path $repoRoot "docs") (Join-Path $pkgDir "docs")
Copy-Item -Force (Join-Path $repoRoot "README.md") (Join-Path $pkgDir "README.md")

# Selected products
Ensure-Dir (Join-Path $pkgDir "products")
foreach ($p in $IncludeProducts) {
  $src = Join-Path $repoRoot ("products\" + ($p -replace '/', [System.IO.Path]::DirectorySeparatorChar))
  if (-not (Test-Path $src)) { throw "Product not found: $src" }
  Copy-Item -Recurse -Force $src (Join-Path $pkgDir ("products\" + $p))
}

# Optional showcases (example implementations only)
if ($IncludeShowcases) {
  Copy-Item -Recurse -Force (Join-Path $repoRoot "showcases") (Join-Path $pkgDir "showcases")
}

# Hard exclusions (defense-in-depth): remove maintainer-only folders if copied by accident
$exclude = @("tooling", "internal", ".local", ".git", ".github")
foreach ($e in $exclude) {
  $path = Join-Path $pkgDir $e
  if (Test-Path $path) { Remove-Item -Recurse -Force $path }
}

if ($Zip) {
  $zipPath = Join-Path $targetRoot ($pkgName + ".zip")
  if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
  Compress-Archive -Path $pkgDir -DestinationPath $zipPath
  Write-Host "Zip written: $zipPath" -ForegroundColor Green
}

Write-Host "Export complete." -ForegroundColor Green

