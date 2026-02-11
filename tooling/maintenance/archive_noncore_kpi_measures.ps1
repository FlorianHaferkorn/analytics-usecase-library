Param(
  [string]$AuditPath = '_internal/reviews/missing_kpi_dependency_audit.md',
  [string]$DomainsRoot = 'semantic_models/domains'
)

$ErrorActionPreference = 'Stop'

function Resolve-RepoPath {
  param([string]$ProvidedPath,[string]$DefaultRelative)
  $repo = (Get-Location).Path
  if ($ProvidedPath) {
    if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
    $candidate = Join-Path -Path $repo -ChildPath $ProvidedPath
    if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
  }
  if ($DefaultRelative) {
    $fallback = Join-Path -Path $repo -ChildPath $DefaultRelative
    if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
  }
  return $null
}

function Ensure-ArchiveFile {
  param([string]$ArchivePath,[string]$Domain)
  if (Test-Path $ArchivePath) { return }
  $header = @(
    ('# Measure Dictionary Archive - ' + $Domain),
    '',
    'Schema: see `/semantic_models/Domain_Measure_Dictionary_Schema.md`',
    '',
    '```yaml',
    '```'
  )
  $header | Set-Content -Path $ArchivePath
}

function Append-ToArchive {
  param([string]$ArchivePath,[string[]]$Blocks)
  $nl = [Environment]::NewLine
  $content = Get-Content -Raw -Path $ArchivePath
  $match = [regex]::Match($content, '(?s)```yaml(.*?)```')
  if (-not $match.Success) { throw ('Archive file missing yaml block: ' + $ArchivePath) }
  $pre = $content.Substring(0, $match.Index)
  $post = $content.Substring($match.Index + $match.Length)
  $body = $match.Groups[1].Value.TrimStart([char]13,[char]10).TrimEnd([char]13,[char]10)
  $open = ('```yaml' + $nl)
  $close = ($nl + '```')

  $newBody = $body.TrimEnd()
  foreach ($block in $Blocks) {
    if ($newBody.Length -gt 0) { $newBody += $nl }
    $newBody += $block.TrimEnd()
    $newBody += $nl
  }
  $newContent = $pre + $open + $newBody.TrimEnd() + $close + $post
  Set-Content -Path $ArchivePath -Value $newContent
}

$auditPath = Resolve-RepoPath -ProvidedPath $AuditPath -DefaultRelative '_internal/reviews/missing_kpi_dependency_audit.md'
$domainsRoot = Resolve-RepoPath -ProvidedPath $DomainsRoot -DefaultRelative 'semantic_models/domains'
if (-not $auditPath) { throw 'Missing audit file. Provide -AuditPath.' }
if (-not $domainsRoot) { throw 'Domains root not found. Provide -DomainsRoot.' }

$missingSet = @{}
foreach ($line in Get-Content -Path $auditPath) {
  if ($line -match '^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*no\s*\|') {
    $id = $matches[1]
    if ($id) { $missingSet[$id.Trim()] = $true }
  }
}
Write-Host ("Missing KPI ids to archive: {0}" -f $missingSet.Count)

$dictFiles = Get-ChildItem -Path $domainsRoot -Recurse -Filter 'Measure_Dictionary_*.md'
foreach ($file in $dictFiles) {
  $nl = [Environment]::NewLine
  $content = Get-Content -Raw -Path $file.FullName
  $match = [regex]::Match($content, '(?s)```yaml(.*?)```')
  if (-not $match.Success) { continue }
  $body = $match.Groups[1].Value.TrimStart([char]13,[char]10).TrimEnd([char]13,[char]10)
  $pre = $content.Substring(0, $match.Index)
  $post = $content.Substring($match.Index + $match.Length)
  $open = ('```yaml' + $nl)
  $close = ($nl + '```')

  $blockMatches = [regex]::Matches($body, '(?ms)^-\s*measure_name\s*:.*?(?=^\s*-\s*measure_name\s*:|\z)')
  if ($blockMatches.Count -eq 0) { continue }

  $kept = New-Object System.Collections.Generic.List[string]
  $moved = New-Object System.Collections.Generic.List[string]

  foreach ($matchBlock in $blockMatches) {
    $blockText = $matchBlock.Value.TrimEnd()
    $kpiMatch = [regex]::Match($blockText, '(?m)^\s*kpi_id_ref\s*:\s*([A-Za-z0-9_.-]+)\s*$')
    $kpiId = if ($kpiMatch.Success) { $kpiMatch.Groups[1].Value } else { '' }
    if ($kpiId -and $missingSet.ContainsKey($kpiId)) {
      $moved.Add($blockText) | Out-Null
    } else {
      $kept.Add($blockText) | Out-Null
    }
  }

  if ($moved.Count -eq 0) { continue }

  $newBody = ($kept -join ($nl + $nl)).TrimEnd()

  $newContent = $pre + $open + $newBody.TrimEnd() + $close + $post
  Set-Content -Path $file.FullName -Value $newContent

  $domain = Split-Path -Path $file.DirectoryName -Leaf
  $archivePath = Join-Path $file.DirectoryName ('Measure_Dictionary_' + $domain + '_Archive.md')
  Ensure-ArchiveFile -ArchivePath $archivePath -Domain $domain
  Append-ToArchive -ArchivePath $archivePath -Blocks $moved
  Write-Host ("Archived {0} measure(s) in {1}" -f $moved.Count, $file.FullName)
}

Write-Host ('Archived KPI measures not required for core. Audit source: ' + $auditPath)
