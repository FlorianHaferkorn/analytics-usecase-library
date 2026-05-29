#!/usr/bin/env bash
# validate_measure_metadata.sh
# PostToolUse hook: enforce measure metadata standards on _Measures.tmdl files.
#
# Every committed measure must have:
#   1. formatString  — prevents blank/wrong number formatting in visuals
#   2. displayFolder — prevents all measures dumping into the root field well
#   3. /// Purpose:  — intent documentation per TMDL conventions
#
# Exit codes:
#   0 = pass or not applicable
#   2 = violation found (blocks the agent)

set -euo pipefail

INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || true)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('path','') or d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)

FILE_PATH="${FILE_PATH//\\//}"

case "$TOOL_NAME" in
  Write|Edit) ;;
  *) exit 0 ;;
esac

# Only fire on _Measures.tmdl files inside semantic model directories
case "$FILE_PATH" in
  *_Measures.tmdl) ;;
  *) exit 0 ;;
esac

if [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

ERRORS=()

# Parse measure blocks: find every `measure 'Name' = ...` and inspect the
# following lines until the next measure/table/partition/empty block.
python3 - "$FILE_PATH" <<'PYEOF'
import sys, re, pathlib

path = sys.argv[1]
lines = pathlib.Path(path).read_text(encoding="utf-8", errors="replace").splitlines()

MEASURE_RE  = re.compile(r"^\t\s*measure\s+")
FORMAT_RE   = re.compile(r"^\t\s+formatString\s*:")
FOLDER_RE   = re.compile(r"^\t\s+displayFolder\s*:")
PURPOSE_RE  = re.compile(r"^\t*///\s*Purpose:")
# Block ends when we hit something at the same indentation level
BLOCK_END_RE = re.compile(r"^\t(measure|column|partition|hierarchy|table|annotation)\b")

issues = []
i = 0
while i < len(lines):
    line = lines[i]
    if MEASURE_RE.match(line):
        # Extract measure name
        m = re.search(r"measure\s+'([^']+)'", line) or re.search(r"measure\s+(\S+)\s*=", line)
        name = m.group(1) if m else line.strip()
        start = i
        has_format  = False
        has_folder  = False
        has_purpose = False
        # Scan backwards for /// Purpose: (usually just above the measure line)
        for k in range(max(0, i - 4), i):
            if PURPOSE_RE.match(lines[k]):
                has_purpose = True
        # Scan forward through the block
        i += 1
        while i < len(lines):
            if BLOCK_END_RE.match(lines[i]) or (not lines[i].strip() and i > start + 10):
                break
            if FORMAT_RE.match(lines[i]):
                has_format = True
            if FOLDER_RE.match(lines[i]):
                has_folder = True
            i += 1
        missing = []
        if not has_format:
            missing.append("formatString")
        if not has_folder:
            missing.append("displayFolder")
        if not has_purpose:
            missing.append("/// Purpose: comment")
        if missing:
            issues.append(f"  Measure '{name}' (line {start+1}) is missing: {', '.join(missing)}")
        continue
    i += 1

if issues:
    print("MEASURE_ISSUES_FOUND", flush=True)
    for issue in issues:
        print(issue, flush=True)
PYEOF

# Capture python output and check for issues
PY_OUT=$(python3 - "$FILE_PATH" 2>/dev/null <<'PYEOF'
import sys, re, pathlib

path = sys.argv[1]
lines = pathlib.Path(path).read_text(encoding="utf-8", errors="replace").splitlines()

MEASURE_RE  = re.compile(r"^\t\s*measure\s+")
FORMAT_RE   = re.compile(r"^\t\s+formatString\s*:")
FOLDER_RE   = re.compile(r"^\t\s+displayFolder\s*:")
PURPOSE_RE  = re.compile(r"^\t*///\s*Purpose:")
BLOCK_END_RE = re.compile(r"^\t(measure|column|partition|hierarchy|table|annotation)\b")

issues = []
i = 0
while i < len(lines):
    line = lines[i]
    if MEASURE_RE.match(line):
        m = re.search(r"measure\s+'([^']+)'", line) or re.search(r"measure\s+(\S+)\s*=", line)
        name = m.group(1) if m else line.strip()
        start = i
        has_format  = False
        has_folder  = False
        has_purpose = False
        for k in range(max(0, i - 4), i):
            if PURPOSE_RE.match(lines[k]):
                has_purpose = True
        i += 1
        while i < len(lines):
            if BLOCK_END_RE.match(lines[i]) or (not lines[i].strip() and i > start + 10):
                break
            if FORMAT_RE.match(lines[i]):
                has_format = True
            if FOLDER_RE.match(lines[i]):
                has_folder = True
            i += 1
        missing = []
        if not has_format:
            missing.append("formatString")
        if not has_folder:
            missing.append("displayFolder")
        if not has_purpose:
            missing.append("/// Purpose: comment")
        if missing:
            issues.append(f"  Measure '{name}' (line {start+1}) is missing: {', '.join(missing)}")
        continue
    i += 1

if issues:
    print("MEASURE_ISSUES_FOUND")
    for issue in issues:
        print(issue)
PYEOF
)

if echo "$PY_OUT" | grep -q "^MEASURE_ISSUES_FOUND"; then
    echo "" >&2
    echo "╔══════════════════════════════════════════════════════════════════╗" >&2
    echo "║  MEASURE METADATA MISSING — add formatString + displayFolder    ║" >&2
    echo "╚══════════════════════════════════════════════════════════════════╝" >&2
    echo "" >&2
    echo "File: $FILE_PATH" >&2
    echo "" >&2
    echo "$PY_OUT" | grep -v "^MEASURE_ISSUES_FOUND" >&2
    echo "" >&2
    echo "Required on every measure:" >&2
    echo "  formatString: \"#,0.00\"   -- or \"0%\", \"@\" for text, etc." >&2
    echo "  displayFolder: \"1_Sales\"  -- prevents root-level measure clutter" >&2
    echo "  /// Purpose: ...          -- above the measure declaration" >&2
    echo "" >&2
    echo "Reference: core/strategy_operating_model/operating_model/reference/TMDL_Allowed_Subset.md" >&2
    echo "" >&2
    exit 2
fi

exit 0
