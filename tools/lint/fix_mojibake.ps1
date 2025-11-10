Param(
  [string]$Root = "."
)

# Fix common mojibake sequences in Markdown docs by replacing with proper UTF-8 characters.
$docExt = @('.md','.markdown')

function Get-MojibakeString([string]$s){
  $utf8 = [System.Text.Encoding]::UTF8
  $latin1 = [System.Text.Encoding]::GetEncoding(1252)
  return $latin1.GetString($utf8.GetBytes($s))
}

$targets = @(
  [char]0x2013, # – en dash
  [char]0x2014, # — em dash
  [char]0x2011, # ‑ non-breaking hyphen
  [char]0x201C, # “ left double quote
  [char]0x201D, # ” right double quote
  [char]0x2018, # ‘ left single quote
  [char]0x2019, # ’ right single quote
  [char]0x201E, # „ low double quote (German)
  [char]0x201A, # ‚ low single quote
  [char]0x2026, # … ellipsis
  [char]0x2192, # → right arrow
  [char]0x2194, # ↔ left-right arrow
  [char]0x2265, # ≥ greater-equal
  [char]0x2264, # ≤ less-equal
  [char]0x2212, # − minus sign
  [char]0x00B1, # ± plus-minus
  [char]0x00B0, # ° degree
  [char]0x00C4, # Ä
  [char]0x00D6, # Ö
  [char]0x00DC, # Ü
  [char]0x00E4, # ä
  [char]0x00F6, # ö
  [char]0x00FC, # ü
  [char]0x00DF, # ß
  [char]0x00D8, # Ø
  [char]0x00D7, # ×
  [char]0x2208, # ∈
  [char]0x0394, # Δ
  [char]0x20AC, # €
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

$files = Get-ChildItem -Path $Root -Recurse -File | Where-Object { $docExt -contains $_.Extension.ToLower() }
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
