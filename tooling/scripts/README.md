# Tooling Scripts

Helper scripts for generation and sync (not part of Stage 1).

## hub_sync.py

Syncs Core YAML (action codes, UseCase_Bracket, decision spines) to Starlight `.mdx` in `docs_hub/`.

**Prerequisite:** Python 3, PyYAML (`pip install pyyaml`).

**Usage (from repo root):**

```powershell
python tooling/scripts/hub_sync.py              # write to docs_hub/src/content/docs
python tooling/scripts/hub_sync.py --dry-run    # list paths only
python tooling/scripts/hub_sync.py --out docs/catalog   # custom output dir
```

Run after Core logic changes so the living Hub reflects current definitions. See [framework-architect.md](../../docs/agent/rules/framework-architect.md).
