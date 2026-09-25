#!/usr/bin/env bash
# validate-tmdl.sh
# PostToolUse hook: validate TMDL files after Write/Edit operations.
#
# Enforces framework TMDL conventions:
#   1. Indentation must use TABS only (spaces cause parser errors)
#   2. No := operator (use = only)
#   3. No `description:` key — descriptions are a `///` block above the object
#
# Exit codes:
#   0 = pass or not applicable
#   2 = violation found (blocks the agent)

set -euo pipefail

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

# Only process .tmdl files
case "$FILE_PATH" in
  *.tmdl) ;;
  *) exit 0 ;;
esac

# Only process files inside semantic model directories
case "$FILE_PATH" in
  *.SemanticModel/*|*.Dataset/*|*/definition/*.tmdl|*/definition/tables/*|*/definition/relationships*) ;;
  *) exit 0 ;;
esac

# File must exist
if [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

ERRORS=()

# --- Check 1: No leading spaces (indentation must be tabs only) ---
# TMDL uses tab-indentation. A line starting with 2+ spaces is almost certainly wrong indentation.
if grep -Pn "^  " "$FILE_PATH" > /dev/null 2>&1; then
  FIRST_LINE=$(grep -Pn "^  " "$FILE_PATH" | head -1)
  ERRORS+=("TMDL indentation error: leading spaces found (use TABS only). First offending line: $FIRST_LINE")
fi

# --- Check 2: No := operator (DAX in TMDL must use = not :=) ---
if grep -n ":=" "$FILE_PATH" > /dev/null 2>&1; then
  FIRST_LINE=$(grep -n ":=" "$FILE_PATH" | head -1)
  ERRORS+=("TMDL DAX error: ':=' operator is forbidden in TMDL. Use '=' instead. Line: $FIRST_LINE")
fi

# --- Check 3: No `description:` key ---
# In TMDL the TOM Description property is written as a `///` block directly above the
# object declaration (learn.microsoft.com/analysis-services/tmdl/tmdl-overview#descriptions).
# That block IS what report authors and Copilot see (Copilot reads the first 200 chars).
# A `description:` key is not TMDL's description syntax; the generator and
# check_tmdl_syntax.ps1 reject it as well.
if grep -n "^[[:space:]]*description:" "$FILE_PATH" > /dev/null 2>&1; then
  FIRST_LINE=$(grep -n "^[[:space:]]*description:" "$FILE_PATH" | head -1)
  ERRORS+=("TMDL description error: write the description as a '///' block above the object, not as a 'description:' key. Line: $FIRST_LINE")
fi

# --- Report results ---
if [ ${#ERRORS[@]} -gt 0 ]; then
  echo "" >&2
  echo "╔══════════════════════════════════════════════════════════════════╗" >&2
  echo "║  TMDL VALIDATION FAILED — fix before continuing                 ║" >&2
  echo "╚══════════════════════════════════════════════════════════════════╝" >&2
  echo "" >&2
  echo "File: $FILE_PATH" >&2
  echo "" >&2
  for ERR in "${ERRORS[@]}"; do
    echo "  ✗ $ERR" >&2
  done
  echo "" >&2
  echo "Reference: core/strategy_operating_model/operating_model/reference/TMDL_Allowed_Subset.md" >&2
  echo "" >&2
  exit 2
fi

exit 0
