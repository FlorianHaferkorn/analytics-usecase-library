# Agent Brief — Studio Rebuild (for Sonnet 4.6)

**You are Sonnet 4.6.** You've been handed a well-scoped rebuild job with all locked decisions and references already written. Your job is to **execute**, not to re-plan.

**Working directory:** `studio/` inside the `analytics-usecase-library` repo.

**User language:** German. When communicating with Flo, explain simply, use examples, break things into steps.

---

## Mission (one sentence)

Rebuild the Studio Next.js app so its visual system and interactions match the uploaded design reference, while every piece of data is sourced from the existing `src/lib/core/*-loader.ts` layer — no mocks, no new backends except explicitly listed gaps.

---

## What you must read before you write a single line of code

Read these files in order. Do not skim. They are short and they unblock you:

1. **`studio/docs/rebuild/REBUILD_DECISIONS.md`** — locked decisions (tabs vs split, theme default, Tweaks-vs-Settings, cascading AI, feature triage). **These are not up for debate.**
2. **`studio/docs/rebuild/TOKEN_SPEC.md`** — the exact CSS variables you must emit.
3. **`studio/docs/rebuild/DATA_WIRING.md`** — the UI ↔ loader mapping.
4. **`studio/docs/rebuild/REBUILD_PLAN.md`** — phase-by-phase plan, acceptance gates, DON'Ts.
5. **`studio/docs/design-reference/README.md`** — critical filename/content map (the JSX uploads have misleading filenames).
6. **`CLAUDE.md`** (repo root) — hard rules, scripts, Fabric/PBIR conventions.

If anything in these docs contradicts the mockup, **decision docs win for behavior, mockup wins for look**.

---

## What already exists (and you must reuse)

- **Loaders** at `studio/src/lib/core/*-loader.ts` (catalog, action, bracket, factsheet, contract, lineage, org-role, golden20, spine). These read the `core/` YAML/MD files. Call them; don't reimplement.
- **API routes** at `studio/src/app/api/*`. 54 routes. Most are fine; a few are dead. Audit-then-archive in Phase 8.
- **AI endpoints**: `/api/ai/wizard`, `/api/ai/factsheet-draft`, `/api/ai/chat`. These are your AI engine — no new ones needed for Phases 1–6.
- **project-store** (`src/store/project-store.ts`) Zustand store for **UI state only**. Domain data comes from loaders.
- **Schemas** at `tooling/generator/schemas/*.json`. Use these for YAML validation in Monaco editors.
- **Hooks** `.claude/settings.json` auto-validate TMDL and PBIR on write. Do not bypass.

---

## How to work

1. **One phase at a time.** Follow `REBUILD_PLAN.md` phase order.
2. **Task-track.** Create tasks with `TaskCreate` for each phase sub-step. Mark in_progress before you start, completed when acceptance passes.
3. **Use sub-agents liberally** (Flo's standing preference — "Nutze Sub Agents immer soweit sinnvoll und möglich"). Good candidates:
   - `Explore` — find files, check conventions in the existing repo.
   - `Plan` — design a non-trivial port (e.g. how to split `library.jsx` into TS components).
   - `general-purpose` — long-running multi-step work where you need to research and implement.
4. **Token-efficient.** Don't re-read files you already have. Don't explain the same plan twice.
5. **Commit per phase** with a conventional-commits message from `REBUILD_PLAN.md`.
6. **Run the gate** after every phase: `.\tooling\run_stage1_checks.ps1` (Windows) / `python3 -m pytest tooling/tests/ products/ -q` (Linux). Do not mark a phase complete if the gate fails.

---

## When to STOP and ask Flo

Stop and post a question (in German) if you're about to:

- Change anything under `core/` (schemas, YAML, MD).
- Add a new API route not in `DATA_WIRING.md` gaps table.
- Add a new npm dependency.
- Violate a hard DON'T from `REBUILD_PLAN.md`.
- Find that a mockup interaction can't be done with the current loaders.

Ask succinctly. Cite the doc section. Offer 2 concrete options. Wait for a decision.

---

## First action (literally your first tool call)

Start Phase 0. Concretely:

1. Verify the branch model: `git status` and `git log -1`. If you're not on `rebuild/studio-v2`, create it: `git checkout -b rebuild/studio-v2`.
2. Tag `pre-studio-rebuild-2026-04-24` on the tip of `main`.
3. Run the baseline: `.\tooling\run_stage1_checks.ps1`.
4. Write the results to `studio/docs/rebuild/BASELINE.md` with format:

   ```markdown
   # Baseline — 2026-04-24

   Snapshot tag: pre-studio-rebuild-2026-04-24
   Branch: rebuild/studio-v2

   ## Stage 1 checks
   - Status: PASS | FAIL (counts)
   - Failing tests (if any): ...

   ## Existing studio app
   - Build: PASS | FAIL
   - Lint: PASS | FAIL
   ```

5. Commit: `chore(studio): snapshot before rebuild`.
6. Mark Phase 0 task complete and move to Phase 1.1 (tokens).

---

## Feedback loop with Flo

- After each phase commit, post a short German status update to Flo:
  - What got done (1–2 sentences).
  - Screenshots or a brief verification (dark + light view of the shell).
  - Next phase + anything you want Flo to sanity-check.
- If blocked, say so explicitly and ask a single, specific question.

---

## Style preferences (Flo)

- German for explanations.
- Simple language, examples, step-by-step.
- Multiple options weighed against each other when there's a real choice.
- Token-efficient — no filler.
- Use sub-agents.

---

## Reminders

- Dark theme is default. Light theme works. Both pass contrast.
- Tweaks panel only in **Report Templates** tool. Studio has a **Settings** modal.
- Factsheet + Bracket are **tabs** with a **Compare** toggle, not a permanent split.
- "New Element" always goes through the **Wizard** with AI draft.
- Every save must trigger the **Cascading AI** reconciliation (prose ↔ YAML diffs for user approval).
- No mock data. Every byte in the UI traces back to a loader or an existing API route.

Ship it carefully. Reversible phases, passing gates, committed work. Good luck.
