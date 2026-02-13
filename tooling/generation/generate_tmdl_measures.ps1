Param(
  [string[]]$UseCase,
  [string]$UseCasesRoot = "core/usecases",
  [string]$KpiCatalogRoot = "core/kpi_catalog",
  [string]$ActionCodesRoot = "core/action_codes",
  [string]$DistRoot = "products/fabric_powerbi/dist",
  [string]$MeasuresTableName = "_Measures",
  # Path to master_registry.json (for trust-score propagation).  When empty the script
  # tries <repo_root>/master_registry.json automatically.
  [string]$RegistryPath = "",
  [switch]$SkipManifest,
  # When set, do not overwrite existing _Measures.tmdl files.
  # Instead, generate a sidecar file named "<table>._generated.tmdl" next to them.
  [switch]$StubOnly,
  # When set, overwrite existing _Measures.tmdl files even if they already exist.
  # Default behaviour without this switch is to skip use cases where a measures file exists.
  [switch]$OverwriteExisting,
  # Write into a shared semantic model (e.g. Aurora showcase). All use cases -> ONE _Measures.tmdl with displayFolder per use case.
  [string]$TargetTablesDir = "",
  # Convenience: same as -TargetTablesDir "showcases/aurora_group/semantic_models/CoreActionReady.SemanticModel/definition/tables"
  # All measures go into ONE _Measures.tmdl file, organized by displayFolder = Use-Case-ID.
  [switch]$UseAuroraShowcase,
  # Skip generation of _ActionReady_Logic.tmdl (action-text measures).
  [switch]$SkipActionLogic
)

$script:ToolRoot = Split-Path -Parent $PSScriptRoot
# Repo root = three levels up from this script (tooling/generation -> repo root)
$script:RepoRoot = Split-Path -Parent (Split-Path -Parent $script:ToolRoot)

function Resolve-RepoPath {
  param(
    [string]$ProvidedPath,
    [string]$DefaultRelative
  )
  if ($ProvidedPath) {
    if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
    if ($script:RepoRoot) {
      $candidate = Join-Path -Path $script:RepoRoot -ChildPath $ProvidedPath
      if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
    }
  }
  if ($DefaultRelative) {
    if ($script:RepoRoot) {
      $fallback = Join-Path -Path $script:RepoRoot -ChildPath $DefaultRelative
      if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
    }
  }
  return $null
}

function Get-FrontMatterBlock {
  param([string]$Path, [int]$Depth = 0)
  if (-not (Test-Path $Path)) { return $null }
  $lines = Get-Content -Path $Path
  if ($lines.Count -lt 2 -or $lines[0].Trim() -ne '---') { return $null }
  for ($i = 1; $i -lt $lines.Count; $i++) {
    if ($lines[$i].Trim() -eq '---') {
      if ($i -le 1) { return @{ Text = ""; Lines = @() } }
      $blockLines = @($lines[1..($i - 1)])
      $text = ($blockLines -join [Environment]::NewLine)
      $pointer = [regex]::Match($text, 'business_factsheet\s*:\s*"([^"]+)"')
      if ($pointer.Success -and $Depth -lt 5) {
        $target = Join-Path -Path (Split-Path -Parent $Path) -ChildPath $pointer.Groups[1].Value
        if (Test-Path $target) {
          return Get-FrontMatterBlock -Path $target -Depth ($Depth + 1)
        }
      }
      return @{
        Text  = $text
        Lines = $blockLines
      }
    }
  }
  return $null
}

function Parse-IdsFromFrontMatter {
  param([string]$FrontMatter,[string]$Field)
  if (-not $FrontMatter) { return @() }
  $escaped = [regex]::Escape($Field)
  $inline = [regex]::Match($FrontMatter, "^\s*$escaped\s*:\s*\[(.*?)\]", 'Multiline,Singleline')
  $items = @()
  if ($inline.Success) {
    foreach ($match in [regex]::Matches($inline.Groups[1].Value, '"([^"]+)"|''([^'']+)''|([^,\s\]]+)')) {
      $value = if ($match.Groups[1].Success) { $match.Groups[1].Value }
               elseif ($match.Groups[2].Success) { $match.Groups[2].Value }
               else { $match.Groups[3].Value }
      if ($value) { $items += $value }
    }
    return $items
  }
  $block = [regex]::Match($FrontMatter, "(?ms)^\s*$escaped\s*:\s*(?:#.*)?\r?\n(?<body>(?:\s{2,}-\s*[^\r\n]*\r?\n?)+)")
  if ($block.Success) {
    foreach ($line in ($block.Groups['body'].Value -split "\r?\n")) {
      $trimmed = $line.Trim()
      if (-not $trimmed) { continue }
      if ($trimmed -match '^\s*-\s*(.*)$') {
        $value = $matches[1].Trim()
      } else {
        continue
      }
      if (-not $value) { continue }
      if ($value -match '^(?<val>[^#]+)\s*(#.*)?$') { $value = $matches['val'].TrimEnd() }
      if ($value.StartsWith('"') -and $value.EndsWith('"')) {
        $value = $value.Trim('"')
      } elseif ($value.StartsWith("'") -and $value.EndsWith("'")) {
        $value = $value.Trim("'")
      }
      if ($value) { $items += $value }
    }
    return $items
  }
  return @()
}

function Get-ScalarValue {
  param([string[]]$Lines,[string]$Key)
  $pattern = "^\s*$Key\s*:\s*""?(.*?)""?\s*$"
  foreach ($line in $Lines) {
    $m = [regex]::Match($line, $pattern)
    if ($m.Success) { return $m.Groups[1].Value }
  }
  return $null
}

function Parse-StringMap {
  param([string[]]$Lines,[string]$Field)
  $map = [ordered]@{}
  for ($i = 0; $i -lt $Lines.Count; $i++) {
    if ($Lines[$i] -match "^\s*$Field\s*:") {
      for ($j = $i + 1; $j -lt $Lines.Count; $j++) {
        $line = $Lines[$j]
        if ($line.Trim().Length -eq 0) { continue }
        if ($line -notmatch "^\s{2,}") { break }
        $kv = [regex]::Match($line, '^\s+([^:\s]+)\s*:\s*"(.*)"\s*$')
        if ($kv.Success) { $map[$kv.Groups[1].Value] = $kv.Groups[2].Value }
        else { break }
      }
      break
    }
  }
  return $map
}

