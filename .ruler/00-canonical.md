# ALUCA — agent entry (cross-tool shim)

Canonical rules live in the repo's hand-authored sources — read them, do not duplicate:
- `AGENTS.md` — primary router (what-lives-where, Golden Thread, scripts/CI).
- `CLAUDE.md` — navigation, doctrine, drift-gate, project rules.
- `docs/agent/_INDEX.md` — agent rules + skills.

Hard rules: TMDL indents with tabs (never spaces), no `:=`; `description:` is
mandatory on tables, columns and measures (Copilot-readiness); reference governed KPIs
(never redefine); Stage-1 and `python3 scripts/gadw_gate.py` must be green before commit.
