# Power BI Report Validator (PBIR)
# Purpose: Validate a PBIR report's pages and visuals against bpa-rules-report.json
#          and the ALUCA canvas tokens (core/templates/page_templates/tokens/layout_grid.yaml).
# Usage:   .\validate_report.ps1 -ReportPath "path\to\X.Report" [-BpaRulesPath ...] [-LayoutGridPath ...]
#
# Rules and where their thresholds come from (no threshold is a literal in this script):
#   REDUCE_PAGES                          bpa-rules-report.json, test '<=' operand (10)
#   REDUCE_VISUALS_ON_PAGE                bpa-rules-report.json, paramMaxVisualsPerPage (20) and the
#                                         excluded visualType list (shape, slicer, actionButton, textbox);
#                                         same limit in Design_Spec_3_30_300.md section 10
#   ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY layout_grid.yaml canvas.design_base / canvas.production
#                                         (decision Florian 01.10.2026: ALUCA canvases, not the 720 px
#                                         Power BI default); Design_Spec_3_30_300.md section 10
#   ENSURE_ALTTEXT                        bpa-rules-report.json, excluded visualType list (shape)
# Every rule honours its 'disabled' flag in bpa-rules-report.json (listed under Disabled).
# A rule whose input is missing is listed under NotEvaluated, never reported as "0 findings".