function Get-YamlBlockIds {
  param([string]$Path)
  if (-not (Test-Path $Path)) { return @() }
  $content = Get-Content -Path $Path -Raw
  $yamlBlocks = [regex]::Matches($content, '(?s)```yaml\r?\n(.*?)```')
  $ids = @()
  foreach ($block in $yamlBlocks) {
    $yamlContent = $block.Groups[1].Value
    $mapping = [regex]::Matches($yamlContent, '(?m)^\s*-\s*kpi_id\s*:\s*([^\s#\r\n]+)')
    foreach ($match in $mapping) {
      $id = $match.Groups[1].Value.Trim()
      if ($id -and $ids -notcontains $id) { $ids += $id }
    }
  }
  # Fallback: if no YAML blocks found in factsheet, read KPI IDs from UseCase_Bracket.yaml
  if ($ids.Count -eq 0) {
    $bracketPath = Join-Path (Split-Path -Parent $Path) 'UseCase_Bracket.yaml'
    if (Test-Path $bracketPath) {
      $bracketLines = Get-Content -Path $bracketPath
      # strategic_kpi_id (single scalar)
      foreach ($line in $bracketLines) {
        $stratMatch = [regex]::Match($line, '^\s*strategic_kpi_id\s*:\s*[''"]?([a-z][a-z0-9_.]+)[''"]?\s*$')
        if ($stratMatch.Success) {
          $stratId = $stratMatch.Groups[1].Value.Trim()
          if ($stratId -and $ids -notcontains $stratId) { $ids += $stratId }
          break
        }
      }
      # influencing_kpi_ids (list, stop at next non-list-item key)
      $inInfluencing = $false
      foreach ($line in $bracketLines) {
        if ($line -match '^\s*influencing_kpi_ids\s*:') { $inInfluencing = $true; continue }
        if ($inInfluencing) {
          if ($line -match '^\s*-\s*[''"]?([a-z][a-z0-9_.]+)[''"]?\s*$') {
            $infId = $matches[1].Trim()
            if ($infId -and $ids -notcontains $infId) { $ids += $infId }
          } elseif ($line -match '^\s*\w+' -and $line -notmatch '^\s*-') {
            break  # new key, stop reading influencing
          }
        }
      }
    }
  }
  return $ids
}

function Get-ChunkValue {
  param([string]$Chunk,[string]$Key)
  $m = [regex]::Match($Chunk, "(?m)^\s*$Key\s*:\s*""([^""]*)""")
  if ($m.Success) { return $m.Groups[1].Value }
  return $null
}

function Get-LiteralBlockValue {
  param([string]$Chunk,[string]$Key)
  # Match YAML literal block: "key: |" followed by indented lines
  # Stop when we hit a line with same or less indentation as the key line
  $keyPattern = "(?m)^(\s*)$Key\s*:\s*\|\s*\r?\n"
  $keyMatch = [regex]::Match($Chunk, $keyPattern)
  if (-not $keyMatch.Success) { return $null }
  
  $keyIndent = $keyMatch.Groups[1].Value.Length
  $startPos = $keyMatch.Index + $keyMatch.Length
  
  # Extract lines until we hit a line with same/less indentation
  $remaining = $Chunk.Substring($startPos)
  $lines = @()
  foreach ($line in $remaining -split "\r?\n") {
    # Stop if line has same or less indentation (and is not empty)
    if ($line -match '^\s*\S' -and $line -match "^(\s*)") {
      $lineIndent = $matches[1].Length
      if ($lineIndent -le $keyIndent) { break }
    }
    $lines += $line
  }
  
  if ($lines.Count -eq 0) { return $null }
  
  # Find minimum indentation of non-empty lines
  $nonEmptyLines = $lines | Where-Object { $_ -match '\S' }
  if ($nonEmptyLines.Count -eq 0) { return $null }
  
  $minIndent = ($nonEmptyLines | ForEach-Object { 
    if ($_ -match '^(\s*)') { $matches[1].Length } else { 0 }
  } | Measure-Object -Minimum).Minimum
  
  # Remove common indentation and join
  $result = ($lines | ForEach-Object {
    if ($_ -match "^\s{$minIndent}(.*)$") { $matches[1] }
    elseif ($_ -match '^\s*$') { "" }
    else { $_ }
  }) -join "`n"
  
  return $result.TrimEnd()
}

function Get-ListValue {
  param([string]$Chunk,[string]$Key)
  $m = [regex]::Match($Chunk, "(?m)^\s*$Key\s*:\s*\[(.*?)\]", 'Singleline')
  if (-not $m.Success) { return @() }
  $list = @()
  foreach ($match in [regex]::Matches($m.Groups[1].Value, '"([^"]+)"')) {
    $list += $match.Groups[1].Value
  }
  return $list
}

function Get-QARules {
  param([string]$Chunk)
  $m = [regex]::Match($Chunk, "(?ms)qa_rules\s*:\s*(?:\r?\n\s*-\s*""[^""]*""\s*)+")
  if (-not $m.Success) { return @() }
  $rules = @()
  foreach ($match in [regex]::Matches($m.Value, '\s*-\s*"(.*?)"', 'Singleline')) {
    $rules += $match.Groups[1].Value
  }
  return $rules
}

function Split-KpiChunks {
  param([string]$Block)
  $listMatches = [regex]::Matches($Block, '(?m)^\s*-\s*kpi_id\s*:\s*([^\s#]+)')
  $chunks = @()
  if ($listMatches.Count -gt 0) {
    for ($i = 0; $i -lt $listMatches.Count; $i++) {
      $start = $listMatches[$i].Index
      $end = if ($i -lt $listMatches.Count - 1) { $listMatches[$i + 1].Index } else { $Block.Length }
      $chunks += $Block.Substring($start, $end - $start)
    }
  } elseif ([regex]::IsMatch($Block, '(?m)^\s*kpi_id\s*:\s*([^\s#]+)')) {
    $chunks += $Block
  }
  return $chunks
}

