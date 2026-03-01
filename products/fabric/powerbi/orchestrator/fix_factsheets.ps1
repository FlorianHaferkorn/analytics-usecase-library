# Fix FactSheet.md files - add required_kpi_ids to frontmatter
# Parses required_kpis YAML blocks and extracts IDs

$ucDirs = Get-ChildItem "core\usecases\core" -Directory | Where-Object { $_.Name -like "COM-*" }

foreach ($dir in $ucDirs) {
    $businessPath = Join-Path $dir.FullName "Business_Factsheet.md"
    $factsheetPath = Join-Path $dir.FullName "FactSheet.md"
    
    if (-not (Test-Path $businessPath)) { continue }
    
    # Parse required_kpis from Business_Factsheet.md
    $content = Get-Content $businessPath -Raw
    $yamlPattern = '(?ms)```yaml\s*required_kpis:(.*?)```'
    $match = [regex]::Match($content, $yamlPattern)
    
    if (-not $match.Success) {
        Write-Host "No required_kpis found in $($dir.Name)" -ForegroundColor Yellow
        continue
    }
    
    $yamlBlock = $match.Groups[1].Value
    $ids = @()
    foreach ($line in ($yamlBlock -split "`n")) {
        if ($line -match '-\s+id:\s+(\S+)') {
            $ids += $matches[1]
        }
    }
    
    if ($ids.Count -eq 0) {
        Write-Host "No IDs extracted from $($dir.Name)" -ForegroundColor Yellow
        continue
    }
    
    # Read current FactSheet.md
    $factsheetContent = Get-Content $factsheetPath -Raw
    
    # Extract frontmatter
    $frontmatterPattern = '(?ms)^---\s*(.*?)\s*---'
    $frontmatterMatch = [regex]::Match($factsheetContent, $frontmatterPattern)
    
    if (-not $frontmatterMatch.Success) {
        Write-Host "No frontmatter in $factsheetPath" -ForegroundColor Yellow
        continue
    }
    
    $existingFrontmatter = $frontmatterMatch.Groups[1].Value
    
    # Add required_kpi_ids
    $idsYaml = "required_kpi_ids:`r`n" + (($ids | ForEach-Object { "  - $_" }) -join "`r`n")
    $newFrontmatter = "$existingFrontmatter`r`n$idsYaml"
    
    # Replace frontmatter
    $newContent = $factsheetContent -replace '(?ms)^---\s*.*?\s*---', "---`r`n$newFrontmatter`r`n---"
    
    # Write back
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($factsheetPath, $newContent, $utf8)
    
    Write-Host "Updated $($dir.Name): Added $($ids.Count) KPI IDs" -ForegroundColor Green
}

Write-Host "`nDone! FactSheet.md files updated with required_kpi_ids" -ForegroundColor Cyan
