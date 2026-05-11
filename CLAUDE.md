# Claude-Specific Agent Instructions — Analytics Use Case Library

> **Read [`AGENTS.md`](AGENTS.md) first.** It contains the complete, universal rules for all agents.
> This file contains **only Claude Code–specific additions** that override or extend AGENTS.md.

---

## Claude-Specific: PostToolUse Hooks (Automatic)

Two hooks fire after every Write/Edit — they are enforced and cannot be bypassed:

- **`validate_tmdl_style.sh`** — blocks on tab/`:=`/`description:` violations in `.tmdl` files
- **`validate_pbir_structure.sh`** — blocks on JSON syntax errors in `.json`/`.pbir` files inside PBIP directories

Hooks are defined in `.claude/settings.json`. If a hook blocks you, fix the violation and retry — **never bypass hooks**.

---

## Claude-Specific: TMDL Conventions Enforcement

The TMDL rules in `AGENTS.md` are automatically enforced by the PostToolUse hook above.
A violation causes an immediate block — fix and retry.

---

## Claude-Specific: Fab CLI Environment

When using `fab` commands in Claude Code terminal sessions, always run:

```bash
fab config set mode command_line
```

before issuing non-interactive commands. This prevents `fab` from opening interactive prompts that block the agent.