function Parse-KpiRecord {
  param([string]$Chunk,[string]$SourcePath)
  $idMatch = [regex]::Match($Chunk, '(?m)^\s*-?\s*kpi_id\s*:\s*([^\s#]+)')
  if (-not $idMatch.Success) { return $null }
  $rec = [ordered]@{}
  $rec.id = $idMatch.Groups[1].Value
  $rec.kpi_key = Get-ChunkValue -Chunk $Chunk -Key 'kpi_key'
  $rec.dax_name = Get-ChunkValue -Chunk $Chunk -Key 'dax_name'
  # Try literal block first (for multi-line DAX), then quoted string
  $rec.dax_expression = Get-LiteralBlockValue -Chunk $Chunk -Key 'dax_expression'
  if (-not $rec.dax_expression) {
    $rec.dax_expression = Get-ChunkValue -Chunk $Chunk -Key 'dax_expression'
  }
  $fmtMatches = [regex]::Matches($Chunk, '(?m)^\s*formatString\s*:\s*"([^"]*)"')
  $rec.formatString = if ($fmtMatches.Count) { $fmtMatches[$fmtMatches.Count - 1].Groups[1].Value } else { "" }
  $folderMatches = [regex]::Matches($Chunk, '(?m)^\s*displayFolder\s*:\s*"([^"]*)"')
  $rec.displayFolder = if ($folderMatches.Count) { $folderMatches[$folderMatches.Count - 1].Groups[1].Value } else { "" }
  $rec.description = Get-ChunkValue -Chunk $Chunk -Key 'description'
  $rec.kpi_type = Get-ChunkValue -Chunk $Chunk -Key 'kpi_type'
  $rec.impact_dimension = Get-ChunkValue -Chunk $Chunk -Key 'impact_dimension'
  $rec.calc_type = Get-ChunkValue -Chunk $Chunk -Key 'calc_type'
  $rec.refresh = Get-ChunkValue -Chunk $Chunk -Key 'refresh'
  $rec.status = Get-ChunkValue -Chunk $Chunk -Key 'status'
  $purposeMatch = [regex]::Match($Chunk, '(?m)^\s+purpose\s*:\s*"([^"]*)"')
  $rec.purpose = if ($purposeMatch.Success) { $purposeMatch.Groups[1].Value } else { "" }
  $rec.domain_tags = Get-ListValue -Chunk $Chunk -Key 'domain_tag'
  $rec.depends_on = Get-ListValue -Chunk $Chunk -Key 'depends_on'
  $rec.depends_on_ids = Get-ListValue -Chunk $Chunk -Key 'depends_on_ids'
  $rec.business_owner = Get-ChunkValue -Chunk $Chunk -Key 'business_owner'
  $rec.data_owner = Get-ChunkValue -Chunk $Chunk -Key 'data_owner'
  $rec.steward = Get-ChunkValue -Chunk $Chunk -Key 'steward'
  $rec.qa_rules = Get-QARules -Chunk $Chunk
  $rec.source = $SourcePath
  return $rec
}

function Load-KpiCatalog {
  param([string]$Root)
  $map = @{}
  Get-ChildItem -Path $Root -Filter '*.md' | Where-Object { $_.Name -ne 'SCHEMA.md' } | ForEach-Object {
    $raw = Get-Content -Raw -Path $_.FullName
    foreach ($match in [regex]::Matches($raw, '(?ms)```yaml\s*(.*?)\s*```')) {
      foreach ($chunk in (Split-KpiChunks -Block $match.Groups[1].Value)) {
        $rec = Parse-KpiRecord -Chunk $chunk -SourcePath $_.FullName
        if ($rec) { $map[$rec.id] = $rec }
      }
    }
  }
  return $map
}

function Ensure-Dir {
  param([string]$Path)
  if (-not (Test-Path $Path)) {
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
  }
}

function Write-Utf8NoBom {
  param([string]$Path,[string]$Text)
  $utf8 = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Text, $utf8)
}

function Get-SafeName {
  param([string]$Name)
  $safe = $Name
  foreach ($ch in [System.IO.Path]::GetInvalidFileNameChars()) {
    $safe = $safe.Replace($ch, '_')
  }
  return $safe
}

# ---------------------------------------------------------------------------
# ActionReady Logic helpers
# ---------------------------------------------------------------------------

function Load-UseCaseBrackets {
  <#
  .SYNOPSIS Load all UseCase_Bracket.yaml files and return a hashtable keyed by use case ID.
  #>
  param([string]$Root)
  $map = @{}
  $bracketFiles = Get-ChildItem -Path $Root -Recurse -Filter 'UseCase_Bracket.yaml' -ErrorAction SilentlyContinue
  foreach ($f in $bracketFiles) {
    $raw = Get-Content -Raw -Path $f.FullName
    $idMatch = [regex]::Match($raw, '(?m)^\s*id\s*:\s*[''"]?([A-Z]{2,3}-\d{3})[''"]?\s*$')
    if (-not $idMatch.Success) { continue }
    $ucId = $idMatch.Groups[1].Value
    # Extract action_code_ids list (multiline only, NOT singleline - '.' must NOT match \n)
    $actionIds = @()
    $actionBlock = [regex]::Match($raw, '(?m)action_code_ids\s*:\s*\r?\n((?:\s*-\s*[^\r\n]+\r?\n)+)')
    if ($actionBlock.Success) {
      foreach ($line in ($actionBlock.Groups[1].Value -split "\r?\n")) {
        $m = [regex]::Match($line, '^\s*-\s*[''"]?([^''"#\r\n]+)[''"]?\s*$')
        if ($m.Success) { $actionIds += $m.Groups[1].Value.Trim() }
      }
    }
    # Extract strategic_kpi_id
    $stratMatch = [regex]::Match($raw, '(?m)^\s*strategic_kpi_id\s*:\s*[''"]?([^''"#\r\n]+)[''"]?\s*$')
    $strategicKpiId = if ($stratMatch.Success) { $stratMatch.Groups[1].Value.Trim() } else { $null }
    # Extract influencing_kpi_ids (multiline only, NOT singleline)
    $influencingIds = @()
    $infBlock = [regex]::Match($raw, '(?m)influencing_kpi_ids\s*:\s*\r?\n((?:\s*-\s*[^\r\n]+\r?\n)+)')
    if ($infBlock.Success) {
      foreach ($line in ($infBlock.Groups[1].Value -split "\r?\n")) {
        $m = [regex]::Match($line, '^\s*-\s*[''"]?([^''"#\r\n]+)[''"]?\s*$')
        if ($m.Success) { $influencingIds += $m.Groups[1].Value.Trim() }
      }
    }
    $map[$ucId] = @{
      id                = $ucId
      action_code_ids   = $actionIds
      strategic_kpi_id  = $strategicKpiId
      influencing_kpi_ids = $influencingIds
      path              = $f.FullName
    }
  }
  return $map
}

