Param(
  [Parameter(Mandatory=$true)][string]$TmdlFile
)

Write-Host "=== TMDL Validation Test ===" -ForegroundColor Cyan
Write-Host "File: $TmdlFile" -ForegroundColor Gray
Write-Host ""

$errors = @()
$warnings = @()
$checks = 0

# Check 1: File exists
$checks++
if (-not (Test-Path $TmdlFile)) {
    $errors += "File not found"
    Write-Host "[FAIL] File exists" -ForegroundColor Red
} else {
    Write-Host "[PASS] File exists" -ForegroundColor Green
}

if ($errors.Count -gt 0) {
    Write-Host "`nCannot proceed - file missing" -ForegroundColor Red
    exit 1
}

# Check 2: UTF-8 without BOM
$checks++
$bytes = [System.IO.File]::ReadAllBytes($TmdlFile)
$hasBOM = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
if ($hasBOM) {
    $errors += "File has UTF-8 BOM (must be UTF-8 without BOM)"
    Write-Host "[FAIL] UTF-8 without BOM" -ForegroundColor Red
} else {
    Write-Host "[PASS] UTF-8 without BOM" -ForegroundColor Green
}

$content = Get-Content -Raw -Path $TmdlFile
$lines = Get-Content -Path $TmdlFile

# Check 3: Valid TMDL structure (table keyword)
$checks++
if ($content -match '(?m)^\s*table\s+' -or $content -match '^table\s+') {
    Write-Host "[PASS] Valid TMDL structure (table keyword found)" -ForegroundColor Green
} else {
    $errors += "Missing 'table' keyword"
    Write-Host "[FAIL] Valid TMDL structure" -ForegroundColor Red
}

# Check 4: Measures present
$checks++
$measureMatches = [regex]::Matches($content, '(?m)^\s*measure\s+''([^'']+)''')
if ($measureMatches.Count -gt 0) {
    Write-Host "[PASS] Measures found ($($measureMatches.Count))" -ForegroundColor Green
    $measureNames = $measureMatches | ForEach-Object { $_.Groups[1].Value }
} else {
    $warnings += "No measures defined"
    Write-Host "[WARN] No measures found" -ForegroundColor Yellow
    $measureNames = @()
}

# Check 5: Each measure has formatString
$checks++
$missingFormat = @()
foreach ($mName in $measureNames) {
    $pattern = '(?ms)measure\s+''' + [regex]::Escape($mName) + '''.*?formatString\s*:'
    if (-not ([regex]::IsMatch($content, $pattern))) {
        $missingFormat += $mName
    }
}
if ($missingFormat.Count -eq 0 -and $measureNames.Count -gt 0) {
    Write-Host "[PASS] All measures have formatString" -ForegroundColor Green
} elseif ($measureNames.Count -eq 0) {
    Write-Host "[SKIP] No measures to check" -ForegroundColor Gray
} else {
    $warnings += "Measures missing formatString: $($missingFormat -join ', ')"
    Write-Host "[WARN] $($missingFormat.Count) measures missing formatString" -ForegroundColor Yellow
}

# Check 6: Each measure has displayFolder
$checks++
$missingFolder = @()
foreach ($mName in $measureNames) {
    $pattern = '(?ms)measure\s+''' + [regex]::Escape($mName) + '''.*?displayFolder\s*:'
    if (-not ([regex]::IsMatch($content, $pattern))) {
        $missingFolder += $mName
    }
}
if ($missingFolder.Count -eq 0 -and $measureNames.Count -gt 0) {
    Write-Host "[PASS] All measures have displayFolder" -ForegroundColor Green
} elseif ($measureNames.Count -eq 0) {
    Write-Host "[SKIP] No measures to check" -ForegroundColor Gray
} else {
    $warnings += "Measures missing displayFolder: $($missingFolder -join ', ')"
    Write-Host "[WARN] $($missingFolder.Count) measures missing displayFolder" -ForegroundColor Yellow
}

# Check 7: Each measure has /// description
$checks++
$missingDesc = @()
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*measure\s+''([^'']+)''') {
        $mName = $matches[1]
        if ($i -eq 0 -or -not $lines[$i-1].TrimStart().StartsWith('///')) {
            $missingDesc += $mName
        }
    }
}
if ($missingDesc.Count -eq 0 -and $measureNames.Count -gt 0) {
    Write-Host "[PASS] All measures have /// description" -ForegroundColor Green
} elseif ($measureNames.Count -eq 0) {
    Write-Host "[SKIP] No measures to check" -ForegroundColor Gray
} else {
    $warnings += "Measures missing /// description: $($missingDesc -join ', ')"
    Write-Host "[WARN] $($missingDesc.Count) measures missing /// comment" -ForegroundColor Yellow
}

# Check 8: No CALCULATE assignment operator := 
$checks++
if ($content -match ':=') {
    $warnings += "DAX uses := operator (not supported, use = instead)"
    Write-Host "[WARN] DAX uses := operator (should be =)" -ForegroundColor Yellow
} else {
    Write-Host "[PASS] No := operator usage" -ForegroundColor Green
}

# Check 9: Indentation consistent (tabs vs spaces)
$checks++
$hasTab = $content -match '\t'
$hasSpaces = $content -match '^    ' # 4 spaces
if ($hasTab -and $hasSpaces) {
    $warnings += "Mixed tabs and spaces for indentation"
    Write-Host "[WARN] Mixed indentation (tabs + spaces)" -ForegroundColor Yellow
} elseif ($hasSpaces) {
    Write-Host "[PASS] Consistent indentation (spaces)" -ForegroundColor Green
} else {
    Write-Host "[INFO] Indentation style: tabs or none" -ForegroundColor Gray
}

# Summary
Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Total checks: $checks" -ForegroundColor Gray
Write-Host "Errors:       $($errors.Count)" -ForegroundColor $(if($errors.Count -eq 0){"Green"}else{"Red"})
Write-Host "Warnings:     $($warnings.Count)" -ForegroundColor $(if($warnings.Count -eq 0){"Green"}else{"Yellow"})

if ($errors.Count -gt 0) {
    Write-Host "`nErrors:" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
}

if ($warnings.Count -gt 0) {
    Write-Host "`nWarnings:" -ForegroundColor Yellow
    $warnings | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
}

if ($errors.Count -eq 0) {
    Write-Host "`nTMDL validation passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`nTMDL validation failed" -ForegroundColor Red
    exit 1
}
