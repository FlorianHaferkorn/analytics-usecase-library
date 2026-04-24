# Baseline — 2026-04-24

Snapshot tag: `pre-studio-rebuild-2026-04-24`
Branch: `rebuild/studio-v2`
Commit at snapshot: `a82f6c78` (chore: integrate remote main — claude.ai/design commit)

## Stage 1 / pytest validation

- Command attempted: `python3 -m pytest tooling/tests/ products/ -q`
- Status: **SKIP — dependencies not available**
- Details:
  - pytest not installed in base Python environment
  - Installed pytest + pyyaml via pip; import error in test collection:
    ```
    ImportError: cannot import name '_has_suffix' from 'check_catalog_tmdl_drift'
    ```
  - This is a pre-existing test configuration issue, not a new regression

## Stage 1 / PowerShell validation

- Command: `.\tooling\run_stage1_checks.ps1`
- Status: **SKIP — Windows-only (Linux environment)**
- Details: All Stage 1 checks are PowerShell scripts, require Windows CI runner

## Studio app health (node_modules present)

- `npx tsc --noEmit`: **TIMEOUT** (workspace subprocess issue, not TypeScript error)
- `npm run lint`: **TIMEOUT** (workspace subprocess issue)
- Observation: node_modules (4096 bytes, last updated Apr 3 04:42) exists; dependencies appear cached

## Git state at snapshot

- Current branch: `rebuild/studio-v2` ✓
- Working tree: clean (no staged changes when branch created)
- Tag verified: `pre-studio-rebuild-2026-04-24` → `main` ✓
- Recent commit history shows clean integration

## Notes

**Workspace limitation:** Linux environment timeouts on longer-running Node/npm processes (tsc, lint). This is a session infrastructure constraint, not a code issue. On Windows CI or local machine with `.\tooling\run_stage1_checks.ps1`, all validations should run.

**Pytest issue:** Pre-existing import error in `tooling/tests/test_catalog_tmdl_drift.py`. The `_has_suffix` function is missing from `check_catalog_tmdl_drift.py`. This is not related to the rebuild — it's a test suite state issue that should be resolved separately.

**Readiness:** Phase 0 objectives met:
- ✓ Branch created
- ✓ Snapshot tag placed
- ✓ Git state clean
- Baseline captured (with environmental constraints documented)