function Load-ActionCodeYaml {
  <#
  .SYNOPSIS Parse a single action code YAML file and return a hashtable with id, name, trigger summary, owner, and steps.
  #>
  param([string]$Path)
  if (-not (Test-Path $Path)) { return $null }
  $raw = Get-Content -Raw -Path $Path
  $idMatch = [regex]::Match($raw, '(?m)^\s*id\s*:\s*"?([^"''\r\n]+)"?\s*$')
  if (-not $idMatch.Success) { return $null }
  $id = $idMatch.Groups[1].Value.Trim()
  $nameMatch = [regex]::Match($raw, '(?m)^\s*name\s*:\s*"?([^"''\r\n]+)"?\s*$')
  $name = if ($nameMatch.Success) { $nameMatch.Groups[1].Value.Trim() } else { $id }

  # Trigger summary: type + levels summary
  $triggerType = ""
  $triggerTypeMatch = [regex]::Match($raw, '(?ms)^trigger\s*:.*?type\s*:\s*"?([^"''\r\n]+)"?')
  if ($triggerTypeMatch.Success) { $triggerType = $triggerTypeMatch.Groups[1].Value.Trim() }

  # Levels: L1/L2/L3 severity
  $levels = @()
  foreach ($lvl in @("L1", "L2", "L3")) {
    $sevMatch = [regex]::Match($raw, "(?ms)$lvl\s*:\s*\r?\n\s*severity\s*:\s*""?([^""\r\n]+)""?")
    if ($sevMatch.Success) {
      $levels += "$($lvl): $($sevMatch.Groups[1].Value.Trim())"
    }
  }
  $triggerSummary = $triggerType
  if ($levels.Count -gt 0) {
    $triggerSummary += " (" + ($levels -join ", ") + ")"
  }
  if (-not $triggerSummary) { $triggerSummary = "(no trigger defined)" }

  # Owner
  $ownerMatch = [regex]::Match($raw, '(?m)^\s*primary_owner_role\s*:\s*"?([^"''\r\n]+)"?\s*$')
  $owner = if ($ownerMatch.Success) { $ownerMatch.Groups[1].Value.Trim() } else { "TBD" }

  # Steps — line-by-line state machine (no singleline regex to avoid cross-section greediness)
  $steps = @()
  $inOpExec = $false
  $inSteps = $false
  $stepsIndent = -1
  foreach ($line in ($raw -split "\r?\n")) {
    if ($line -match '^\s*operational_execution\s*:') { $inOpExec = $true; continue }
    if (-not $inOpExec) { continue }
    # Detect end of operational_execution (next top-level key)
    if ($line -match '^\S' -and $line -notmatch '^\s*$') { break }
    if ($line -match '^\s*steps\s*:') { $inSteps = $true; continue }
    if ($inSteps) {
      if ($line -match '^\s*-\s*"?([^"'']+)"?\s*$') {
        $currentIndent = ($line -replace '^(\s*).*', '$1').Length
        if ($stepsIndent -lt 0) { $stepsIndent = $currentIndent }
        if ($currentIndent -eq $stepsIndent) {
          $steps += $matches[1].Trim()
        } else {
          break  # indentation changed -> new sub-key
        }
      } elseif ($line -match '^\s+\w+\s*:') {
        break  # next key after steps
      }
    }
  }

  return @{
    id             = $id
    name           = $name
    trigger_summary = $triggerSummary
    owner_role     = $owner
    steps          = $steps
  }
}

function Load-AllActionCodes {
  <#
  .SYNOPSIS Load all action code YAML files into a hashtable keyed by action code ID.
  #>
  param([string]$Root)
  $map = @{}
  $files = Get-ChildItem -Path $Root -Recurse -Filter '*.yaml' -ErrorAction SilentlyContinue |
    Where-Object { $_.DirectoryName -notmatch 'decision_spines' }
  foreach ($f in $files) {
    $ac = Load-ActionCodeYaml -Path $f.FullName
    if ($ac) { $map[$ac.id] = $ac }
  }
  return $map
}

function Load-Registry {
  <#
  .SYNOPSIS Load master_registry.json and return its content as a PSObject, or $null if not found.
  #>
  param([string]$ExplicitPath, [string]$RepoRoot)
  $candidates = @()
  if ($ExplicitPath -and (Test-Path $ExplicitPath)) { $candidates += $ExplicitPath }
  if ($RepoRoot) {
    $candidates += (Join-Path $RepoRoot 'tooling\ontology\out\master_registry.json')
    $candidates += (Join-Path $RepoRoot 'master_registry.json')
    $candidates += (Join-Path $RepoRoot 'tooling\ontology\master_registry.json')
  }
  foreach ($p in $candidates) {
    if (Test-Path $p) {
      try {
        $json = Get-Content -Raw -Path $p | ConvertFrom-Json
        Write-Host "Loaded registry from $p" -ForegroundColor Gray
        return $json
      } catch {
        Write-Host "Warning: Failed to parse registry at $($p): $_" -ForegroundColor Yellow
      }
    }
  }
  return $null
}

function Build-ActionTextMeasureBlock {
  <#
  .SYNOPSIS Build TMDL measure block for a single Action Code text measure.
  Output: array of TMDL lines (tab-indented).
  #>
  param($ActionCode)
  $t1 = "`t"
  $t2 = "`t`t"
  $t3 = "`t`t`t"
  $lines = @()
  $acId = $ActionCode.id
  $measureName = "Action_$($acId)_Text"
  $safeId = $measureName.Replace("'", "''")

  # Build DAX string content
  $daxParts = @()
  $daxParts += "Trigger: $($ActionCode.trigger_summary)"
  $daxParts += "Owner: $($ActionCode.owner_role)"
  if ($ActionCode.steps -and $ActionCode.steps.Count -gt 0) {
    $daxParts += "Steps:"
    $stepNum = 1
    foreach ($step in $ActionCode.steps) {
      $daxParts += "  $($stepNum). $step"
      $stepNum++
    }
  }

  # Build DAX expression using UNICHAR(10) for line breaks
  $daxFragments = @()
  foreach ($part in $daxParts) {
    $escaped = $part.Replace('"', '""')
    $daxFragments += """$escaped"""
  }
  $daxExpression = $daxFragments -join " & UNICHAR(10) & "

  # Comment header
  $lines += ($t1 + "/// ActionReady Logic: $acId - $($ActionCode.name)")

  # Measure definition
  $lines += ($t1 + "measure '$safeId' =")
  $lines += ($t3 + $daxExpression)
  $lines += ($t2 + "isHidden")
  $lines += ($t2 + "displayFolder: ""9_ActionReady_Logic""")
  # Annotation for RLS / automation
  $lines += ($t2 + "annotation ActionReady_ResponsibleRole = ""$($ActionCode.owner_role)""")
  $lines += ($t2 + "annotation ActionReady_ActionCodeId = ""$acId""")
  $lines += ""
  return $lines
}

