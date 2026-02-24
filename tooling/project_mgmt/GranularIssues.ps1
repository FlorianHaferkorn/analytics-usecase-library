# Load granular issues from granular_issues.json (single source of truth for sync and setup_project_full).
# Sets $script:GranularIssues as array of hashtables: title, milestone, area, priority, labels, body.

$jsonPath = Join-Path $PSScriptRoot "granular_issues.json"
if (-not (Test-Path $jsonPath -PathType Leaf)) {
    throw "granular_issues.json not found: $jsonPath"
}
$json = Get-Content -Raw -Path $jsonPath -Encoding UTF8 | ConvertFrom-Json
$script:GranularIssues = @()
foreach ($item in $json) {
    $labels = @()
    if ($item.labels) {
        if ($item.labels -is [array]) {
            $labels = @($item.labels)
        } else {
            $labels = @($item.labels)
        }
    }
    $script:GranularIssues += @{
        title     = $item.title
        milestone = $item.milestone
        area      = $item.area
        priority  = $item.priority
        labels    = $labels
        body      = $item.body
    }
}