param(
	[Parameter(Mandatory=$true)]
	[string]$ReportPath,

	[string]$BpaRulesPath = "",

	[string]$LayoutGridPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Exit-WithError {
	param([string]$Message)
	$Host.UI.WriteErrorLine($Message)
	exit 1
}

if (-not $BpaRulesPath) {
	$BpaRulesPath = [System.IO.Path]::Combine($PSScriptRoot, "..", "linters", "powerbi", "bpa-rules-report.json")
}
if (-not $LayoutGridPath) {
	$LayoutGridPath = [System.IO.Path]::Combine($PSScriptRoot, "..", "..", "core", "templates", "page_templates",
		"tokens", "layout_grid.yaml")
}

# Load BPA Rules
if (-not (Test-Path -LiteralPath $BpaRulesPath)) {
	Exit-WithError "BPA Rules not found: $BpaRulesPath"
}

$bpaRules = Get-Content -LiteralPath $BpaRulesPath -Raw -Encoding utf8 | ConvertFrom-Json

# Validation Results
$results = @{
	IsValid = $true
	Errors = @()
	Warnings = @()
	Info = @()
	Evaluated = @()
	NotEvaluated = @()
	Disabled = @()
}

# --- JSON helpers (StrictMode-safe property access) -------------------------------------------

function Get-Prop {
	param($Object, [string]$Name)
	if ($null -eq $Object) { return $null }
	if ($Object -is [System.Management.Automation.PSCustomObject]) {
		$p = $Object.PSObject.Properties[$Name]
		if ($p) { return $p.Value }
	}
	return $null
}

function Read-JsonFile {
	param([string]$Path)
	return (Get-Content -LiteralPath $Path -Raw -Encoding utf8 | ConvertFrom-Json)
}

function Add-NotEvaluated {
	param([string]$RuleId, [string]$Reason)
	$script:results.NotEvaluated += @{ RuleId = $RuleId; Reason = $Reason }
	Write-Warning "$RuleId not evaluated: $Reason"
}

# --- BPA rule file readers --------------------------------------------------------------------

function Get-BpaRule {
	param([string]$Id)
	foreach ($r in @(Get-Prop $bpaRules "rules")) {
		if ((Get-Prop $r "id") -eq $Id) { return $r }
	}
	return $null
}

# Depth-first search for the first JSON-logic node that carries operator $Op.
function Find-LogicNode {
	param($Node, [string]$Op)
	if ($null -eq $Node) { return $null }
	if ($Node -is [System.Management.Automation.PSCustomObject]) {
		if ($Node.PSObject.Properties[$Op]) { return $Node }
		foreach ($p in $Node.PSObject.Properties) {
			$hit = Find-LogicNode -Node $p.Value -Op $Op
			if ($null -ne $hit) { return $hit }
		}
	} elseif ($Node -is [System.Array]) {
		foreach ($item in $Node) {
			$hit = Find-LogicNode -Node $item -Op $Op
			if ($null -ne $hit) { return $hit }
		}
	}
	return $null
}

# The rule's excluded visual types: the array operand of {"in": [{"var": "visual.visualType"}, [...]]}.
function Get-ExcludedVisualTypes {
	param($Rule)
	$inNode = Find-LogicNode -Node (Get-Prop $Rule "test") -Op "in"
	if ($null -eq $inNode) { return $null }
	$operands = @($inNode.in)
	if ($operands.Count -ne 2) { return $null }
	if ((Get-Prop $operands[0] "var") -ne "visual.visualType") { return $null }
	return ,@($operands[1] | ForEach-Object { [string]$_ })
}

function Test-RuleDisabled {
	param($Rule, [string]$RuleId)
	if ((Get-Prop $Rule "disabled") -eq $true) {
		$script:results.Disabled += @{ RuleId = $RuleId; Source = $BpaRulesPath }
		Write-Host "  $RuleId disabled in bpa-rules-report.json (disabled: true), not run." -ForegroundColor DarkGray
		return $true
	}
	return $false
}

# --- Canvas tokens (layout_grid.yaml) -----------------------------------------------------------
# YAML is read by Python (PyYAML), as in check_validate_data_contracts.ps1: no powershell-yaml module.

function Get-PythonExe {
	foreach ($c in @("python", "python3", "py -3")) {
		$parts = $c -split " "
		if (-not (Get-Command $parts[0] -ErrorAction SilentlyContinue)) { continue }
		try {
			$versionArgs = @()
			if ($parts.Count -gt 1) { $versionArgs += $parts[1..($parts.Count - 1)] }
			$versionArgs += "--version"
			$output = & $parts[0] $versionArgs 2>&1 | Out-String
			if ($LASTEXITCODE -eq 0 -and $output -match "Python 3") { return $c }
		} catch {
			continue
		}
	}
	return $null
}

function Get-LayoutCanvases {
	param([string]$Path)
	if (-not (Test-Path -LiteralPath $Path)) {
		return @{ Canvases = $null; Reason = "layout_grid.yaml not found: $Path" }
	}
	$pyExe = Get-PythonExe
	if (-not $pyExe) {
		return @{ Canvases = $null; Reason = "Python 3 not found (needed to read layout_grid.yaml)" }
	}
	$parts = $pyExe -split " "
	$code = "import json,sys,yaml; d=yaml.safe_load(open(sys.argv[1],encoding='utf-8')); print(json.dumps((d or {}).get('canvas')))"
	$pyArgs = @()
	if ($parts.Count -gt 1) { $pyArgs += $parts[1..($parts.Count - 1)] }
	$pyArgs += @("-c", $code, $Path)
	$prevPref = $ErrorActionPreference
	$ErrorActionPreference = "Continue"
	$raw = & $parts[0] $pyArgs 2>&1 | Out-String
	$rc = $LASTEXITCODE
	$ErrorActionPreference = $prevPref
	if ($rc -ne 0) {
		return @{ Canvases = $null; Reason = "reading layout_grid.yaml failed (PyYAML installed?): $($raw.Trim())" }
	}
	$canvasObj = $raw | ConvertFrom-Json
	$canvases = @()
	foreach ($name in @("design_base", "production")) {
		$c = Get-Prop $canvasObj $name
		$w = (Get-Prop $c "width") -as [double]
		$h = (Get-Prop $c "height") -as [double]
		if ($null -ne $w -and $null -ne $h -and $w -gt 0 -and $h -gt 0) {
			$canvases += @{ Name = $name; Width = $w; Height = $h }
		}
	}
	if ($canvases.Count -eq 0) {
		return @{ Canvases = $null; Reason = "layout_grid.yaml carries no canvas.design_base/production width+height" }
	}
	return @{ Canvases = $canvases; Reason = "" }
}

# --- PBIR readers -------------------------------------------------------------------------------

# PBIR only (Florian, 01.10.2026). Learn power-bi/developer/projects/projects-report
# (read 01.10.2026): a root report.json holds "the Power BI Report Legacy format
# (PBIR-Legacy)"; the definition\ folder "replaces the report.json file". A root
# report.json is therefore an error, never a fallback.
function Get-ReportJson {
	param([string]$ReportPath)

	$legacyPath = Join-Path $ReportPath "report.json"
	if (Test-Path -LiteralPath $legacyPath) {
		Exit-WithError ("PBIR-Legacy wird nicht mehr akzeptiert: $legacyPath. " +
			"In Power BI Desktop als PBIR speichern (Learn power-bi/developer/projects/projects-report).")
	}

	$reportJsonPath = Join-Path (Join-Path $ReportPath "definition") "report.json"
	if (-not (Test-Path -LiteralPath $reportJsonPath)) {
		Exit-WithError "PBIR definition\report.json not found in: $ReportPath"
	}

	return Read-JsonFile $reportJsonPath
}

# Pages: definition\pages\<name>\page.json, ordered by pages.json pageOrder; pages missing from
# pageOrder follow by displayName (pagesMetadata 1.1.0 schema, pageOrder description).
function Get-PbirPages {
	param([string]$PagesDir)
	$pages = @()
	foreach ($dir in @(Get-ChildItem -LiteralPath $PagesDir -Directory)) {
		$pageJsonPath = Join-Path $dir.FullName "page.json"
		if (-not (Test-Path -LiteralPath $pageJsonPath)) { continue }
		$pages += @{ Dir = $dir.FullName; Json = (Read-JsonFile $pageJsonPath) }
	}

	$order = @()
	$metaPath = Join-Path $PagesDir "pages.json"
	if (Test-Path -LiteralPath $metaPath) {
		$order = @(Get-Prop (Read-JsonFile $metaPath) "pageOrder")
	}
	$ordered = @()
	foreach ($name in $order) {
		$ordered += @($pages | Where-Object { (Get-Prop $_.Json "name") -eq $name })
	}
	$ordered += @($pages | Where-Object { $order -notcontains (Get-Prop $_.Json "name") } |
		Sort-Object { [string](Get-Prop $_.Json "displayName") })
	return ,$ordered
}

# Visual containers of one page: definition\pages\<page>\visuals\<name>\visual.json.
# A container with 'visualGroup' is a group, not a visual (visualContainer 2.9.0 schema). A visual
# is hidden if it or any ancestor group (parentGroupName chain) has isHidden = true.
function Get-PbirVisuals {
	param([string]$PageDir)
	$visualsDir = Join-Path $PageDir "visuals"
	$byName = @{}
	if (Test-Path -LiteralPath $visualsDir) {
		foreach ($dir in @(Get-ChildItem -LiteralPath $visualsDir -Directory)) {
			$visualJsonPath = Join-Path $dir.FullName "visual.json"
			if (-not (Test-Path -LiteralPath $visualJsonPath)) { continue }
			$json = Read-JsonFile $visualJsonPath
			$name = [string](Get-Prop $json "name")
			if (-not $name) { $name = $dir.Name }
			$byName[$name] = $json
		}
	}

	$visuals = @()
	foreach ($name in @($byName.Keys | Sort-Object)) {
		$json = $byName[$name]
		$hidden = $false
		$cursor = $json
		$seen = @{}
		while ($null -ne $cursor) {
			if ((Get-Prop $cursor "isHidden") -eq $true) { $hidden = $true; break }
			$parent = [string](Get-Prop $cursor "parentGroupName")
			if (-not $parent -or $seen.ContainsKey($parent) -or -not $byName.ContainsKey($parent)) { break }
			$seen[$parent] = $true
			$cursor = $byName[$parent]
		}
		$visualCfg = Get-Prop $json "visual"
		$visuals += @{
			Name = $name
			IsGroup = ($null -ne (Get-Prop $json "visualGroup"))
			IsHidden = $hidden
			VisualType = [string](Get-Prop $visualCfg "visualType")
			Visual = $visualCfg
		}
	}
	return ,$visuals
}

# Alt text location: visual.visualContainerObjects.general[].properties.altText
# (visualConfiguration 2.3.0 schema: VisualContainerFormattingObjects.general ->
# VisualContainerGeneralFormattingObjects.altText; same path as the PBI Inspector rule in
# bpa-rules-report.json). A literal "''" is empty; any non-literal expression (measure,
# aggregation = conditional alt text, Learn desktop-accessibility-creating-reports) counts as set.
function Test-HasAltText {
	param($VisualCfg)
	$vco = Get-Prop $VisualCfg "visualContainerObjects"
	foreach ($entry in @(Get-Prop $vco "general")) {
		$alt = Get-Prop (Get-Prop $entry "properties") "altText"
		if ($null -eq $alt) { continue }
		$expr = Get-Prop $alt "expr"
		if ($null -eq $expr) { continue }
		$literal = Get-Prop $expr "Literal"
		if ($null -eq $literal) { return $true }
		$value = [string](Get-Prop $literal "Value")
		if ($value -and $value -ne "''") { return $true }
	}
	return $false
}

# --- Run ------------------------------------------------------------------------------------------

Write-Host "Validating Power BI report: $ReportPath" -ForegroundColor Cyan

$null = Get-ReportJson -ReportPath $ReportPath
$ruleIds = @("REDUCE_PAGES", "REDUCE_VISUALS_ON_PAGE", "ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY", "ENSURE_ALTTEXT")
$pagesDir = Join-Path (Join-Path $ReportPath "definition") "pages"
$pages = @()
$pagesFound = Test-Path -LiteralPath $pagesDir
if ($pagesFound) {
	$pages = Get-PbirPages -PagesDir $pagesDir
} else {
	foreach ($id in $ruleIds) {
		Add-NotEvaluated -RuleId $id -Reason "definition\pages not found in $ReportPath"
	}
}

# Resolve each rule: missing / disabled / thresholds unreadable -> not run.
$run = @{}
foreach ($id in $ruleIds) { $run[$id] = $false }
$maxPages = $null
$maxVisuals = $null
$visualsExcluded = @()
$altExcluded = @()
$canvases = @()

if ($pagesFound) {
	foreach ($id in $ruleIds) {
		$rule = Get-BpaRule $id
		if ($null -eq $rule) {
			Add-NotEvaluated -RuleId $id -Reason "rule missing in $BpaRulesPath"
			continue
		}
		if (Test-RuleDisabled -Rule $rule -RuleId $id) { continue }
		switch ($id) {
			"REDUCE_PAGES" {
				$le = Find-LogicNode -Node (Get-Prop $rule "test") -Op "<="
				if ($null -ne $le -and @($le.'<=').Count -eq 2) { $maxPages = @($le.'<=')[1] -as [int] }
				if ($null -eq $maxPages) {
					Add-NotEvaluated -RuleId $id -Reason "no numeric '<=' threshold in the rule test"
				} else { $run[$id] = $true }
			}
			"REDUCE_VISUALS_ON_PAGE" {
				$test = @(Get-Prop $rule "test")
				if ($test.Count -ge 2) { $maxVisuals = (Get-Prop $test[1] "paramMaxVisualsPerPage") -as [int] }
				$visualsExcluded = Get-ExcludedVisualTypes -Rule $rule
				if ($null -eq $maxVisuals -or $null -eq $visualsExcluded) {
					Add-NotEvaluated -RuleId $id -Reason "paramMaxVisualsPerPage or the visualType exclusion list not found in the rule"
				} else { $run[$id] = $true }
			}
			"ENSURE_ALTTEXT" {
				$altExcluded = Get-ExcludedVisualTypes -Rule $rule
				if ($null -eq $altExcluded) {
					Add-NotEvaluated -RuleId $id -Reason "visualType exclusion list not found in the rule"
				} else { $run[$id] = $true }
			}
			"ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY" {
				# The 720 px literal in the BPA rule is replaced by the ALUCA canvases (layout_grid.yaml).
				$canvasRead = Get-LayoutCanvases -Path $LayoutGridPath
				if ($null -eq $canvasRead.Canvases) {
					Add-NotEvaluated -RuleId $id -Reason $canvasRead.Reason
				} else {
					$canvases = $canvasRead.Canvases
					$run[$id] = $true
				}
			}
		}
	}
}

# Evaluated rules with the thresholds they ran on: "0 findings" is only meaningful next to this list.
$thresholds = @{
	"REDUCE_PAGES" = "max $maxPages pages (bpa-rules-report.json)"
	"REDUCE_VISUALS_ON_PAGE" = "max $maxVisuals visuals/page without [$($visualsExcluded -join ', ')] (bpa-rules-report.json)"
	"ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY" = "canvases [$(@($canvases | ForEach-Object { "$($_.Name) $($_.Width)x$($_.Height)" }) -join ', ')] (layout_grid.yaml)"
	"ENSURE_ALTTEXT" = "all visible visuals without [$($altExcluded -join ', ')] (bpa-rules-report.json)"
}
foreach ($id in $ruleIds) {
	if ($run[$id]) { $results.Evaluated += @{ RuleId = $id; Threshold = $thresholds[$id] } }
}

# Rule: REDUCE_PAGES -- every page definition counts (BPA rule counts part 'Pages', no visibility filter)
if ($run["REDUCE_PAGES"] -and $pages.Count -gt $maxPages) {
	$results.IsValid = $false
	$results.Errors += @{
		RuleId = "REDUCE_PAGES"
		RuleName = "Reduce number of pages per report"
		Severity = "error"
		Description = "Report has $($pages.Count) pages, maximum allowed is $maxPages"
		Value = $pages.Count
		Threshold = $maxPages
	}
}

$maxRatio = 0.0
$maxCanvasHeight = 0.0
$canvasText = ""
if ($run["ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY"]) {
	foreach ($c in $canvases) {
		$maxRatio = [Math]::Max($maxRatio, $c.Height / $c.Width)
		$maxCanvasHeight = [Math]::Max($maxCanvasHeight, $c.Height)
	}
	$canvasText = (@($canvases | ForEach-Object { "$($_.Name) $($_.Width)x$($_.Height)" }) -join ", ")
}

foreach ($page in $pages) {
	$pj = $page.Json
	$pageLabel = [string](Get-Prop $pj "displayName")
	if (-not $pageLabel) { $pageLabel = [string](Get-Prop $pj "name") }
	$visuals = Get-PbirVisuals -PageDir $page.Dir
	$shown = @($visuals | Where-Object { -not $_.IsGroup -and -not $_.IsHidden })

	# Rule: REDUCE_VISUALS_ON_PAGE -- visible non-group visuals minus the BPA-excluded types.
	# Groups are containers, not visuals: their visible children are counted one by one.
	if ($run["REDUCE_VISUALS_ON_PAGE"]) {
		$counted = @($shown | Where-Object { $visualsExcluded -notcontains $_.VisualType })
		if ($counted.Count -gt $maxVisuals) {
			$results.Warnings += @{
				RuleId = "REDUCE_VISUALS_ON_PAGE"
				RuleName = "Reduce the number of visible visuals on the page"
				Severity = "warning"
				Page = $pageLabel
				Description = "Page has $($counted.Count) visible visuals (without $($visualsExcluded -join ', ')), recommended maximum is $maxVisuals"
				Value = $counted.Count
				Threshold = $maxVisuals
			}
		}
	}

	# Rule: ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY (visible pages; tooltip pages are overlays, not views)
	# displayOption semantics (page 2.1.0 schema, PageDisplayOption; Learn explore-reports/end-user-report-view):
	#   FitToPage  -- "scaled so both width and height fit on the current viewport"; Learn: no scroll bars.
	#                 A page taller than the canvas ratio is shrunk instead -> Info, not Warning.
	#   FitToWidth -- "height will be updated to maintain page aspect ratio"; Learn: "you might need to use
	#                 the vertical scroll bar". ANNAHME: the viewport has the canvas aspect ratio (16:9).
	#   ActualSize(TopLeft) -- no scaling. ANNAHME: the viewport is the largest ALUCA canvas.
	#   DeprecatedDynamic / no fixed size -- not evaluated for this page.
	$visibility = [string](Get-Prop $pj "visibility")
	$pageType = [string](Get-Prop $pj "type")
	if ($run["ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY"] -and $visibility -ne "HiddenInViewMode" -and $pageType -ne "Tooltip") {
		$w = (Get-Prop $pj "width") -as [double]
		$h = (Get-Prop $pj "height") -as [double]
		$display = [string](Get-Prop $pj "displayOption")
		if ($null -eq $w -or $null -eq $h -or $w -le 0 -or $h -le 0 -or $display -eq "DeprecatedDynamic") {
			Add-NotEvaluated -RuleId "ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY" -Reason "page '$pageLabel': no fixed width/height (displayOption '$display')"
		} else {
			$isCanvas = @($canvases | Where-Object { $_.Width -eq $w -and $_.Height -eq $h }).Count -gt 0
			$maxH = [Math]::Floor($w * $maxRatio + 1e-6)
			$ratioOk = $isCanvas -or ($h -le $maxH)
			$soll = "Soll: Leinwand ($canvasText) oder Hoehe <= Breite x $([Math]::Round($maxRatio, 4)) = $maxH px"
			$finding = $null
			if ($display -eq "FitToPage") {
				if (-not $ratioOk) {
					$results.Info += @{
						RuleId = "ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY"
						RuleName = "Ensure pages do not scroll vertically"
						Severity = "info"
						Page = $pageLabel
						Description = "Page ${w}x${h} (FitToPage) does not scroll but is shrunk to fit; $soll"
						Value = $h
						Threshold = $maxH
					}
				}
			} elseif ($display -eq "FitToWidth") {
				if (-not $ratioOk) { $finding = "Page ${w}x${h} (FitToWidth) scrolls vertically; $soll" }
			} elseif ($display -eq "ActualSize" -or $display -eq "ActualSizeTopLeft") {
				if (-not $ratioOk -or $h -gt $maxCanvasHeight) {
					$finding = "Page ${w}x${h} ($display, no scaling) scrolls vertically; $soll and Hoehe <= $maxCanvasHeight px"
				}
			} else {
				Add-NotEvaluated -RuleId "ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY" -Reason "page '$pageLabel': unknown displayOption '$display'"
			}
			if ($finding) {
				$results.Warnings += @{
					RuleId = "ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY"
					RuleName = "Ensure pages do not scroll vertically"
					Severity = "warning"
					Page = $pageLabel
					Description = $finding
					Value = $h
					Threshold = $maxH
				}
			}
		}
	}

	# Rule: ENSURE_ALTTEXT -- visible non-group visuals minus the BPA-excluded types (shape)
	if ($run["ENSURE_ALTTEXT"]) {
		foreach ($v in @($shown | Where-Object { $altExcluded -notcontains $_.VisualType })) {
			if (-not (Test-HasAltText -VisualCfg $v.Visual)) {
				$results.Info += @{
					RuleId = "ENSURE_ALTTEXT"
					RuleName = "Ensure alternativeText has been defined for all visuals"
					Severity = "info"
					Page = $pageLabel
					Visual = $v.Name
					Description = "Visual $($v.Name) ($($v.VisualType)) missing alt-text for accessibility"
				}
			}
		}
	}
}

# Output results
Write-Host "`nValidation Results:" -ForegroundColor Cyan
Write-Host "  Errors: $($results.Errors.Count)" -ForegroundColor $(if ($results.Errors.Count -gt 0) { "Red" } else { "Green" })
Write-Host "  Warnings: $($results.Warnings.Count)" -ForegroundColor $(if ($results.Warnings.Count -gt 0) { "Yellow" } else { "Green" })
Write-Host "  Info: $($results.Info.Count)" -ForegroundColor Cyan
Write-Host "  Evaluated rules: $(@($results.Evaluated | ForEach-Object { $_.RuleId }) -join ', ')" -ForegroundColor Cyan
Write-Host "  Not evaluated: $($results.NotEvaluated.Count)" -ForegroundColor $(if ($results.NotEvaluated.Count -gt 0) { "Yellow" } else { "Green" })
Write-Host "  Disabled: $($results.Disabled.Count)" -ForegroundColor DarkGray

if ($results.Errors.Count -gt 0) {
	Write-Host "`nErrors:" -ForegroundColor Red
	foreach ($err in $results.Errors) {
		Write-Host "  [$($err.RuleId)] $($err.Description)" -ForegroundColor Red
	}
}

if ($results.Warnings.Count -gt 0) {
	Write-Host "`nWarnings:" -ForegroundColor Yellow
	foreach ($warning in $results.Warnings) {
		Write-Host "  [$($warning.RuleId)] $($warning.Page): $($warning.Description)" -ForegroundColor Yellow
	}
}

# Return JSON result
$jsonResult = $results | ConvertTo-Json -Depth 10
Write-Output $jsonResult

# Exit code
if ($results.Errors.Count -gt 0) {
	exit 1
}

exit 0