function Build-ActionReadyLogicTable {
  <#
  .SYNOPSIS Generate the full _ActionReady_Logic.tmdl file content.
  Collects all action codes referenced by the selected use cases.
  Returns: string (full TMDL file content) and a count of measures generated.
  #>
  param(
    [hashtable]$Brackets,      # UseCase ID -> bracket data
    [hashtable]$ActionCodes,   # Action Code ID -> action code data
    [string[]]$SelectedUseCases # Use case IDs to include (empty = all)
  )
  $t1 = "`t"
  $t2 = "`t`t"
  $t3 = "`t`t`t"

  # Collect unique action code IDs from brackets
  $actionIdsNeeded = @{}
  foreach ($ucId in $Brackets.Keys) {
    if ($SelectedUseCases -and $SelectedUseCases.Count -gt 0) {
      $matched = $false
      foreach ($filter in $SelectedUseCases) {
        if ($ucId -like ($filter + '*')) { $matched = $true; break }
      }
      if (-not $matched) { continue }
    }
    foreach ($acId in $Brackets[$ucId].action_code_ids) {
      if (-not $actionIdsNeeded.ContainsKey($acId)) {
        $actionIdsNeeded[$acId] = @()
      }
      $actionIdsNeeded[$acId] += $ucId
    }
  }

  if ($actionIdsNeeded.Count -eq 0) {
    return @{ Content = $null; Count = 0 }
  }

  # Sort action code IDs for deterministic output
  $sortedAcIds = $actionIdsNeeded.Keys | Sort-Object

  $header = @()
  $header += "/// ActionReady Logic Table - Auto-generated from UseCase Brackets + Action Code YAMLs"
  $header += "/// Contains hidden text measures for each subscribed Action Code."
  $header += "/// DO NOT EDIT MANUALLY - regenerate via generate_tmdl_measures.ps1"
  $header += "table _ActionReady_Logic"
  $header += ($t1 + "isHidden")
  $header += ""
  $header += ($t1 + "partition _ActionReady_Logic = m")
  $header += ($t2 + "mode: import")
  $header += ($t2 + "source =")
  $header += ($t3 + "`tlet")
  $header += ($t3 + "`t`tSource = #table(type table[_Placeholder = text], {})")
  $header += ($t3 + "`tin")
  $header += ($t3 + "`t`tSource")
  $header += ""
  $header += ($t1 + "column _Placeholder")
  $header += ($t2 + "dataType: string")
  $header += ($t2 + "sourceColumn: _Placeholder")
  $header += ($t2 + "isHidden")
  $header += ($t2 + "summarizeBy: none")
  $header += ""

  $measureBlocks = @()
  $generatedCount = 0
  foreach ($acId in $sortedAcIds) {
    $ac = if ($ActionCodes.ContainsKey($acId)) { $ActionCodes[$acId] } else { $null }
    if (-not $ac) {
      # Action code YAML not found - generate a stub with warning
      $ac = @{
        id             = $acId
        name           = "(Action Code not found)"
        trigger_summary = "(no trigger defined)"
        owner_role     = "TBD"
        steps          = @("(Action Code YAML missing - please create $acId)")
      }
      Write-Host "Warning: Action Code '$acId' referenced by $($actionIdsNeeded[$acId] -join ', ') but YAML not found." -ForegroundColor Yellow
    }
    $block = Build-ActionTextMeasureBlock -ActionCode $ac
    $measureBlocks += $block
    $generatedCount++
  }

  $content = ($header + $measureBlocks) -join [Environment]::NewLine
  return @{ Content = $content; Count = $generatedCount }
}

function Resolve-SemanticModelPath {
  param(
    [string]$CaseRoot,
    [string]$DatasetModel,
    [string]$UseCaseId
  )
  $candidates = New-Object System.Collections.Generic.List[string]
  if ($DatasetModel) {
    $candidates.Add((Join-Path $CaseRoot $DatasetModel))
    $safeName = Get-SafeName -Name $DatasetModel
    if ($safeName -ne $DatasetModel) {
      $candidates.Add((Join-Path $CaseRoot $safeName))
    }
  }
  $candidates.Add((Join-Path $CaseRoot ("$UseCaseId.SemanticModel")))
  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
  }
  $target = $candidates[0]
  Ensure-Dir $CaseRoot
  Ensure-Dir $target
  return (Resolve-Path -Path $target).Path
}

function Build-MeasureObject {
  param(
    [string]$KpiId,
    $CatalogRecord,
    [System.Collections.Specialized.OrderedDictionary]$LabelMap
  )
  $label = if ($LabelMap -and $LabelMap.Contains($KpiId)) { $LabelMap[$KpiId] }
  elseif ($CatalogRecord -and $CatalogRecord.kpi_key) { $CatalogRecord.kpi_key }
  elseif ($CatalogRecord -and $CatalogRecord.dax_name) { $CatalogRecord.dax_name }
  else { $KpiId }

  if (-not $CatalogRecord) {
    return [ordered]@{
      kpi_id       = $KpiId
      name         = $label
      missing      = $true
      purpose      = $null
      description  = $null
      dax_expression = $null
    }
  }

  $domainTags = @()
  if ($CatalogRecord.domain_tags) { $domainTags = @($CatalogRecord.domain_tags) }
  $dependsOn = @()
  if ($CatalogRecord.depends_on) { $dependsOn = @($CatalogRecord.depends_on) }
  $dependsOnIds = @()
  if ($CatalogRecord.depends_on_ids) { $dependsOnIds = @($CatalogRecord.depends_on_ids) }
  $qaRules = @()
  if ($CatalogRecord.qa_rules) { $qaRules = @($CatalogRecord.qa_rules) }
  $purpose = $CatalogRecord.purpose

  return [ordered]@{
    kpi_id          = $KpiId
    name            = $label
    kpi_key         = $CatalogRecord.kpi_key
    kpi_type        = $CatalogRecord.kpi_type
    impact_dimension= $CatalogRecord.impact_dimension
    domain_tags     = $domainTags
    calc_type       = $CatalogRecord.calc_type
    refresh         = $CatalogRecord.refresh
    status          = $CatalogRecord.status
    format_string   = $CatalogRecord.formatString
    display_folder  = $CatalogRecord.displayFolder
    purpose         = $purpose
    description     = if ($purpose) { $purpose } else { $CatalogRecord.description }
    technical_description = $CatalogRecord.description
    dax_expression  = $CatalogRecord.dax_expression
    depends_on      = $dependsOn
    depends_on_ids  = $dependsOnIds
    business_owner  = $CatalogRecord.business_owner
    data_owner      = $CatalogRecord.data_owner
    steward         = $CatalogRecord.steward
    qa_rules        = $qaRules
    catalog_source  = $CatalogRecord.source
  }
}

