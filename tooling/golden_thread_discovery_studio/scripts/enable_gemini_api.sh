#!/usr/bin/env bash
# Enable Generative Language API (Gemini) in the current or given GCP project.
# Requires: gcloud CLI installed and logged in (gcloud auth login).
# Usage: ./enable_gemini_api.sh
#        ./enable_gemini_api.sh my-gcp-project-id

set -e
PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null)}"
if [ -z "$PROJECT_ID" ]; then
  echo "No project set. Run: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi
echo "Enabling Generative Language API (Gemini) in project: $PROJECT_ID"
gcloud services enable generativelanguage.googleapis.com --project="$PROJECT_ID"
echo "Done. Create an API key at: https://console.cloud.google.com/apis/credentials (Create credentials -> API key)"
echo "Then add to .env: GOOGLE_API_KEY=your-key"
