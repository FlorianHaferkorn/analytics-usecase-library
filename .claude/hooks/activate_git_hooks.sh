#!/bin/bash
# SessionStart: den versionierten pre-commit-Hook `.githooks/pre-commit` aktivieren (idempotent;
# eine bewusst gesetzte andere Einstellung bleibt unangetastet). Bis zum 29.09.2026 war
# `core.hooksPath` in keinem Klon gesetzt; vom 29.09. bis 07.10.2026 zeigte er auf
# `tooling/git-hooks`. Seit 07.10.2026 sind beide Hooks in `.githooks/pre-commit` zusammengelegt
# und `tooling/git-hooks/pre-commit` ist entfernt -- ein noch auf `tooling/git-hooks` stehender
# Wert legte alle Tore still und wird deshalb umgestellt.
set -u
root="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
[ -f "$root/.githooks/pre-commit" ] || exit 0
current="$(git -C "$root" config --get core.hooksPath || true)"
if [ -z "$current" ] || [ "$current" = "tooling/git-hooks" ]; then
  git -C "$root" config core.hooksPath .githooks \
    && echo "[session-start] core.hooksPath ${current:-(leer)} -> .githooks (Tore aktiv)"
fi
exit 0