function Build-MeasureBlock {
  param($Measure, [string]$DefaultDisplayFolder, [hashtable]$TrustScores)
  # TMDL requires tabs only for indentation (tmdl_best_practices.md; check_tmdl_syntax.ps1).
  $t1 = "`t"
  $t2 = "`t`t"
  $t3 = "`t`t`t"
  $lines = @()
  if ($Measure.kpi_id -or $Measure.kpi_key) {
    $label = $Measure.kpi_key
    if (-not $label) { $label = $Measure.name }
    $lines += ($t1 + "/// " + $Measure.kpi_id + " - " + $label)
  }
  # Trust-score warning (annotation-based, does NOT change measure name)
  $trustScore = $null
  if ($TrustScores -and $Measure.kpi_id -and $TrustScores.ContainsKey($Measure.kpi_id)) {
    $trustScore = $TrustScores[$Measure.kpi_id]
    if ($trustScore -eq 0) {
      $lines += ($t1 + "/// [!] UNTRUSTED - Data Contract validation failed for this KPI. trust_score=0")
    }
  }
  if ($Measure.purpose) { $lines += ($t1 + "/// " + $Measure.purpose) }
  elseif ($Measure.description) { $lines += ($t1 + "/// " + $Measure.description) }
  $name = $Measure.name.Replace("'", "''")
  $expressionLines = @()
  if ($Measure.missing) {
    $lines += ($t1 + "/// MISSING in KPI catalog: " + $Measure.kpi_id)
    $expressionLines = @("// TODO", "BLANK()")
  } else {
    $expr = if ($Measure.dax_expression) { $Measure.dax_expression } else { "BLANK()" }
    $expressionLines = $expr -split "\r?\n"
  }
  $lines += ($t1 + "measure '$name' =")
  foreach ($ln in $expressionLines) {
    $lines += ($t3 + $ln.TrimStart())
  }
  if ($Measure.format_string) { $lines += ($t2 + "formatString: """ + $Measure.format_string.Replace('"', '\"') + """") }
  # Display folder: strategic vs influencing vs default
  $displayFolder = if ($Measure.display_folder) { $Measure.display_folder } else { $DefaultDisplayFolder }
  if ($displayFolder) { $lines += ($t2 + "displayFolder: """ + $displayFolder.Replace('"', '\"') + """") }
  # Trust-score annotation (machine-readable, no name change)
  if ($null -ne $trustScore) {
    $lines += ($t2 + "annotation ActionReady_TrustScore = ""$trustScore""")
  }
  $lines += ""
  return $lines
}

function Write-Manifest {
  param([string]$Path,$Manifest)
  $json = $Manifest | ConvertTo-Json -Depth 10
  Write-Utf8NoBom -Path $Path -Text $json
}

$resolvedUseCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative 'core/usecases'
if (-not $resolvedUseCasesRoot) { throw "Unable to resolve UseCases root folder. Provide -UseCasesRoot or run inside repository." }
$resolvedKpiRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative 'core/kpi_catalog'
if (-not $resolvedKpiRoot) { throw "Unable to resolve KPI catalog root. Provide -KpiCatalogRoot or run inside repository." }

# Primary output: shared semantic model (e.g. Aurora showcase). When set, write <UseCase>_Measures.tmdl into this directory.
$resolvedTablesDir = $null
if ($UseAuroraShowcase) {
  $auroraRelative = "showcases/aurora_group/semantic_models/CoreActionReady.SemanticModel/definition/tables"
  $resolvedTablesDir = if ($script:RepoRoot -and (Test-Path (Join-Path $script:RepoRoot $auroraRelative))) { (Resolve-Path (Join-Path $script:RepoRoot $auroraRelative)).Path } else { $null }
  if (-not $resolvedTablesDir) { $resolvedTablesDir = Join-Path $script:RepoRoot $auroraRelative; Ensure-Dir (Split-Path -Parent $resolvedTablesDir) | Out-Null; New-Item -ItemType Directory -Path $resolvedTablesDir -Force | Out-Null; $resolvedTablesDir = (Resolve-Path $resolvedTablesDir).Path }
}
if ($TargetTablesDir -and $TargetTablesDir.Trim().Length -gt 0) {
  if (Test-Path $TargetTablesDir) { $resolvedTablesDir = (Resolve-Path $TargetTablesDir).Path }
  elseif ($script:RepoRoot) {
    $candidate = Join-Path $script:RepoRoot $TargetTablesDir.Trim()
    if (Test-Path $candidate) { $resolvedTablesDir = (Resolve-Path $candidate).Path }
    else { $resolvedTablesDir = $candidate; Ensure-Dir (Split-Path -Parent $resolvedTablesDir) | Out-Null; New-Item -ItemType Directory -Path $resolvedTablesDir -Force | Out-Null; $resolvedTablesDir = (Resolve-Path $resolvedTablesDir).Path }
  }
  else { throw "Unable to resolve TargetTablesDir. Provide an absolute path or run from repository root." }
}
if (-not $resolvedTablesDir) {
  $resolvedDistRoot = Resolve-RepoPath -ProvidedPath $DistRoot -DefaultRelative 'products/fabric_powerbi/dist'
  if (-not $resolvedDistRoot) { throw "Unable to resolve dist root. Provide -DistRoot or -UseAuroraShowcase / -TargetTablesDir or run inside repository." }
}

$factSheets = Get-ChildItem -Path $resolvedUseCasesRoot -Recurse -Filter 'Business_Factsheet.md' | Where-Object {
  $_.FullName -notmatch '\\templates\\' -and $_.FullName -notmatch '\\_internal\\archive\\'
}
if ($UseCase -and $UseCase.Count -gt 0) {
  # Split comma-separated values if passed as single string from CLI
  $expandedUseCase = @()
  foreach ($uc in $UseCase) {
    if ($uc -and $uc.Contains(',')) {
      $expandedUseCase += $uc -split ',' | Where-Object { $_ -and $_.Trim().Length -gt 0 } | ForEach-Object { $_.Trim() }
    } elseif ($uc) {
      $expandedUseCase += $uc.Trim()
    }
  }
  $filters = $expandedUseCase | Where-Object { $_ -and $_.Trim().Length -gt 0 }
  if ($filters.Count -gt 0) {
    $factSheets = foreach ($fs in $factSheets) {
      $frontMatter = Get-FrontMatterBlock -Path $fs.FullName
      if (-not $frontMatter) { continue }
      $lines = @($frontMatter.Lines)
      $useCaseId = Get-ScalarValue -Lines $lines -Key 'id'
      if (-not $useCaseId) { $useCaseId = $fs.Directory.Name.Split('_')[0] }
      if ($filters | Where-Object { $useCaseId -like ($_ + '*') }) { $fs }
    }
  }
}

if ($factSheets.Count -eq 0) {
  Write-Host "No FactSheets matched the provided filters." -ForegroundColor Yellow
  exit 0
}

$catalog = Load-KpiCatalog -Root $resolvedKpiRoot
$generated = 0

# ---------------------------------------------------------------------------
# ActionReady: load brackets, action codes, registry (trust scores)
# ---------------------------------------------------------------------------
$resolvedActionCodesRoot = Resolve-RepoPath -ProvidedPath $ActionCodesRoot -DefaultRelative 'core/action_codes'
$useCaseBrackets = Load-UseCaseBrackets -Root $resolvedUseCasesRoot
$allActionCodes = if ($resolvedActionCodesRoot) { Load-AllActionCodes -Root $resolvedActionCodesRoot } else { @{} }
$registry = Load-Registry -ExplicitPath $RegistryPath -RepoRoot $script:RepoRoot

