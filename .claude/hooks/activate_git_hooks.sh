#!/bin/bash
# SessionStart: versionierte Git-Hooks aktivieren (idempotent; eine bewusst gesetzte
# andere Einstellung bleibt unangetastet). Bis zum 29.09.2026 war `core.hooksPath` in
# keinem Klon gesetzt, und `tooling/git-hooks/pre-commit` war nicht einmal ausfuehrbar:
# Index-Gate, Kundendaten-Pruefer und Ontologie-Build liefen beim Commit nie.
set -u
root="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
[ -d "$root/tooling/git-hooks" ] || exit 0
if [ -z "$(git -C "$root" config --get core.hooksPath || true)" ]; then
  git -C "$root" config core.hooksPath tooling/git-hooks \
    && echo "[session-start] core.hooksPath -> tooling/git-hooks (Tore aktiv)"
fi
exit 0
