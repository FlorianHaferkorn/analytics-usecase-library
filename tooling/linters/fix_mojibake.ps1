Param(
  [string]$Root = "."
)

# Fix common mojibake sequences by replacing with proper UTF-8 characters.
$docExt = @('.md','.markdown','.yaml','.yml','.txt')
$excludeDirs = @('.git','node_modules','internal\\archive','internal\\reviews','products\\fabric\\powerbi\\dist')

function Get-MojibakeString([string]$s){
  $utf8 = [System.Text.Encoding]::UTF8
  $latin1 = [System.Text.Encoding]::GetEncoding(1252)
  return $latin1.GetString($utf8.GetBytes($s))
}

$targets = @(
  [char]0x2013, # â€“ en dash
  [char]0x2014, # â€” em dash
  [char]0x2011, # â€‘ non-breaking hyphen
  [char]0x201C, # â€œ left double quote
  [char]0x201D, # â€ right double quote
  [char]0x2018, # â€˜ left single quote
  [char]0x2019, # â€™ right single quote
  [char]0x201E, # â€ž low double quote (German)
  [char]0x201A, # â€š low single quote
  [char]0x2026, # â€¦ ellipsis
  [char]0x2192, # â†’ right arrow
  [char]0x2194, # â†” left-right arrow
  [char]0x2265, # â‰¥ greater-equal
  [char]0x2264, # â‰¤ less-equal
  [char]0x2212, # âˆ’ minus sign
  [char]0x00B1, # Â± plus-minus
  [char]0x00B0, # Â° degree
  [char]0x00C4, # Ã„
  [char]0x00D6, # Ã–
  [char]0x00DC, # Ãœ
  [char]0x00E4, # Ã¤
  [char]0x00F6, # Ã¶
  [char]0x00FC, # Ã¼
  [char]0x00DF, # ÃŸ
  [char]0x00D8, # Ã˜
  [char]0x00D7, # Ã—
  [char]0x00C1, # Ã
  [char]0x00C9, # Ã‰
  [char]0x00CD, # Ã
  [char]0x00D3, # Ã“
  [char]0x00DA, # Ãš
  [char]0x00D1, # Ã‘
  [char]0x00E1, # Ã¡
  [char]0x00E9, # Ã©
  [char]0x00ED, # Ã­
  [char]0x00F3, # Ã³
  [char]0x00FA, # Ãº
  [char]0x00F1, # Ã±
  [char]0x2208, # âˆˆ
  [char]0x0394, # Î”
  [char]0x20AC, # â‚¬
  [char]0x21D2, # â‡’
  [char]0x21D4, # â‡”
  [char]0x00A0, # NBSP
  [char]0x202F  # NARROW NO-BREAK SPACE
)

$map = [ordered]@{}
foreach($t in $targets){
  $s = [string]$t
  $bad = Get-MojibakeString $s
  # Convert non-breaking hyphen to plain hyphen for consistency
  if ([int]$t -eq 0x2011) { $map[$bad] = '-' }
  elseif ([int]$t -eq 0x00A0) { $map[$bad] = ' ' }
  elseif ([int]$t -eq 0x202F) { $map[$bad] = ' ' }
  else { $map[$bad] = $s }
}

# Handle common double-encoded sequences.
$map[[string]::Concat([char]0x00C3,[char]0x00A2,[char]0x00E2,[char]0x20AC,[char]0x00B0,[char]0x00C2,[char]0x00A5)] = [string][char]0x2265
$map[[string]::Concat([char]0x00C3,[char]0x00A2,[char]0x00E2,[char]0x20AC,[char]0x00B0,[char]0x00C2,[char]0x00A4)] = [string][char]0x2264

$files = Get-ChildItem -Path $Root -Recurse -File | Where-Object {
  $ext = $_.Extension.ToLower()
  if ($docExt -notcontains $ext) { return $false }
  foreach ($dir in $excludeDirs) {
    if ($_.FullName -match [Regex]::Escape([IO.Path]::DirectorySeparatorChar + $dir + [IO.Path]::DirectorySeparatorChar)) { return $false }
    if ($_.FullName -match [Regex]::Escape($dir + [IO.Path]::DirectorySeparatorChar)) { return $false }
  }
  return $true
}
foreach($f in $files){
  $raw = Get-Content -Raw -Path $f.FullName -ErrorAction SilentlyContinue
  if (-not $raw) { continue }
  $orig = $raw
  foreach($k in $map.Keys){ $raw = $raw.Replace($k, $map[$k]) }
  if ($raw -ne $orig){
    Set-Content -Path $f.FullName -Value $raw -Encoding UTF8
    Write-Host ("Fixed mojibake in: {0}" -f $f.FullName) -ForegroundColor Cyan
  }
}
Write-Host "Mojibake fix pass complete." -ForegroundColor Green







