<#
.SYNOPSIS
  Startet Power BI Desktop fuer PBIP-Artefakte und optional temporaere PBIX-Validierungsartefakte und wertet neue Trace-Fehler aus.

.DESCRIPTION
  Der Smoke-Test ist ein lokaler Runtime-Check fuer "oeffnet in Desktop ohne frische Fehler".
  Fuer jedes uebergebene Artefakt wird Power BI Desktop gestartet, eine kurze Anlaufphase abgewartet,
  neue Zeilen aus PBIDesktop.log seit dem Start gelesen und auf Fehler/Frown/Exceptions gefiltert.

.PARAMETER ArtifactPaths
  Eine oder mehrere PBIP/PBIR-Pfade sowie optional temporaere PBIX-Validierungsartefakte. Relative Pfade sind relativ zum Repo-Root.

.PARAMETER TimeoutSeconds
  Wartefenster pro Artefakt, in dem neue Desktop-Trace-Eintraege eingesammelt werden.

.PARAMETER KeepDesktopOpen
  Beendet Desktop nach jedem Artefakt standardmaessig. Mit diesem Schalter bleibt Desktop offen.

.PARAMETER ResultFile
  Optionaler JSON-Output mit Detailergebnissen.
#>

param(
  [Parameter(Mandatory = $true)]
  [string[]] $ArtifactPaths,
  [string] $RepoRoot = "",
  [int] $TimeoutSeconds = 30,
  [switch] $KeepDesktopOpen,
  [string] $ResultFile = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = Split-Path -Path $PSScriptRoot -Parent
}

function Resolve-DesktopExecutablePath {
  $commands = @(
    (Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue),
    (Get-Command PBIDesktopStore.exe -ErrorAction SilentlyContinue)
  ) | Where-Object { $_ }

  if ($commands.Count -gt 0) {
    return $commands[0].Source
  }

  $candidates = @(
    (Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\PBIDesktopStore.exe"),
    (Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\PBIDesktop.exe"),
    (Join-Path $env:ProgramFiles "Microsoft Power BI Desktop\bin\PBIDesktop.exe")
  )

  foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path $candidate)) {
      return (Resolve-Path -Path $candidate).Path
    }
  }

  throw "Power BI Desktop executable not found. Checked PATH and common WindowsApps locations."
}

function Resolve-ArtifactPath {
  param([string] $PathValue)

  if ([System.IO.Path]::IsPathRooted($PathValue)) {
    $resolved = $PathValue
  } else {
    $resolved = Join-Path $RepoRoot ($PathValue -replace '/', [IO.Path]::DirectorySeparatorChar)
  }

  if (-not (Test-Path $resolved)) {
    throw "Artifact not found: $resolved"
  }

  return (Resolve-Path -Path $resolved).Path
}

function Read-FileSegment {
  param(
    [string] $Path,
    [long] $Offset
  )

  if (-not (Test-Path $Path)) { return "" }

  $fileInfo = Get-Item -LiteralPath $Path
  if ($fileInfo.Length -le $Offset) { return "" }

  $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
  try {
    $stream.Seek($Offset, [System.IO.SeekOrigin]::Begin) | Out-Null
    $reader = New-Object System.IO.StreamReader($stream)
    try {
      return $reader.ReadToEnd()
    } finally {
      $reader.Dispose()
    }
  } finally {
    $stream.Dispose()
  }
}

function Get-TraceErrorLines {
  param([string] $TraceText)

  if ([string]::IsNullOrWhiteSpace($TraceText)) { return @() }

  $regexes = @(
    [regex]'(?i)\berror\b',
    [regex]'(?i)\bexception\b',
    [regex]'(?i)\bfrown\b',
    [regex]'(?i)DataSource\.Error',
    [regex]'(?i)Unhandled'
  )

  return @(
    $TraceText -split "`r?`n" |
      ForEach-Object { $_.Trim() } |
      Where-Object {
        $line = $_
        $line -and (@($regexes | Where-Object { $_.IsMatch($line) }).Count -gt 0)
      }
  )
}

$desktopExe = Resolve-DesktopExecutablePath
$tracePath = Join-Path $env:LOCALAPPDATA "Microsoft\Power BI Desktop\Traces\PBIDesktop.log"
$results = [System.Collections.ArrayList]::new()

foreach ($artifact in $ArtifactPaths) {
  $resolvedArtifact = Resolve-ArtifactPath -PathValue $artifact
  if (Test-Path $tracePath) {
    $traceOffset = (Get-Item -LiteralPath $tracePath).Length
  } else {
    $traceOffset = 0L
  }
  $startedAt = Get-Date
  $process = Start-Process -FilePath $desktopExe -ArgumentList @($resolvedArtifact) -PassThru

  $deadline = $startedAt.AddSeconds([Math]::Max($TimeoutSeconds, 5))
  do {
    Start-Sleep -Seconds 2
    $traceReady = (Test-Path $tracePath) -and ((Get-Item -LiteralPath $tracePath).Length -gt $traceOffset)
    if ($traceReady -and ((Get-Date) -ge $startedAt.AddSeconds(8))) {
      break
    }
  } while ((Get-Date) -lt $deadline)

  $traceText = Read-FileSegment -Path $tracePath -Offset $traceOffset
  $errorLines = Get-TraceErrorLines -TraceText $traceText

  if (-not $KeepDesktopOpen -and -not $process.HasExited) {
    try { Stop-Process -Id $process.Id -Force -ErrorAction Stop } catch {}
  }

  [void]$results.Add(@{
    artifact = $resolvedArtifact
    startedAt = $startedAt.ToString('o')
    desktopProcessId = $process.Id
    traceUpdated = -not [string]::IsNullOrWhiteSpace($traceText)
    success = ($errorLines.Count -eq 0)
    errors = @($errorLines | Select-Object -First 50)
  })
}

$success = (@($results | Where-Object { -not $_.success }).Count -eq 0)
$resultObject = @{
  success = $success
  desktopExecutable = $desktopExe
  tracePath = $tracePath
  artifacts = @($results)
  timestamp = (Get-Date).ToString('o')
}

$resultJson = $resultObject | ConvertTo-Json -Depth 6

if ($ResultFile) {
  if ([System.IO.Path]::IsPathRooted($ResultFile)) {
    $resolvedResultFile = $ResultFile
  } else {
    $resolvedResultFile = Join-Path $RepoRoot ($ResultFile -replace '/', [IO.Path]::DirectorySeparatorChar)
  }
  $resultDir = Split-Path -Parent $resolvedResultFile
  if ($resultDir -and -not (Test-Path $resultDir)) {
    New-Item -ItemType Directory -Path $resultDir -Force | Out-Null
  }
  $resultJson | Set-Content -Path $resolvedResultFile -Encoding utf8
}

Write-Output $resultJson
if (-not $success) { exit 1 }
exit 0