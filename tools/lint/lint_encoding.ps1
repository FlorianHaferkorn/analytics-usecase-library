Param(
  [string]$Root = "analytics-usecase-library",
  [switch]$FailOnError
)

# Policy:
# - Docs (.md/.markdown): allow Unicode, but flag common mojibake markers
# - Code/Config (.ps1/.psm1/.json/.yml/.yaml/.toml): require ASCII only (no chars > 0x7F)

$docExt   = @('.md','.markdown')
$codeExt  = @('.ps1','.psm1','.json','.yml','.yaml','.toml')
$scanExt  = $docExt + $codeExt

# Build mojibake markers from code points to avoid literal problematic chars in the script
$ACIRC  = [char]0x00E2  # mojibake marker 0x00E2
$ATILDE = [char]0x00C3  # mojibake marker 0x00C3
$ACIRC2 = [char]0x00C2  # mojibake marker 0x00C2
$FFFD   = [char]0xFFFD  # Unicode replacement char

$mojibakeMarkers = @([string]$ACIRC,[string]$ATILDE,[string]$ACIRC2,[string]$FFFD)

$docHits = @(); $codeHits = @()
Get-ChildItem -Path $Root -Recurse -File |
  Where-Object { $scanExt -contains $_.Extension.ToLower() } |
  ForEach-Object {
    $p = $_.FullName
    $ext = $_.Extension.ToLower()
    $raw = Get-Content -Raw -Path $p -ErrorAction SilentlyContinue
    if(-not $raw){ return }

    if ($docExt -contains $ext) {
      foreach($m in $mojibakeMarkers){ if($raw.Contains($m)){ $docHits += [pscustomobject]@{ File=$p; Marker=$m } } }
    } elseif ($codeExt -contains $ext) {
      $hasNonAscii = $false
      $chars = $raw.ToCharArray()
      for($i=0; $i -lt $chars.Length; $i++){
        $cp = [int][char]$chars[$i]
        if ($i -eq 0 -and $cp -eq 0xFEFF) { continue } # allow BOM at start
        if ($cp -gt 127) { $hasNonAscii = $true; break }
      }
      if ($hasNonAscii) { $codeHits += [pscustomobject]@{ File=$p; Issue='Non-ASCII characters in code/config' } }
    }
  }

if ($docHits.Count -gt 0) {
  Write-Host "Docs mojibake markers detected:" -ForegroundColor Yellow
  $docHits | Sort-Object File, Marker | Select-Object File,Marker | Format-Table -AutoSize | Out-String | Write-Host
}
if ($codeHits.Count -gt 0) {
  Write-Host "Code/config contains non-ASCII characters:" -ForegroundColor Red
  $codeHits | Sort-Object File | Select-Object File,Issue | Format-Table -AutoSize | Out-String | Write-Host
}

if ($codeHits.Count -gt 0 -and $FailOnError) { exit 1 }
if (($docHits.Count -eq 0) -and ($codeHits.Count -eq 0)) {
  Write-Host "Encoding lint passed: no issues detected." -ForegroundColor Green
}


