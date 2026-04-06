param([string]$Path)
$parseErrors = $null
$null = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$null, [ref]$parseErrors)
if ($parseErrors.Count -gt 0) {
    $parseErrors | ForEach-Object { $_.Message }
    exit 1
}
Write-Host "Parse OK"
exit 0
