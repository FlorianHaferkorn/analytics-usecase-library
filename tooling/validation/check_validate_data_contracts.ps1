# Validate domain data contracts (delegates to Python). Used by Stage 1 and registry_builder.
# Requires: Python with PyYAML (pip install -r tooling/validation/requirements-data-contracts.txt).

param(
	[string]$Root = ".",
	[switch]$FailOnError
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Get-Location).Path
if ($Root -and (Test-Path $Root)) {
	$rootPath = (Resolve-Path -Path $Root).Path
} elseif ($Root) {
	$candidate = Join-Path -Path $repoRoot -ChildPath $Root
	if (Test-Path $candidate) { $rootPath = (Resolve-Path -Path $candidate).Path } else { $rootPath = $repoRoot }
} else {
	$rootPath = $repoRoot
}

$pyScript = Join-Path -Path $scriptDir -ChildPath "check_validate_data_contracts.py"
if (-not (Test-Path -LiteralPath $pyScript)) { Write-Error "Missing: check_validate_data_contracts.py" }

$pyExe = $null
foreach ($c in @("python", "python3", "py -3")) {
	$parts = $c -split " "
	if (Get-Command $parts[0] -ErrorAction SilentlyContinue) { $pyExe = $c; break }
}
if (-not $pyExe) { Write-Error "Python not found. Install Python 3 or ensure 'py -3' or 'python' is on PATH." }

$pyArgs = @("--root", $rootPath)
if ($FailOnError) { $pyArgs += "--fail-on-error" }

$allArgs = ($pyExe -split " ") + @($pyScript) + $pyArgs
& $allArgs[0] $allArgs[1..($allArgs.Count - 1)]
exit $LASTEXITCODE