# Build trust-score lookup: kpi_id -> integer (0 = untrusted, 1 = trusted, $null = unknown)
$trustScores = @{}
if ($registry -and $registry.kpis) {
  foreach ($prop in $registry.kpis.PSObject.Properties) {
    $kpiObj = $prop.Value
    if ($null -ne $kpiObj.trust_score) {
      $trustScores[$prop.Name] = [int]$kpiObj.trust_score
    }
  }
  if ($trustScores.Count -gt 0) {
    $untrustedCount = ($trustScores.Values | Where-Object { $_ -eq 0 }).Count
    Write-Host "Loaded trust scores for $($trustScores.Count) KPIs ($untrustedCount untrusted)." -ForegroundColor Gray
  }
}

# Determine selected use case IDs (for action logic generation)
$selectedUseCaseFilters = @()
if ($UseCase -and $UseCase.Count -gt 0) {
  foreach ($uc in $UseCase) {
    if ($uc -and $uc.Contains(',')) {
      $selectedUseCaseFilters += $uc -split ',' | Where-Object { $_ -and $_.Trim().Length -gt 0 } | ForEach-Object { $_.Trim() }
    } elseif ($uc) {
      $selectedUseCaseFilters += $uc.Trim()
    }
  }
}

# ============================================================================
# MODE: Shared semantic model (Aurora showcase) - ALL measures in ONE _Measures.tmdl
# ============================================================================
if ($resolvedTablesDir) {
  $allMeasureBlocks = @()
  $processedUseCases = @()

  foreach ($fs in $factSheets) {
    $frontMatter = Get-FrontMatterBlock -Path $fs.FullName
    if (-not $frontMatter) { continue }
    $lines = $frontMatter.Lines
    $useCaseId = Get-ScalarValue -Lines $lines -Key 'id'
    if (-not $useCaseId) { $useCaseId = $fs.Directory.Name.Split('_')[0] }

    $targetIds = Get-YamlBlockIds -Path $fs.FullName
    if ($targetIds.Count -eq 0) {
      Write-Host "Skipping $useCaseId - no kpi_id entries found in YAML blocks." -ForegroundColor Yellow
      continue
    }
    $labelMap = Parse-StringMap -Lines $lines -Field 'required_kpis'
    if (-not $labelMap) { $labelMap = [ordered]@{} }

    foreach ($id in $targetIds) {
      $record = if ($catalog.ContainsKey($id)) { $catalog[$id] } else { $null }
      $measure = Build-MeasureObject -KpiId $id -CatalogRecord $record -LabelMap $labelMap
      if (-not $record) {
        Write-Host "Warning: KPI '$id' missing in catalog for $useCaseId" -ForegroundColor Yellow
      }
      # Build measure block with displayFolder = useCaseId + trust scores
      $allMeasureBlocks += (Build-MeasureBlock -Measure $measure -DefaultDisplayFolder $useCaseId -TrustScores $trustScores)
    }
    $processedUseCases += $useCaseId
    Write-Host "Collected measures for $useCaseId" -ForegroundColor Gray
  }

  if ($allMeasureBlocks.Count -eq 0) {
    Write-Host "No measures collected." -ForegroundColor Yellow
    exit 0
  }

  # Write ALL measures to ONE _Measures.tmdl
  $measuresPath = Join-Path $resolvedTablesDir "_Measures.tmdl"
  $generatedPath = Join-Path $resolvedTablesDir "_Measures.generated.tmdl"

  if (-not $StubOnly -and -not $OverwriteExisting -and (Test-Path $measuresPath)) {
    Write-Host "Skipping - _Measures.tmdl already exists (use -OverwriteExisting or -StubOnly)." -ForegroundColor Yellow
    exit 0
  }

  $header = @()
  $header += ("/// Consolidated Measures for: " + ($processedUseCases -join ", "))
  $header += ("table $MeasuresTableName")
  $header += ""
  $header += ("`tpartition $MeasuresTableName = m")
  $header += ("`t`tmode: import")
  $header += ("`t`tsource =")
  $header += ("`t`t`t`tlet")
  $header += ("`t`t`t`t`tSource = #table(type table[Column1 = text], {})")
  $header += ("`t`t`t`tin")
  $header += ("`t`t`t`t`tSource")
  $header += ""
  $header += ("`tcolumn Column1")
  $header += ("`t`tdataType: string")
  $header += ("`t`tsourceColumn: Column1")
  $header += ("`t`tisHidden")
  $header += ("`t`tsummarizeBy: none")
  $header += ""

  $content = ($header + $allMeasureBlocks) -join [Environment]::NewLine

  if ($StubOnly) {
    Write-Utf8NoBom -Path $generatedPath -Text $content
    Write-Host ("Generated stub _Measures.tmdl with measures from: " + ($processedUseCases -join ", ") + " -> " + $generatedPath) -ForegroundColor Green
  } else {
    Write-Utf8NoBom -Path $measuresPath -Text $content
    Write-Host ("Generated _Measures.tmdl with measures from: " + ($processedUseCases -join ", ") + " -> " + $measuresPath) -ForegroundColor Green
  }
  $generated = $processedUseCases.Count
}
# ============================================================================
# MODE: Per-use-case output (dist) - one _Measures.tmdl per use case folder
# ============================================================================
else {
  foreach ($fs in $factSheets) {
    $frontMatter = Get-FrontMatterBlock -Path $fs.FullName
    if (-not $frontMatter) { continue }
    $lines = $frontMatter.Lines
    $text = $frontMatter.Text

    $useCaseId = Get-ScalarValue -Lines $lines -Key 'id'
    if (-not $useCaseId) { $useCaseId = $fs.Directory.Name.Split('_')[0] }

    $title = Get-ScalarValue -Lines $lines -Key 'title'
    $datasetModel = Get-ScalarValue -Lines $lines -Key 'dataset_model'
    if (-not $datasetModel) { $datasetModel = "$useCaseId.SemanticModel" }

    $targetIds = Get-YamlBlockIds -Path $fs.FullName
    if ($targetIds.Count -eq 0) {
      Write-Host "Skipping $useCaseId - no kpi_id entries found in YAML blocks." -ForegroundColor Yellow
      continue
    }
    $labelMap = Parse-StringMap -Lines $lines -Field 'required_kpis'
    if (-not $labelMap) { $labelMap = [ordered]@{} }

    $manifest = [ordered]@{
      usecase_id    = $useCaseId
      title         = $title
      dataset_model = $datasetModel
      table_name    = $MeasuresTableName
      fact_sheet    = (Resolve-Path -Path $fs.FullName).Path
      measures      = @()
    }

    foreach ($id in $targetIds) {
      $record = if ($catalog.ContainsKey($id)) { $catalog[$id] } else { $null }
      $measure = Build-MeasureObject -KpiId $id -CatalogRecord $record -LabelMap $labelMap
      $manifest.measures += $measure
      if (-not $record) {
        Write-Host "Warning: KPI '$id' missing in catalog for $useCaseId" -ForegroundColor Yellow
      }
    }

    $caseRoot = Join-Path $resolvedDistRoot $useCaseId
    $semRoot = Resolve-SemanticModelPath -CaseRoot $caseRoot -DatasetModel $datasetModel -UseCaseId $useCaseId
    $definitionRoot = Join-Path $semRoot 'definition'
    $tablesDir = Join-Path $definitionRoot 'tables'
    Ensure-Dir $tablesDir
    $measuresPath = Join-Path $tablesDir ("$MeasuresTableName.tmdl")
    $generatedPath = Join-Path $tablesDir ("$MeasuresTableName.generated.tmdl")

    if (-not $StubOnly -and -not $OverwriteExisting -and (Test-Path $measuresPath)) {
      Write-Host "Skipping $useCaseId - measures file already exists (use -OverwriteExisting or -StubOnly)." -ForegroundColor Yellow
      continue
    }

    $header = @()
    if ($title) { $header += ("/// $useCaseId Measures ($title)") } else { $header += ("/// $useCaseId Measures") }
    $header += ("table $MeasuresTableName")
    $header += ""
    $header += ("`tpartition $MeasuresTableName = m")
    $header += ("`t`tmode: import")
    $header += ("`t`tsource =")
    $header += ("`t`t`t`tlet")
    $header += ("`t`t`t`t`tSource = #table(type table[Column1 = text], {})")
    $header += ("`t`t`t`tin")
    $header += ("`t`t`t`t`tSource")
    $header += ""
    $header += ("`tcolumn Column1")
    $header += ("`t`tdataType: string")
    $header += ("`t`tsourceColumn: Column1")
    $header += ("`t`tisHidden")
    $header += ("`t`tsummarizeBy: none")
    $header += ""

    $blocks = @()
    foreach ($measure in $manifest.measures) {
      $blocks += (Build-MeasureBlock -Measure $measure -DefaultDisplayFolder $useCaseId -TrustScores $trustScores)
    }

    $content = ($header + $blocks) -join [Environment]::NewLine

    if ($StubOnly) {
      Write-Utf8NoBom -Path $generatedPath -Text $content
    } else {
      Write-Utf8NoBom -Path $measuresPath -Text $content
    }

    $modelPath = Join-Path $definitionRoot 'model.tmdl'
    if (-not $StubOnly -and (Test-Path $modelPath)) {
      $modelRaw = Get-Content -Raw -Path $modelPath
      if ($modelRaw -notmatch ("(?m)^ref\s+table\s+" + [regex]::Escape($MeasuresTableName) + '\s*$')) {
        $append = "ref table $MeasuresTableName"
        if ($modelRaw.TrimEnd().Length -gt 0) {
          Write-Utf8NoBom -Path $modelPath -Text ($modelRaw.TrimEnd() + [Environment]::NewLine + $append + [Environment]::NewLine)
        } else {
          Write-Utf8NoBom -Path $modelPath -Text ($append + [Environment]::NewLine)
        }
      }
    }
    if (-not $SkipManifest) {
      $manifestPath = Join-Path $semRoot 'measures_manifest.json'
      Write-Manifest -Path $manifestPath -Manifest $manifest
    }

    if ($StubOnly) {
      Write-Host ("Generated stub measures for $useCaseId -> " + $generatedPath) -ForegroundColor Green
    } else {
      Write-Host ("Generated measures for $useCaseId -> " + $measuresPath) -ForegroundColor Green
    }
    $generated++
  }
}

