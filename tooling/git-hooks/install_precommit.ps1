# Aktiviert den versionierten pre-commit-Hook `.githooks/pre-commit` ueber
# `git config core.hooksPath .githooks` (seit 07.10.2026; vorher kopierte dieses Skript
# tooling/git-hooks/pre-commit nach .git/hooks -- die Tore sind jetzt in .githooks zusammengelegt).
#
# Idempotent: ein zweiter Lauf aendert nichts. Ein alter, kopierter Hook in .git/hooks/pre-commit
# wird nicht geloescht, sondern umbenannt (mit core.hooksPath laeuft er ohnehin nicht mehr).
# Ein bewusst gesetzter anderer lokaler core.hooksPath bleibt unangetastet, ausser mit -Force.
# Aufruf aus der Repo-Wurzel:  .\tooling\git-hooks\install_precommit.ps1 [-Force]

[CmdletBinding()]
param(
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Ziel = ".githooks"
$Altwert = "tooling/git-hooks"   # core.hooksPath, den der SessionStart bis 07.10.2026 setzte

function Invoke-Git {
    param([Parameter(Mandatory)][string[]]$Arguments)
    $out = & git @Arguments 2>$null
    return [pscustomobject]@{ Code = $LASTEXITCODE; Out = (($out | Out-String).Trim()) }
}

$top = Invoke-Git @("rev-parse", "--show-toplevel")
if ($top.Code -ne 0 -or -not $top.Out) {
    throw "Kein Git-Arbeitsbaum. Aus der Repo-Wurzel aufrufen."
}
$repoRoot = $top.Out

$hookFile = Join-Path (Join-Path $repoRoot $Ziel) "pre-commit"
if (-not (Test-Path -LiteralPath $hookFile -PathType Leaf)) {
    throw "Versionierter Hook fehlt: $hookFile"
}

# Python-Probe: der Hook braucht Python 3 (py-Launcher zuerst, wie im Hook selbst).
$pyCmd = $null
$kandidaten = @(, @("py", "-3")) + @(, @("python3")) + @(, @("python"))
foreach ($kandidat in $kandidaten) {
    if (-not (Get-Command $kandidat[0] -ErrorAction SilentlyContinue)) { continue }
    $exe = $kandidat[0]
    $rest = @($kandidat | Select-Object -Skip 1) + @("--version")
    try {
        $v = & $exe @rest 2>&1
        if ($LASTEXITCODE -eq 0 -and "$v" -match "Python 3") { $pyCmd = ($kandidat -join " "); break }
    } catch {
        continue
    }
}
if (-not $pyCmd) {
    throw "Python 3 nicht gefunden ('py -3', 'python3' oder 'python'). Der Hook bricht ohne Python jeden Commit ab; erst Python installieren."
}

# Alter, kopierter Hook im unversionierten Ordner: umbenennen statt loeschen. Der gemeinsame
# Git-Ordner, nicht --git-path hooks (das folgt bereits einem gesetzten core.hooksPath).
$common = Invoke-Git @("rev-parse", "--path-format=absolute", "--git-common-dir")
if ($common.Code -ne 0 -or -not $common.Out) { throw "git rev-parse --git-common-dir fehlgeschlagen." }
$legacyDir = Join-Path $common.Out "hooks"
$legacyHook = Join-Path $legacyDir "pre-commit"
if (Test-Path -LiteralPath $legacyHook -PathType Leaf) {
    $neu = "$legacyHook.vor-hooksPath-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Rename-Item -LiteralPath $legacyHook -NewName (Split-Path -Leaf $neu)
    Write-Warning "Alter Hook umbenannt: $legacyHook -> $neu. Er lief mit core.hooksPath ohnehin nicht mehr; alle seine Tore stehen in $Ziel/pre-commit. Loeschen, wenn nicht mehr gebraucht."
}
if (Test-Path -LiteralPath $legacyDir -PathType Container) {
    $andere = @(Get-ChildItem -LiteralPath $legacyDir -File |
        Where-Object { $_.Name -notlike "*.sample" -and $_.Name -notlike "pre-commit.vor-hooksPath-*" } |
        ForEach-Object { $_.Name })
    if ($andere.Count -gt 0) {
        Write-Warning "Weitere Hooks in $legacyDir werden durch core.hooksPath stillgelegt: $($andere -join ', '). Bei Bedarf nach $Ziel/ umziehen."
    }
}

$aktuell = Invoke-Git @("config", "--local", "--get", "core.hooksPath")
$wert = if ($aktuell.Code -eq 0) { $aktuell.Out } else { "" }
if ($wert -eq $Ziel) {
    Write-Host "core.hooksPath ist bereits $Ziel - nichts zu tun."
} elseif ($wert -and $wert -ne $Altwert -and -not $Force) {
    Write-Warning "Lokaler core.hooksPath ist '$wert' (bewusst gesetzt?) - nicht geaendert. Mit -Force auf $Ziel umstellen."
    exit 1
} else {
    $set = Invoke-Git @("config", "--local", "core.hooksPath", $Ziel)
    if ($set.Code -ne 0) { throw "git config core.hooksPath $Ziel fehlgeschlagen (Exit $($set.Code))." }
    $vorher = if ($wert) { $wert } else { "(leer)" }
    Write-Host "core.hooksPath: $vorher -> $Ziel"
}
Write-Host "Aktiver Hook: $hookFile (Python: $pyCmd)"
Write-Host "Tore: Drift-Gate, Kundenkennungen, Secret-Baseline, Ruff-Sperrklinke (.py), Ontologie-Registry (core/)."
