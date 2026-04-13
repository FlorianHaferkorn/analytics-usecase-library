Param(
  [switch]$StubOnly,
  [switch]$OverwriteExisting
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot   = Split-Path -Parent $scriptRoot

Set-Location $repoRoot

Write-Host "Generating measures for all use cases..." -ForegroundColor Cyan


# Korrigierter Pfad: Skript liegt direkt im selben Verzeichnis
$generator = Join-Path $scriptRoot "generate_tmdl_measures.ps1"
if (-not (Test-Path $generator)) {
  throw "Generator script not found: tooling/generation/generate_tmdl_measures.ps1"
}

$args = @()
if ($StubOnly)        { $args += "-StubOnly" }
if ($OverwriteExisting) { $args += "-OverwriteExisting" }

& $generator @args

