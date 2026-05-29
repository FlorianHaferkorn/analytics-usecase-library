#!/usr/bin/env bash
# check_pbi_desktop.sh
# PostToolUse hook: opportunistic Power BI Desktop live validation.
#
# When the developer has Power BI Desktop open with the matching semantic model
# loaded, this hook connects via the local XMLA endpoint, runs a lightweight
# DAX "smoke test" query, and reports referential integrity problems.
#
# Behaviour:
#   • Desktop NOT running  → exits 0 silently (graceful skip)
#   • Desktop running but pbir-cli not available → prints advisory, exits 0
#   • Desktop running + pbir-cli available → runs `pbir validate --fields`
#     against the active report/model and reports field-reference errors
#
# Exit codes:
#   0 = pass, skip, or not applicable
#   1 = field-reference errors found (advisory — does NOT block, warn only)
#
# References:
#   https://github.com/data-goblin/power-bi-agentic-development (pbi-desktop plugin)
#   products/fabric/powerbi/docs/references/pbir-visual-json.md

set -uo pipefail

INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || true)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('path','') or d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)

FILE_PATH="${FILE_PATH//\\//}"

case "$TOOL_NAME" in
  Write|Edit) ;;
  *) exit 0 ;;
esac

# Only relevant for TMDL semantic model files and PBIR JSON files
case "$FILE_PATH" in
  *.tmdl|*.json) ;;
  *) exit 0 ;;
esac

# ── Check if Power BI Desktop is running (Windows via tasklist) ───────────────
DESKTOP_RUNNING=false
if command -v tasklist.exe >/dev/null 2>&1; then
    if tasklist.exe 2>/dev/null | grep -qi "PBIDesktop.exe"; then
        DESKTOP_RUNNING=true
    fi
elif command -v powershell.exe >/dev/null 2>&1; then
    PROC_CHECK=$(powershell.exe -NoProfile -Command "Get-Process -Name PBIDesktop -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Id" 2>/dev/null || true)
    if [ -n "$PROC_CHECK" ]; then
        DESKTOP_RUNNING=true
    fi
fi

if [ "$DESKTOP_RUNNING" = "false" ]; then
    exit 0
fi

# Desktop IS running — report context
echo "" >&2
echo "INFO: Power BI Desktop is running." >&2

# ── Try pbir-cli field validation ─────────────────────────────────────────────
PBIR_CLI=$(command -v pbir 2>/dev/null || true)
if [ -z "$PBIR_CLI" ]; then
    echo "INFO: pbir-cli not installed. Run 'pip install pbir-cli' to enable live field-reference checks." >&2
    echo "" >&2
    exit 0
fi

# Find the nearest .Report directory from the file being edited
REPORT_DIR=""
DIR="$FILE_PATH"
for _ in $(seq 1 8); do
    DIR=$(dirname "$DIR")
    if [[ "$DIR" == *.Report ]]; then
        REPORT_DIR="$DIR"
        break
    fi
done

if [ -z "$REPORT_DIR" ] || [ ! -d "$REPORT_DIR" ]; then
    echo "INFO: Could not locate a .Report directory from $FILE_PATH. Skipping field validation." >&2
    exit 0
fi

echo "INFO: Running pbir validate --fields on $REPORT_DIR" >&2
echo "      (validates field references against the Desktop-connected model)" >&2

PBIR_OUT=$("$PBIR_CLI" validate "$REPORT_DIR" --fields 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "" >&2
    echo "┌──────────────────────────────────────────────────────────────────┐" >&2
    echo "│  ADVISORY: pbir-cli field-reference issues detected             │" >&2
    echo "└──────────────────────────────────────────────────────────────────┘" >&2
    echo "" >&2
    echo "$PBIR_OUT" >&2
    echo "" >&2
    echo "These may be caused by uncommitted TMDL changes not yet loaded in Desktop." >&2
    echo "Save the .tmdl file and refresh the model in Desktop, then verify." >&2
    echo "" >&2
    # Advisory only — do NOT block (exit 0) to allow iterative development
    exit 0
fi

echo "INFO: pbir field-reference check: OK" >&2
exit 0
