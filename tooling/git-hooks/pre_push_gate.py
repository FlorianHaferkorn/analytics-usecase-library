#!/usr/bin/env python3
"""Claude Code PreToolUse hook: gate git push on preflight checks.

Inspects the Bash tool input. If the command is a git push, runs the
preflight suite first. Exits non-zero to block the push on failure.
Non-push commands pass through immediately.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PREFLIGHT = REPO_ROOT / "tooling" / "preflight.py"


def is_git_push(tool_input: str) -> bool:
    """Return True if the tool input contains a git push command."""
    try:
        data = json.loads(tool_input)
        command = data.get("command", "")
    except (json.JSONDecodeError, AttributeError):
        command = tool_input
    return "git push" in command


def main():
    tool_input = sys.argv[1] if len(sys.argv) > 1 else ""
    if not is_git_push(tool_input):
        sys.exit(0)

    print("Preflight gate: running checks before push...")
    result = subprocess.run(
        [sys.executable, str(PREFLIGHT)],
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        print("\nPush blocked: preflight checks failed. Fix errors first.")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
