# Phase 5 report generation: page_scaffold_generator, theme application.
# Dot-sourced from orchestrate_full_model.ps1; runs in orchestrator scope (script:RepoRoot, ThemeName, etc.).

function Invoke-Phase5ReportGeneration {
    $state.phase = "report_generation"
    $state.iteration = 5
    $distReportRoot = Join-Path $script:RepoRoot "products\fabric\powerbi\dist"
    if (-not (Test-Path $distReportRoot)) { New-Item -ItemType Directory -Path $distReportRoot -Force | Out-Null }
    $reportUseCases = @($script:SelectedUseCaseIds)
    $pyCmd = $null
    foreach ($cmd in @("py -3", "python3", "python")) {
        try {
            $parts = $cmd -split " "; $exe = $parts[0]
            # $parts[1..0] counts down (1,0) for a single-word command and would pass the exe name as an argument.
            $exeArgs = @($parts | Select-Object -Skip 1) + @("--version")
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
    $pyExeArgs = @($pySplit | Select-Object -Skip 1)
    # Resolve theme: explicit -ThemeName wins; else Aurora default from showcases/aurora_group/theme_config.json (no hardcoded fallback)
    $effectiveTheme = $ThemeName
    if (-not $effectiveTheme) {
        $auroraThemeConfig = Join-Path $script:RepoRoot "showcases\aurora_group\theme_config.json"
        if (Test-Path $auroraThemeConfig) {
            try { $cfg = Get-Content $auroraThemeConfig -Raw -ErrorAction Stop | ConvertFrom-Json; if ($cfg.defaultThemeName) { $effectiveTheme = $cfg.defaultThemeName } } catch { Write-Verbose "Could not load theme config: $($_.Exception.Message)" }
        }
    }

    $scriptPath = Join-Path $script:RepoRoot "products\fabric\powerbi\tooling\page_scaffold_generator\generate_full_report.py"
    foreach ($ucId in $reportUseCases) {
        $domainName = Get-DomainNameFromUseCaseId -UcId $ucId
        $datasetRef = Get-DatasetReferenceRelativeFromReport -DomainName $domainName
        if (-not $datasetRef) { $datasetRef = "..\$($domainName).SemanticModel" }
        $reportFolderBaseName = Get-UseCaseReportFolderBaseName -UcId $ucId
        $reportFolder = Join-Path $distReportRoot "$reportFolderBaseName.Report"
        # I-3.3: the prototype renderer is deprecated; the orchestrator is its documented
        # rollback path, so it opts in explicitly. New work uses the official-first PBIR
        # emit (tooling/superversion/targets/pbir.py) gated by `powerbi-report-author validate`.
        $allArgs = $pyExeArgs + @($scriptPath, "--allow-deprecated-prototype", "--use-case", $ucId, "--output", $reportFolder, "--repo-root", $script:RepoRoot, "--dataset-reference", $datasetRef)
        $pyOutput = & $pyExe @allArgs 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "generate_full_report.py failed for $ucId (exit $LASTEXITCODE). Check Bracket ux_layout_rules and page_scaffold_generator."
        }
        if ($pyOutput -match "mode=delta") {
            Write-Host "  Report updated for $ucId (delta)" -ForegroundColor Green
        } else {
            Write-Host "  Report created for $ucId (overview + detail, UX Engine)" -ForegroundColor Green
        }
        # Base theme (BaseThemes/<name>.json, themeCollection.baseTheme, SharedResources item) comes from
        # the one established source: apply_report_theme --sync-base-theme, i.e. the vendored copy in
        # tooling/report_quality/base_theme.py (D-587). Runs with or without a custom theme.
        $applyThemeScript = Join-Path $script:RepoRoot "products\fabric\powerbi\tooling\apply_report_theme.ps1"
        if (-not (Test-Path $applyThemeScript)) {
            throw "apply_report_theme.ps1 not found at $applyThemeScript."
        }
        $reportFolderResolved = if ([System.IO.Path]::IsPathRooted($reportFolder)) { $reportFolder } else { Join-Path $script:RepoRoot $reportFolder }
        $reportFolderResolved = [System.IO.Path]::GetFullPath($reportFolderResolved)
        & $applyThemeScript -Report $reportFolderResolved -SyncBaseTheme -ErrorAction Stop | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "apply_report_theme.ps1 -SyncBaseTheme failed (exit $LASTEXITCODE) for $ucId. Report: $reportFolderResolved"
        }
        if ($effectiveTheme) {
            & $applyThemeScript -Report $reportFolderResolved -ThemeName $effectiveTheme -NoValidate -ErrorAction Stop | Out-Null
            if ($LASTEXITCODE -ne 0) {
                throw "apply_report_theme.ps1 failed (exit $LASTEXITCODE) for $ucId. Theme '$effectiveTheme' not applied. Check products/fabric/powerbi/themes/ (vendored) or themes_local/ and the report definition."
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