if ($generated -eq 0) {
  Write-Host "No measures were generated. Ensure the requested UseCase IDs exist." -ForegroundColor Yellow
} else {
  Write-Host ("Completed measure generation for $generated use case(s).") -ForegroundColor Cyan
}

# ============================================================================
# ActionReady Logic: _ActionReady_Logic.tmdl (hidden action-text measures)
# ============================================================================
if (-not $SkipActionLogic -and $useCaseBrackets.Count -gt 0 -and $allActionCodes.Count -gt 0) {
  $actionResult = Build-ActionReadyLogicTable `
    -Brackets $useCaseBrackets `
    -ActionCodes $allActionCodes `
    -SelectedUseCases $selectedUseCaseFilters

  if ($actionResult.Content) {
    # Determine output directory
    $actionTargetDir = $null
    if ($resolvedTablesDir) {
      $actionTargetDir = $resolvedTablesDir
    } elseif ($resolvedDistRoot) {
      # In per-use-case mode, write to a shared location under dist
      $actionTargetDir = Join-Path $resolvedDistRoot '_shared'
      Ensure-Dir $actionTargetDir
    }

    if ($actionTargetDir) {
      $actionTmdlPath = Join-Path $actionTargetDir '_ActionReady_Logic.tmdl'
      $actionGeneratedPath = Join-Path $actionTargetDir '_ActionReady_Logic.generated.tmdl'

      if ($StubOnly) {
        Write-Utf8NoBom -Path $actionGeneratedPath -Text $actionResult.Content
        Write-Host ("Generated stub _ActionReady_Logic.tmdl with $($actionResult.Count) action measures -> " + $actionGeneratedPath) -ForegroundColor Green
      } else {
        Write-Utf8NoBom -Path $actionTmdlPath -Text $actionResult.Content
        Write-Host ("Generated _ActionReady_Logic.tmdl with $($actionResult.Count) action measures -> " + $actionTmdlPath) -ForegroundColor Green
      }

      # Add ref to model.tmdl if it exists in the same semantic model
      if (-not $StubOnly -and $resolvedTablesDir) {
        $modelPath = Join-Path (Split-Path -Parent $resolvedTablesDir) 'model.tmdl'
        if (Test-Path $modelPath) {
          $modelRaw = Get-Content -Raw -Path $modelPath
          if ($modelRaw -notmatch '(?m)^ref\s+table\s+_ActionReady_Logic\s*$') {
            $append = "ref table _ActionReady_Logic"
            Write-Utf8NoBom -Path $modelPath -Text ($modelRaw.TrimEnd() + [Environment]::NewLine + $append + [Environment]::NewLine)
            Write-Host "Added ref table _ActionReady_Logic to model.tmdl" -ForegroundColor Gray
          }
        }
      }
    } else {
      Write-Host "Skipping _ActionReady_Logic.tmdl - no output directory resolved." -ForegroundColor Yellow
    }
  } else {
    Write-Host "No action codes found for selected use cases - skipping _ActionReady_Logic.tmdl." -ForegroundColor Yellow
  }
} elseif (-not $SkipActionLogic) {
  if ($useCaseBrackets.Count -eq 0) {
    Write-Host "No UseCase_Bracket.yaml files found - skipping _ActionReady_Logic.tmdl generation." -ForegroundColor Yellow
  }
  if ($allActionCodes.Count -eq 0) {
    Write-Host "No action code YAMLs found - skipping _ActionReady_Logic.tmdl generation." -ForegroundColor Yellow
  }
}
