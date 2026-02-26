# Apply a custom theme to a PBIP report (wrapper for apply_report_theme.py).
# Run from repo root. Usage:
#   .\products\fabric_powerbi\tooling\apply_report_theme.ps1 -Report "path\to\Report" -ThemePath "path\to\theme.json"
#   .\products\fabric_powerbi\tooling\apply_report_theme.ps1 -Report "path\to\Report" -ThemeName "Aurora Group__NeutralAccent__Light__#118DFF"

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
    [string] $BaseTheme = "CY25SU10",
    [switch] $NoValidate
)

$scriptDir = Split-Path -LiteralPath $MyInvocation.MyCommand.Path
$pyScript = Join-Path $scriptDir "apply_report_theme.py"

$args = @($Report)
if ($ThemePath) {
    $args += "--theme-path", (Resolve-Path -LiteralPath $ThemePath).Path
} elseif ($ThemeName) {
    $args += "--theme-name", $ThemeName
    if ($RunGenerator) { $args += "--run-generator" }
    $args += "--color", $Color, "--concept", $Concept, "--mode", $Mode, "--brand", $Brand
    if ($Secondary) { $args += "--secondary", $Secondary }
} else {
    Write-Error "Provide -ThemePath or -ThemeName."
    exit 1
}
if ($CustomName) { $args += "--custom-name", $CustomName }
if ($BaseTheme) { $args += "--base-theme", $BaseTheme }
if ($NoValidate) { $args += "--no-validate" }

# Prefer py -3 (Windows) so orchestrator and manual runs succeed when python is not in PATH
$pyExe = "python"
$pyExeArgs = @()
foreach ($c in @("py -3", "python3", "python")) {
    $parts = $c -split " "
    try {
        $v = & $parts[0] @($parts[1..99] | Where-Object { $_ }) --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $v -match "Python 3") { $pyExe = $parts[0]; $pyExeArgs = @($parts[1..99] | Where-Object { $_ }); break }
    } catch { continue }
}
& $pyExe @$pyExeArgs $pyScript @args
exit $LASTEXITCODE
