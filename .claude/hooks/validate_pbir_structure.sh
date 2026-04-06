#!/usr/bin/env bash
# validate-pbip-json.sh
# PostToolUse hook: validate JSON/PBIR structure after Write/Edit in PBIP directories.
#
# Checks (all require jq):
#   1. JSON syntax (jq empty)
#   2. Folder name spaces — spaces in pages/<PageName>/ or visuals/<VisualName>/ break rendering
#   3. Required fields per schema:
#        visual.json  → $schema, name, position, and (visual or visualGroup)
#        page.json    → $schema, name, displayName
#        definition.pbir → $schema, version, datasetReference
#   4. definition.pbir byPath existence — checks that the referenced .SemanticModel dir exists
#   5. definition.pbir byConnection sanity — pbiModelDatabaseName must be a non-empty string
#
# Exit codes:
#   0 = pass, not applicable, or jq not available
#   2 = violation (blocks the agent)

set -euo pipefail

ERRORS=()

# ─── helpers ────────────────────────────────────────────────────────────────

add_error() { ERRORS+=("$1"); }

emit_errors() {
  echo "" >&2
  echo "╔══════════════════════════════════════════════════════════════════╗" >&2
  echo "║  PBIP VALIDATION FAILED — fix before continuing                 ║" >&2
  echo "╚══════════════════════════════════════════════════════════════════╝" >&2
  echo "" >&2
  echo "File: $FILE_PATH" >&2
  echo "" >&2
  for err in "${ERRORS[@]}"; do
    echo "  ✗ $err" >&2
  done
  echo "" >&2
  echo "Fix the issue(s) above, then retry." >&2
  echo "" >&2
  exit 2
}

# ─── prerequisites ───────────────────────────────────────────────────────────

if ! command -v jq &>/dev/null; then
  exit 0
fi

INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || true)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)
FILE_PATH="${FILE_PATH//\\//}"

case "$TOOL_NAME" in
  Write|Edit) ;;
  *) exit 0 ;;
esac

case "$FILE_PATH" in
  *.json|*.pbir) ;;
  *) exit 0 ;;
esac

case "$FILE_PATH" in
  *.Report/*|*.SemanticModel/*|*.Dataset/*) ;;
  *) exit 0 ;;
esac

if [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

# ─── Check 1: JSON syntax ────────────────────────────────────────────────────

if ! jq empty "$FILE_PATH" 2>/tmp/jq_error.txt; then
  add_error "JSON syntax error: $(cat /tmp/jq_error.txt)"
  emit_errors
fi

# ─── Check 2: Folder name spaces ─────────────────────────────────────────────
# Spaces in pages/<name>/ or visuals/<name>/ folder names break Power BI rendering silently.

DIR_PATH=$(dirname "$FILE_PATH")
# Extract the last two meaningful path segments (e.g. "pages/My Page Name")
if echo "$DIR_PATH" | grep -qE '/pages/[^/]* |/visuals/[^/]* '; then
  SEGMENT=$(echo "$DIR_PATH" | grep -oE '/(pages|visuals)/[^/]+' | tail -1)
  add_error "Folder name contains a space: '$SEGMENT' — Power BI will silently fail to render pages/visuals with spaces in folder names. Use underscores instead."
fi

# ─── Check 3: Required fields per schema ─────────────────────────────────────

BASENAME=$(basename "$FILE_PATH")

case "$BASENAME" in
  visual.json)
    # Required: $schema, name, position, and either visual or visualGroup
    MISSING=()
    if ! jq -e '.["$schema"]' "$FILE_PATH" >/dev/null 2>&1; then MISSING+=('$schema'); fi
    if ! jq -e '.name'       "$FILE_PATH" >/dev/null 2>&1; then MISSING+=('name'); fi
    if ! jq -e '.position'   "$FILE_PATH" >/dev/null 2>&1; then MISSING+=('position'); fi
    if ! jq -e '(.visual // .visualGroup)' "$FILE_PATH" >/dev/null 2>&1; then
      MISSING+=('visual or visualGroup')
    fi
    for field in "${MISSING[@]}"; do
      add_error "visual.json missing required field: $field"
    done
    # Name format: word chars, hyphens, underscores only (no spaces, commas, special chars)
    NAME=$(jq -r '.name // ""' "$FILE_PATH" 2>/dev/null || true)
    if [ -n "$NAME" ] && echo "$NAME" | grep -qE '[^a-zA-Z0-9_\-]'; then
      add_error "visual.json name '$NAME' contains invalid characters — use only letters, digits, underscores, hyphens."
    fi
    ;;
  page.json)
    MISSING=()
    if ! jq -e '.["$schema"]'   "$FILE_PATH" >/dev/null 2>&1; then MISSING+=('$schema'); fi
    if ! jq -e '.name'          "$FILE_PATH" >/dev/null 2>&1; then MISSING+=('name'); fi
    if ! jq -e '.displayName'   "$FILE_PATH" >/dev/null 2>&1; then MISSING+=('displayName'); fi
    for field in "${MISSING[@]}"; do
      add_error "page.json missing required field: $field"
    done
    # displayOption must be a string (not integer) in PBIR
    DISPLAY_OPT_TYPE=$(jq -r '.displayOption | type' "$FILE_PATH" 2>/dev/null || true)
    if [ "$DISPLAY_OPT_TYPE" = "number" ]; then
      add_error "page.json displayOption must be a string (e.g. \"FitToPage\"), not an integer. Integer values are the legacy report.json format."
    fi
    ;;
  definition.pbir)
    MISSING=()
    if ! jq -e '.["$schema"]'        "$FILE_PATH" >/dev/null 2>&1; then MISSING+=('$schema'); fi
    if ! jq -e '.version'            "$FILE_PATH" >/dev/null 2>&1; then MISSING+=('version'); fi
    if ! jq -e '.datasetReference'   "$FILE_PATH" >/dev/null 2>&1; then MISSING+=('datasetReference'); fi
    for field in "${MISSING[@]}"; do
      add_error "definition.pbir missing required field: $field"
    done

    # Check 4: byPath existence
    BY_PATH=$(jq -r '.datasetReference.byPath.path // ""' "$FILE_PATH" 2>/dev/null || true)
    if [ -n "$BY_PATH" ]; then
      REPORT_DIR=$(dirname "$FILE_PATH")
      TARGET=$(python3 -c "
import os, sys
report_dir = sys.argv[1]
rel = sys.argv[2]
print(os.path.normpath(os.path.join(report_dir, rel)))
" "$REPORT_DIR" "$BY_PATH" 2>/dev/null || true)
      if [ -n "$TARGET" ] && [ ! -d "$TARGET" ]; then
        add_error "definition.pbir byPath '${BY_PATH}' resolves to '${TARGET}' which does not exist. Update the path to point to the correct .SemanticModel directory."
      fi
    fi

    # Check 5: byConnection sanity — pbiModelDatabaseName must be a non-empty GUID-like string
    DB_NAME=$(jq -r '.datasetReference.byConnection.pbiModelDatabaseName // ""' "$FILE_PATH" 2>/dev/null || true)
    if jq -e '.datasetReference.byConnection' "$FILE_PATH" >/dev/null 2>&1; then
      if [ -z "$DB_NAME" ] || [ "$DB_NAME" = "null" ]; then
        add_error "definition.pbir byConnection.pbiModelDatabaseName is empty or null. Set it to the Fabric SemanticModel item GUID (dataset_id)."
      fi
    fi
    ;;
esac

# ─── Emit errors or pass ─────────────────────────────────────────────────────

if [ ${#ERRORS[@]} -gt 0 ]; then
  emit_errors
fi

exit 0
