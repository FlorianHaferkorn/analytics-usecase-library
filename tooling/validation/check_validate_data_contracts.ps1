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
foreach ($c in @("py -3", "python3", "python")) {
	$parts = $c -split " "
	if (-not (Get-Command $parts[0] -ErrorAction SilentlyContinue)) { continue }
	try {
		$versionArgs = @()
		if ($parts.Count -gt 1) {
			$versionArgs += $parts[1..($parts.Count - 1)]
		}
		$versionArgs += "--version"
		$output = & $parts[0] $versionArgs 2>&1 | Out-String
		if ($LASTEXITCODE -eq 0 -and $output -match "Python 3") {
			$pyExe = $c
			break
		}
	} catch {
		continue
	}
}
if (-not $pyExe) { Write-Error "Python 3 not found. Install Python 3 or ensure 'py -3' resolves to a working interpreter; ignore broken Microsoft Store 'python' aliases." }

$pyArgs = @("--root", $rootPath)
if ($FailOnError) { $pyArgs += "--fail-on-error" }

if ($pyExe -match " ") {
	$allArgs = ($pyExe -split " ") + @($pyScript) + $pyArgs
	& $allArgs[0] $allArgs[1..($allArgs.Count - 1)]
} else {
	& $pyExe $pyScript @pyArgs
}
exit $LASTEXITCODE
