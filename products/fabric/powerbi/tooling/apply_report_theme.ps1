# Apply a custom theme to a PBIP report (wrapper for apply_report_theme.py).
# Works from any cwd (paths resolve against the cwd, the .py puts the repo root on sys.path). Usage:
#   .\products\fabric\powerbi\tooling\apply_report_theme.ps1 -Report "path\to\Report" -ThemePath "path\to\theme.json"
#   .\products\fabric\powerbi\tooling\apply_report_theme.ps1 -Report "path\to\Report" -ThemeName "Aurora Group__NeutralAccent__Light__#118DFF"
#   .\products\fabric\powerbi\tooling\apply_report_theme.ps1 -Report "path\to\Report" -SyncBaseTheme [-Check]   # base theme only (D-587)

param(
    [Parameter(Mandatory = $true)]
    [string] $Report,
    [string] $ThemePath,
    [string] $ThemeName,
    [switch] $RunGenerator,
    [string] $Color = "#118DFF",
    [string] $Concept = "Monochromatic",
    [string] $Mode = "Light",
    [string] $Brand = "Generic",
    [string] $Secondary,
    [string] $CustomName,
    [string] $BaseTheme,  # leer = Default aus tooling/report_quality/base_theme.py (D-587)
    [switch] $NoValidate,
    [switch] $SyncBaseTheme,  # nur Basis-Theme angleichen (--sync-base-theme), Custom Theme bleibt
    [switch] $Check           # mit -SyncBaseTheme: nichts schreiben, Exit 1 bei Drift
)

$pyScript = Join-Path $PSScriptRoot "apply_report_theme.py"

# Build script arguments (do not use $args - it is PowerShell's automatic variable and can cause wrong Python invocation)
$scriptArgs = @((Resolve-Path -LiteralPath $Report -ErrorAction Stop).Path)
if ($SyncBaseTheme) {
    $scriptArgs += "--sync-base-theme"
    if ($Check) { $scriptArgs += "--check" }
} elseif ($Check) {
    Write-Error "-Check is only valid with -SyncBaseTheme."
    exit 2
} elseif ($ThemePath) {
    $scriptArgs += "--theme-path", (Resolve-Path -LiteralPath $ThemePath).Path
} elseif ($ThemeName) {
    $scriptArgs += "--theme-name", $ThemeName
    if ($RunGenerator) { $scriptArgs += "--run-generator" }
    $scriptArgs += "--color", $Color, "--concept", $Concept, "--mode", $Mode, "--brand", $Brand
    if ($Secondary) { $scriptArgs += "--secondary", $Secondary }
} else {
    Write-Error "Provide -ThemePath, -ThemeName or -SyncBaseTheme."
    exit 2
}
if ($CustomName) { $scriptArgs += "--custom-name", $CustomName }
if ($BaseTheme) { $scriptArgs += "--base-theme", $BaseTheme }
if ($NoValidate) { $scriptArgs += "--no-validate" }

# Find Python 3: prefer py -3 (Windows), then python3, then python. Use only exe + script path + args (no -3 on invoke to avoid launcher passing wrong argv to python.exe).
$pyExe = $null
foreach ($c in @("py", "python3", "python")) {
    try {
        $v = & $c --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $v -match "Python 3") { $pyExe = $c; break }
    } catch { continue }
}
if (-not $pyExe) {
    Write-Error "Python 3 not found. Install Python 3 or ensure py/python3/python is in PATH."
    exit 2
}
# Invoke: exe, script path, script args (report path, --theme-name, ...). No version flag to avoid launcher argv issues.
& $pyExe $pyScript @scriptArgs
$pyExit = $LASTEXITCODE
if ($pyExit -ne 0) {
    Write-Warning "apply_report_theme.py failed with exit code $pyExit."
}
exit $pyExit
