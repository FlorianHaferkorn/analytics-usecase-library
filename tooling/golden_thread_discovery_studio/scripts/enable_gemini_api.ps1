# Enable Generative Language API (Gemini) in the current or given GCP project.
# Requires: gcloud CLI installed and logged in (gcloud auth login).
# Usage: .\enable_gemini_api.ps1
#        .\enable_gemini_api.ps1 -ProjectId "my-gcp-project-id"

param(
    [string]$ProjectId = ""
)

$ErrorActionPreference = "Stop"
if (-not $ProjectId) {
    $ProjectId = (gcloud config get-value project 2>$null)
    if (-not $ProjectId) {
        Write-Error "No project set. Run: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    }
}
Write-Host "Enabling Generative Language API (Gemini) in project: $ProjectId"
gcloud services enable generativelanguage.googleapis.com --project=$ProjectId
Write-Host "Done. Create an API key at: https://console.cloud.google.com/apis/credentials (Create credentials -> API key)"
Write-Host "Then add to .env: GOOGLE_API_KEY=your-key"
