<#
.SYNOPSIS
  Validate Fabric measure overlay YAML (structure and optional keys).
.DESCRIPTION
  Ensures the overlay file exists and can be loaded; entries may have dax_expression, format_string, dax_name, display_folder.
#>
Param(
  [string]$OverlayPath = "products/fabric/powerbi/specs/fabric_measure_overlay.yaml",
  [string]$RepoRoot
)

$ErrorActionPreference = "Stop"
$repo = if ($RepoRoot -and (Test-Path $RepoRoot)) { $RepoRoot } else { (Get-Location).Path }
$path = if ([System.IO.Path]::IsPathRooted($OverlayPath)) { $OverlayPath } else { Join-Path $repo $OverlayPath }

if (-not (Test-Path $path)) {
  Write-Host "Fabric overlay not found: $path (optional for tool-agnostic core)." -ForegroundColor Yellow
  exit 0
}

# Minimal check: file exists and is non-empty; detailed YAML validation would require Python/yq
$content = Get-Content -Raw -Path $path -ErrorAction Stop
if ([string]::IsNullOrWhiteSpace($content)) {
  Write-Host "validate_fabric_overlay: overlay file is empty." -ForegroundColor Red
  exit 1
}
# Quick sanity: should contain kpi_id-like keys (e.g. "sales." or "crm.")
if ($content -notmatch '[\w.]+\s*:\s*\r?\n') {
  Write-Host "validate_fabric_overlay: overlay does not look like kpi_id -> fields map." -ForegroundColor Red
  exit 1
}
Write-Host "OK: Fabric overlay present and non-empty: $path"
exit 0
