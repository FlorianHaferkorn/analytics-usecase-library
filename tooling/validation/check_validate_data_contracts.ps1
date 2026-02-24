# Validate domain data contracts under core/data_contracts/domains/
# Writes tooling/validation/results/contract_validation.json with failed_contracts list.
# Exit 1 if any contract fails validation (used by Stage 1 and registry_builder).

param(
	[string]$Root = ".",
	[switch]$FailOnError
)

$ErrorActionPreference = "Stop"

function Resolve-RepoPath {
	param([string]$ProvidedPath, [string]$DefaultRelative)
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

$rootPath = Resolve-RepoPath -ProvidedPath $Root -DefaultRelative "."
if (-not $rootPath) { throw "Root path not found." }

# When ConvertFrom-Yaml is not available (e.g. CI without powershell-yaml), use Node + yaml package from tooling/validation
if (-not (Get-Command ConvertFrom-Yaml -ErrorAction SilentlyContinue)) {
	$validationDir = Join-Path -Path $rootPath -ChildPath "tooling\validation"
	Push-Location $validationDir
	try {
		& node validate_data_contracts.js $rootPath
		exit $LASTEXITCODE
	} finally {
		Pop-Location
	}
}

$contractsDir = Join-Path -Path $rootPath -ChildPath "core\data_contracts\domains"
$resultsDir = Join-Path -Path $rootPath -ChildPath "tooling\validation\results"
$outPath = Join-Path -Path $resultsDir -ChildPath "contract_validation.json"

$failedContracts = [System.Collections.Generic.List[string]]::new()

if (-not (Test-Path $contractsDir)) {
	# No domains folder: write empty result, exit 0 (nothing to validate)
	if (-not (Test-Path $resultsDir)) { New-Item -ItemType Directory -Path $resultsDir -Force | Out-Null }
	@{
		failed_contracts = @()
		timestamp        = (Get-Date -Format "o")
	} | ConvertTo-Json -Depth 2 | Set-Content -Path $outPath -Encoding utf8
	Write-Host "check_validate_data_contracts: no core/data_contracts/domains, skipped."
	exit 0
}

$yamlFiles = Get-ChildItem -Path $contractsDir -Filter "*.yaml" -File -ErrorAction SilentlyContinue
# #region agent log
$agentLogPath = Join-Path $rootPath "debug-0c8311.log"
$cmdletExists = (Get-Command ConvertFrom-Yaml -ErrorAction SilentlyContinue) -ne $null
$agentPayload = @{ sessionId = "0c8311"; runId = "run1"; hypothesisId = "H1"; location = "check_validate_data_contracts.ps1:before_loop"; message = "ConvertFrom-Yaml availability"; data = @{ cmdletExists = $cmdletExists; psVersion = $PSVersionTable.PSVersion.ToString(); psEdition = $PSVersionTable.PSEdition }; timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() } | ConvertTo-Json -Compress
Add-Content -Path $agentLogPath -Value $agentPayload -Encoding utf8 -ErrorAction SilentlyContinue
# #endregion agent log
foreach ($file in $yamlFiles) {
	$relPath = $file.FullName.Replace($rootPath + [IO.Path]::DirectorySeparatorChar, "").Replace("\", "/")
	$contractPath = "core/data_contracts/domains/$($file.Name)"
	$fileFailed = $false
	try {
		$raw = Get-Content -Path $file.FullName -Raw -Encoding UTF8
		$data = $raw | ConvertFrom-Yaml
		if (-not $data) {
			$fileFailed = $true
			Write-Host "FAIL $relPath : not a YAML object" -ForegroundColor Red
		} else {
			# Require at least domain or (dimension or fact)
			$hasDomain = $data.domain -ne $null
			$hasDimension = $data.dimension -ne $null
			$hasFact = $data.fact -ne $null
			if (-not ($hasDomain -or $hasDimension -or $hasFact)) {
				$fileFailed = $true
				Write-Host "FAIL $relPath : missing domain, dimension, or fact" -ForegroundColor Red
			}
			if (-not $fileFailed -and $data.dimension) {
				$dims = @($data.dimension)
				foreach ($d in $dims) {
					if (-not $d.name) {
						$fileFailed = $true
						Write-Host "FAIL $relPath : dimension entry missing name" -ForegroundColor Red
						break
					}
				}
			}
			if (-not $fileFailed -and $data.fact) {
				$facts = @($data.fact)
				foreach ($f in $facts) {
					if (-not $f.name) {
						$fileFailed = $true
						Write-Host "FAIL $relPath : fact entry missing name" -ForegroundColor Red
						break
					}
					if (-not $f.grain) {
						$fileFailed = $true
						Write-Host "FAIL $relPath : fact '$($f.name)' missing grain" -ForegroundColor Red
						break
					}
				}
			}
		}
	} catch {
		$fileFailed = $true
		Write-Host "FAIL $relPath : $($_.Exception.Message)" -ForegroundColor Red
	}
	if ($fileFailed) { $failedContracts.Add($contractPath) }
}

if (-not (Test-Path $resultsDir)) { New-Item -ItemType Directory -Path $resultsDir -Force | Out-Null }
$payload = @{
	failed_contracts = [string[]]$failedContracts
	timestamp        = (Get-Date -Format "o")
}
$payload | ConvertTo-Json -Depth 2 | Set-Content -Path $outPath -Encoding utf8

if ($failedContracts.Count -gt 0) {
	Write-Host "check_validate_data_contracts: $($failedContracts.Count) failed contract(s). Results: $outPath" -ForegroundColor Red
	if ($FailOnError) { exit 1 }
	exit 1
}

Write-Host "check_validate_data_contracts: all domain contracts valid. Results: $outPath" -ForegroundColor Green
exit 0
