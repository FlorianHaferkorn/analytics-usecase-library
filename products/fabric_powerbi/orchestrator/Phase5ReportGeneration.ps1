# Phase 5 report generation: page_scaffold_generator, theme application.
# Dot-sourced from orchestrate_full_model.ps1; runs in orchestrator scope (script:RepoRoot, ThemeName, etc.).

function Invoke-Phase5ReportGeneration {
    $state.phase = "report_generation"
    $state.iteration = 5
    $distReportRoot = Join-Path $script:RepoRoot "products\fabric_powerbi\dist"
    if (-not (Test-Path $distReportRoot)) { New-Item -ItemType Directory -Path $distReportRoot -Force | Out-Null }
    $reportUseCases = @($script:SelectedUseCaseIds)
    $pyCmd = $null
    foreach ($cmd in @("py -3", "python3", "python")) {
        try {
            $parts = $cmd -split " "; $exe = $parts[0]
            $exeArgs = @($parts[1..([Math]::Min(999, $parts.Count - 1))] | Where-Object { $null -ne $_ }) + @("--version")
            $ver = (& $exe $exeArgs 2>&1) -join " "
            if ($LASTEXITCODE -eq 0 -and $ver -match "Python 3") { $pyCmd = $cmd; break }
        } catch { continue }
    }
    if (-not $pyCmd) {
        Write-Host "  WARNING: Python 3 not found; falling back to report_generator.ps1 (empty visuals)" -ForegroundColor Yellow
        foreach ($ucId in $reportUseCases) {
            & (Join-Path $script:OrchestratorRoot "report_generator.ps1") -UseCase $ucId -OutputPath $distReportRoot -ErrorAction Stop | Out-Null
            Write-Host "  Report structure created for $ucId (fallback)" -ForegroundColor Green
        }
        return
    }
    $pyExe = ($pyCmd -split " ")[0]
    $pySplit = $pyCmd -split " "
    $pyExeArgs = @($pySplit[1..([Math]::Min(999, $pySplit.Count - 1))] | Where-Object { $null -ne $_ })
    # Resolve theme: explicit -ThemeName wins; else Aurora default from showcases/aurora_group/theme_config.json (no hardcoded fallback)
    $effectiveTheme = $ThemeName
    if (-not $effectiveTheme) {
        $auroraThemeConfig = Join-Path $script:RepoRoot "showcases\aurora_group\theme_config.json"
        if (Test-Path $auroraThemeConfig) {
            try { $cfg = Get-Content $auroraThemeConfig -Raw -ErrorAction Stop | ConvertFrom-Json; if ($cfg.defaultThemeName) { $effectiveTheme = $cfg.defaultThemeName } } catch { }
        }
    }

    $scriptPath = Join-Path $script:RepoRoot "products\fabric_powerbi\tooling\page_scaffold_generator\generate_full_report.py"
    foreach ($ucId in $reportUseCases) {
        $domainName = Get-DomainNameFromUseCaseId -UcId $ucId
        $datasetRef = Get-DatasetReferenceRelativeFromReport -DomainName $domainName
        if (-not $datasetRef) { $datasetRef = "..\Commercial.SemanticModel" }
        $reportFolderBaseName = Get-UseCaseReportFolderBaseName -UcId $ucId
        $reportFolder = Join-Path $distReportRoot "$reportFolderBaseName.Report"
        $allArgs = $pyExeArgs + @($scriptPath, "--use-case", $ucId, "--output", $reportFolder, "--repo-root", $script:RepoRoot, "--dataset-reference", $datasetRef)
        $pyOutput = & $pyExe @allArgs 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "generate_full_report.py failed for $ucId (exit $LASTEXITCODE). Check Bracket ux_layout_rules and page_scaffold_generator."
        }
        if ($pyOutput -match "mode=delta") {
            Write-Host "  Report updated for $ucId (delta)" -ForegroundColor Green
        } else {
            Write-Host "  Report created for $ucId (overview + detail, UX Engine)" -ForegroundColor Green
        }
        # Ensure report has StaticResources (BaseThemes) like sample so theme application and base theme work
        $sampleStatic = Join-Path $script:RepoRoot "showcases\sample_pbip_report\Procurement_Wireframe_Theme.Report\StaticResources"
        if (Test-Path $sampleStatic) {
            $destStatic = Join-Path $reportFolder "StaticResources"
            $baseThemesPath = Join-Path $destStatic "SharedResources\BaseThemes"
            if (-not (Test-Path $baseThemesPath)) {
                New-Item -ItemType Directory -Force -Path $destStatic | Out-Null
                Copy-Item -Path (Join-Path $sampleStatic "*") -Destination $destStatic -Recurse -Force
                Write-Host "  StaticResources (BaseThemes) copied from sample" -ForegroundColor Cyan
            }
        }
        if ($effectiveTheme) {
            $applyThemeScript = Join-Path $script:RepoRoot "products\fabric_powerbi\tooling\apply_report_theme.ps1"
            if (-not (Test-Path $applyThemeScript)) {
                throw "apply_report_theme.ps1 not found at $applyThemeScript. Cannot apply theme $effectiveTheme."
            }
            $reportFolderResolved = if ([System.IO.Path]::IsPathRooted($reportFolder)) { $reportFolder } else { Join-Path $script:RepoRoot $reportFolder }
            $reportFolderResolved = [System.IO.Path]::GetFullPath($reportFolderResolved)
            & $applyThemeScript -Report $reportFolderResolved -ThemeName $effectiveTheme -NoValidate -ErrorAction Stop | Out-Null
            if ($LASTEXITCODE -ne 0) {
                throw "apply_report_theme.ps1 failed (exit $LASTEXITCODE) for $ucId. Theme '$effectiveTheme' not applied. Check theme_generator/themes/ and report definition."
            }
            $reportJsonPath = Join-Path $reportFolderResolved "definition\report.json"
            if (Test-Path $reportJsonPath) {
                $reportDef = Get-Content $reportJsonPath -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json
                $customTheme = $reportDef.themeCollection.customTheme
                if (-not $customTheme -or $customTheme.type -ne "RegisteredResources") {
                    throw "Theme apply did not update report.json (missing themeCollection.customTheme or type RegisteredResources). Report: $reportFolderResolved"
                }
            }
            Write-Host "  Theme applied: $effectiveTheme" -ForegroundColor Green
        }
    }
}
