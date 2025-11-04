param(
  [switch]$FailOnError
)

# Validates KPI catalog entries (YAML blocks) for unique IDs and allowed enums.
$allowedTypes = @('strategic','diagnostic','supporting')
$allowedCalc  = @('amount','rate','ratio','count')
$idRegex = '^[a-z0-9]+(\.[a-z0-9_]+)*$'

function Get-KpisFromCatalog {
  param([string]$File)
  $content = Get-Content -LiteralPath $File -Raw
  $matches = [regex]::Matches($content, "```yaml([\s\S]*?)```", 'Singleline')
  foreach ($m in $matches) {
    $yaml = $m.Groups[1].Value
    try { $items = $yaml | ConvertFrom-Yaml } catch { continue }
    if ($items -is [System.Collections.IEnumerable]) { $items } else { if ($items) { ,$items } }
  }
}

$repoRoot = Join-Path $PSScriptRoot '..' '..' '..' | Resolve-Path
$catalogRoot = Join-Path $repoRoot 'analytics-usecase-library' '_includes' 'kpi_catalog'

$errors = @()
$seen = @{}

Get-ChildItem -Path $catalogRoot -Filter *.md -File | ForEach-Object {
  $file = $_.FullName
  foreach ($k in (Get-KpisFromCatalog -File $file)) {
    $kid = [string]$k.kpi_id
    $kkey = [string]$k.kpi_key
    $ktype = [string]$k.kpi_type
    $cc = [string]$k.calc_type
    if (-not $kid) { $errors += "$file: missing kpi_id"; continue }
    if (-not $kkey) { $errors += "$file: $kid missing kpi_key" }
    if ($seen.ContainsKey($kid)) { $errors += "duplicate kpi_id: $kid ($file) also in $($seen[$kid])" } else { $seen[$kid] = $file }
    if ($ktype -and ($allowedTypes -notcontains $ktype)) { $errors += "$file: $kid invalid kpi_type '$ktype'" }
    if ($cc -and ($allowedCalc -notcontains $cc)) { $errors += "$file: $kid invalid calc_type '$cc'" }
    if (-not ($kid -match $idRegex)) { $errors += "$file: $kid invalid id format (regex $idRegex)" }
  }
}

if ($errors.Count -gt 0) {
  Write-Error "KPI Catalog validation failed:`n$(($errors -join "`n"))"
  if ($FailOnError) { exit 1 } else { exit 0 }
} else {
  Write-Host "KPI Catalog validation passed."
}

