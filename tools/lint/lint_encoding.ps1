Param(
  [string]$Root = "analytics-usecase-library",
  [switch]$FailOnError
)

$textExt = @('.md','.markdown','.yaml','.yml','.json','.ps1')
$badTokens = @(
  'Â±','Â','Ã„','Ã–','Ãœ','Ã¤','Ã¶','Ã¼','ÃŸ',
  'â€“','â€”','â€œ','â€','â€˜','â€™','â€¦','Ã—','�'
)

$hits = @()
Get-ChildItem -Path $Root -Recurse -File |
  Where-Object { $textExt -contains $_.Extension.ToLower() } |
  ForEach-Object {
    $p = $_.FullName
    $raw = Get-Content -Raw -Path $p -ErrorAction SilentlyContinue
    if(-not $raw){ return }
    foreach($t in $badTokens){ if($raw.Contains($t)){ $hits += [pscustomobject]@{ File=$p; Token=$t } } }
  }

if($hits.Count){
  Write-Host "Encoding artifacts detected:" -ForegroundColor Red
  $hits | Sort-Object File, Token | Select-Object File,Token | Format-Table -AutoSize | Out-String | Write-Host
  if($FailOnError){ exit 1 }
} else {
  Write-Host "No encoding artifacts found." -ForegroundColor Green
}

