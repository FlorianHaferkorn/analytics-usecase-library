#!/usr/bin/env bash
# validate-pbip-json.sh
# PostToolUse hook: validate JSON/PBIR syntax after Write/Edit operations in PBIP directories.
#
# Runs `jq empty` on any .json or .pbir file inside a PBIP project directory.
# Silently skips if jq is not installed.
#
# Exit codes:
#   0 = pass, not applicable, or jq not available
#   2 = invalid JSON (blocks the agent)

set -euo pipefail

# Check jq is available
if ! command -v jq &> /dev/null; then
  exit 0
fi

# Read stdin JSON payload
INPUT=$(cat)

# Extract tool name and file path
TOOL_NAME=$(echo "$INPUT" | grep -o '"tool_name":"[^"]*"' | head -1 | cut -d'"' -f4 2>/dev/null || true)
if [ -z "$TOOL_NAME" ]; then
  TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || true)
fi

FILE_PATH=$(echo "$INPUT" | grep -o '"file_path":"[^"]*"' | head -1 | cut -d'"' -f4 2>/dev/null || true)
if [ -z "$FILE_PATH" ]; then
  FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)
fi

# Normalize Windows backslashes to forward slashes
FILE_PATH="${FILE_PATH//\\//}"

# Only process Write and Edit operations
case "$TOOL_NAME" in
  Write|Edit) ;;
  *) exit 0 ;;
esac

# Only process .json and .pbir files
case "$FILE_PATH" in
  *.json|*.pbir) ;;
  *) exit 0 ;;
esac

# Only process files inside PBIP project directories
case "$FILE_PATH" in
  *.Report/*|*.SemanticModel/*|*.Dataset/*) ;;
  *) exit 0 ;;
esac

# File must exist
if [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

# Run jq empty — exits non-zero if JSON is invalid
if ! jq empty "$FILE_PATH" 2>/tmp/jq_error.txt; then
  JQ_ERR=$(cat /tmp/jq_error.txt)
  echo "" >&2
  echo "╔══════════════════════════════════════════════════════════════════╗" >&2
  echo "║  PBIP JSON VALIDATION FAILED — fix before continuing            ║" >&2
  echo "╚══════════════════════════════════════════════════════════════════╝" >&2
  echo "" >&2
  echo "File: $FILE_PATH" >&2
  echo "" >&2
  echo "  ✗ JSON syntax error: $JQ_ERR" >&2
  echo "" >&2
  echo "Fix the JSON syntax error above, then retry." >&2
  echo "" >&2
  exit 2
fi

exit 0
