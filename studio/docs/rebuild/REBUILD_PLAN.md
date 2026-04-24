# Studio Rebuild — Phased Execution Plan

**Audience:** Sonnet 4.6 (executing agent) and Flo (reviewer).

**Working directory:** `studio/` (inside the repo).

**Prerequisite reading (in this order):**

1. `studio/docs/rebuild/REBUILD_DECISIONS.md` — locked product decisions.
2. `studio/docs/rebuild/TOKEN_SPEC.md` — CSS variable contract.
3. `studio/docs/rebuild/DATA_WIRING.md` — loader ↔ UI map.
4. `studio/docs/design-reference/README.md` — filename/content map for the mockup files.

**Golden rule:** when a decision doc conflicts with the mockup, the **decision doc wins for behavior**, the **mockup wins for look**.

---

## Phase 0 — Safety nets (before any code change)

**Goal:** make the rebuild reversible.

1. Create branch `rebuild/studio-v2` from current `main`.
2. Take a snapshot tag `pre-studio-rebuild-2026-04-24`.
3. Run existing test suite to capture baseline:
   - `.\tooling\run_stage1_checks.ps1` (Windows) or `python3 -m pytest tooling/tests/ products/ -q` (Linux).
   - Record pass/fail count in `studio/docs/rebuild/BASELINE.md`.
4. Ensure `.claude/settings.json` PostToolUse hooks still trigger (touch a dummy `.tmdl` file to verify).

**Acceptance:** branch exists, baseline captured, hooks fire. **Commit message:** `chore(studio): snapshot before rebuild`.

---

## Phase 1 — Shell & tokens

**Goal:** the app boots, routes work, dark default, Settings modal stores preferences. No Core data wired yet.

### 1.1 Tokens

- Create `studio/src/styles/tokens.css` with all tokens from `TOKEN_SPEC.md` §2–§9.
- Import from `studio/src/app/layout.tsx` (global, before Tailwind entry).
- Verify in browser: `data-theme="dark"` on `<html>` uses the dark tokens; toggling to `light` switches without reload.

**Acceptance:** visual diff against the uploaded `wizard.jsx`/`dashboard.jsx` mockup screenshots shows matching panel, ink, line, accent colors in both themes.

### 1.2 Fonts

- Load all four pairings (Inter+JetBrains, IBM Plex, Geist, Instrument Serif+Inter) via `next/font`.
- Map `data-fonts` → font-family variables per `TOKEN_SPEC.md` §6.

**Acceptance:** switching font pairing in Settings changes the display font without FOUT.

### 1.3 App Shell

- Replace `studio/src/app/(studio)/layout.tsx` with the new Shell:
  - `Sidebar` component (ported from mockup `wizard.jsx` → `Sidebar`)
  - `Topbar` component (ported from mockup `wizard.jsx` → `Topbar`)
  - `CommandPalette` (⌘K, ports the mockup's `CommandPalette`)
  - `Settings` modal (new — replaces old Tweaks panel in Studio)
  - `Wizard` modal (ported from mockup `primitives.jsx` → `Wizard`)
- Nav items (REBUILD_DECISIONS §D3):
  1. **Overview** (Dashboard view)
  2. **Canvas**
  3. **Library**
  4. **Detail** (active when an entity is open)
  5. **Report Templates** → separate tool, opens in a different route group
- Keyboard shortcuts: ⌘K palette, `N` = new element (wizard), `Esc` = close modal, `[` / `]` = collapse/expand sidebar.

**Acceptance:**
- All nav items reachable via keyboard.
- Sidebar collapse animation matches mockup (240ms cubic-bezier).
- Settings modal opens, changes persist to localStorage, reloads preserve theme.
- Command Palette fuzzy-searches nav items (data wiring for entity search → Phase 3).

### 1.4 Routing

- Reorganize route groups per REBUILD_DECISIONS §D8:
  - Keep `(auth)` untouched.
  - Merge `(forge)` and `(registry)` into `(studio)` — move orphan pages to `studio/archive/`.
  - Add `(templates)` for Report Templates tool.
- Every top-level view is a Server Component where possible.

**Acceptance:** `/studio/overview`, `/studio/canvas`, `/studio/library`, `/studio/detail/[type]/[id]`, `/templates` all render a placeholder with the Shell active.

**Commit:** `feat(studio): shell + tokens + routing`

---

## Phase 2 — Library view (entity registry)

**Goal:** every entity in the Core is browsable with a row-click → Detail view.

### 2.1 Tabs

- Port `tweaks.jsx` → `Library` with tabs: KPIs / Dimensions / Sources / Action Codes / Use Cases.
- Each tab is a Server Component that calls the corresponding loader (see `DATA_WIRING.md` §2.3).
- Use the existing **project-store** (`src/store/project-store.ts`) **only** for UI state (active tab, search query, sort order). Domain data comes from loaders.

### 2.2 Row actions

- Click row → `/studio/detail/[type]/[id]`.
- Right-click (or kebab) → actions: Open, Duplicate, Archive, Show lineage (opens Canvas view zoomed to node).

### 2.3 Search

- Local fuzzy search (Fuse.js or equivalent) over the loaded set.
- Wire Command Palette to search across all tabs (entities).

**Acceptance:**
- All five tabs populate from real loaders with real data from `core/`.
- Clicking a Use Case row opens its Detail view with the Overview tab active.
- Visual parity with mockup (card grid, row density follows `data-density`).

**Commit:** `feat(studio): Library tabs wired to loaders`

---

## Phase 3 — Detail view (the critical one)

**Goal:** Factsheet ↔ Bracket tabs with Cascading AI on save. This is **the** core editing surface.

### 3.1 Use Case Detail

Port `library.jsx` → `Detail` and extend with tabs per `REBUILD_DECISIONS.md` §D5 and `DATA_WIRING.md` §2.4.1:

- **Overview** (read-only): rolled-up summary from bracket + factsheet.
- **Factsheet** (MDX editor): prose editing with live preview. Use the existing MDX pipeline or `@mdxeditor/editor`.
- **Bracket** (Monaco YAML): schema-aware editing. Load schema from `tooling/generator/schemas/usecase_bracket.schema.json`.
- **Data Contracts** (read-only list).
- **History** (audit log read).

### 3.2 Compare view toggle

- Topbar button: splits the content area 50/50 with Factsheet on the left, Bracket on the right. Both editable simultaneously.
- Toggle state persists per-user.

### 3.3 Cascading AI

- On save of either editable tab:
  1. Call `POST /api/ai/factsheet-draft` with `{ mode: 'reconcile', prose, bracket, change_hint }`.
  2. Render a **Diff panel** showing the proposed patch on the *other* tab.
  3. User **Accept** → apply patch + save both. **Reject** → save only the edited tab.
- Do **not** auto-apply patches. See REBUILD_DECISIONS §D7.

### 3.4 Other entity detail views

KPI / Action Code / Data Source detail views follow the same pattern, minus the Factsheet↔Bracket reconciliation. See `DATA_WIRING.md` §2.4.2–§2.4.4.

**Acceptance:**
- Edit `core/usecases/core/COM-001_Sales_Performance/Business_Factsheet.md`, save, verify AI proposes a bracket patch referencing the correct YAML paths.
- Edit the bracket, save, verify AI proposes prose insertions/removals.
- Compare view works in both light and dark themes with no layout break.
- Save mutations write an audit event visible in the History tab.
- Validation gate (`.\tooling\run_stage1_checks.ps1`) still passes.

**Commit:** `feat(studio): Use Case Detail with tabs + cascading AI`

---

## Phase 4 — Canvas view (Golden Thread graph)

**Goal:** visualize the full lineage, pan/zoom, drill-in.

- Keep the existing `@xyflow/react` + `@dagrejs/dagre` setup.
- Port `data.jsx` visual treatment to React Flow node types (4 types: `KPI`, `Contract`, `Action`, `UseCase`).
- Wire to `buildLineageGraph()` from `lineage-builder.ts`.
- Node click → popover with summary + "Open Detail" button.
- Filters: domain, certification status, Golden-20 only.

**Acceptance:** graph renders with real loader data for a sample project (COM-001). Pan/zoom smooth. Filter toggles work.

**Commit:** `feat(studio): Canvas view wired to lineage builder`

---

## Phase 5 — Dashboard view

**Goal:** Core-health snapshot, the first screen on login.

- Port `detail.jsx` → `Dashboard` with the real data mapping from `DATA_WIRING.md` §2.1.
- Sparklines from `/api/audit` last-14-days.
- "Recent changes" feed from the same endpoint.
- "Needs attention" card: Use Cases with Factsheet ↔ Bracket drift (detected via `/api/validate/drift`).

**Acceptance:** loads in ≤ 1.5 s on warm cache. All data derived from loaders, no mocks.

**Commit:** `feat(studio): Dashboard wired to audit + loaders`

---

## Phase 6 — Wizard (AI-first new element flow)

**Goal:** a single entry point for creating new KPIs / Data Sources / Action Codes / Use Cases.

- Port `primitives.jsx` → `Wizard` with three steps (type + intent → AI draft → review + save).
- Backend already exists (`/api/ai/wizard`). Only UI work.
- For Use Case type: generate Factsheet + Bracket in one call, pre-fill both Detail tabs, open in edit mode.

**Acceptance:** wizard creates a valid KPI, valid Action Code, valid Data Source, valid Use Case — each round-tripping through the validation gate.

**Commit:** `feat(studio): Wizard wired to AI draft endpoints`

---

## Phase 7 — Report Templates tool

**Goal:** the second tool in the same shell, with the Tweaks panel alive.

- Create `studio/src/app/(templates)/` route group with its own layout.
- Port `app.jsx` (T4), `T2_overview.jsx`, `T3_overview.jsx`, and T1 (embedded in `Report_Templates.html`) to Next.js pages.
- Bring the Tweaks panel over from `design-canvas.jsx` — live-editable theme that exports PBI / Evidence themes via `/api/export/theme`.

**Acceptance:** all four templates render at 1280×720 with annotation toggles. Theme export produces a valid PBI theme JSON that passes `tooling/validate_theme.py` (or equivalent).

**Commit:** `feat(templates): T1-T4 gallery + theme exporter`

---

## Phase 8 — Cleanup

- Archive dead API routes that no view consumes (move to `studio/archive/api/`, don't delete).
- Regenerate TypeScript types: `npm run types`.
- Update `studio/README.md` with the new shell structure.
- Update `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` with anything learned during the rebuild.
- Run `.\tooling\run_all_checks.ps1` — all green.

**Commit:** `chore(studio): archive dead code + update docs`

---

## Phase order & dependencies

```
Phase 0 (snapshot) → Phase 1 (shell)
                      ↓
                     Phase 2 (Library) → Phase 3 (Detail — CRITICAL)
                                            ↓
                                           Phase 4 (Canvas), Phase 5 (Dashboard), Phase 6 (Wizard) — parallelizable
                                                           ↓
                                                          Phase 7 (Templates)
                                                           ↓
                                                          Phase 8 (Cleanup)
```

Phases 4, 5, and 6 can be tackled in any order after Phase 3. Phase 7 depends on Phase 1 (shell + tokens).

---

## Hard DON'Ts (enforced)

- **Do not** copy `FRAMEWORK` / `GRAPH` mock globals from `icons.jsx` into components.
- **Do not** redefine KPIs or Action Codes in the UI layer. Edits always go through API routes that write back to the `core/` YAML files.
- **Do not** bypass the PostToolUse hooks. If a hook blocks you, fix the root cause.
- **Do not** use hex or `hsl()` for theme colors. OKLCH only (see `TOKEN_SPEC.md`).
- **Do not** introduce new state managers. Zustand project-store stays; no Redux / Jotai / etc.
- **Do not** auto-apply cascading AI patches. Diff → user accepts or rejects.
- **Do not** mark a phase complete if validation gates fail.

---

## Acceptance gates between phases

Before moving to the next phase, the current phase must:

1. Compile with `tsc --noEmit` = 0 errors.
2. `npm run lint` = 0 errors.
3. Stage 1 checks pass (`.\tooling\run_stage1_checks.ps1`).
4. Manual smoke test: open the new view, do one realistic action, confirm behaviour.
5. Commit with a conventional-commits message.
6. Update `studio/docs/rebuild/PROGRESS.md` (create in Phase 0) with phase status.

---

## When to stop and ask

Stop and ask Flo before:

- Changing any file under `core/` (schemas, catalog YAML, action codes, etc.).
- Adding a new API route not listed in `DATA_WIRING.md`.
- Introducing a new npm dependency.
- Skipping any item in the hard DON'Ts above.
- Finding that a mockup interaction is impossible to reproduce with the current loaders.

**Flo's working language:** German. Explanations should be simple, with examples, and step-by-step.

---

## Reference implementation order (first 10 files to touch)

Sonnet 4.6's first ten commits, in order:

1. `studio/src/styles/tokens.css` — full token set.
2. `studio/src/app/layout.tsx` — mount tokens, data attributes.
3. `studio/src/components/shell/Sidebar.tsx` — ported shell.
4. `studio/src/components/shell/Topbar.tsx` — ported shell.
5. `studio/src/components/shell/CommandPalette.tsx` — ⌘K.
6. `studio/src/components/shell/Settings.tsx` — replaces old Tweaks for Studio.
7. `studio/src/app/(studio)/layout.tsx` — wires Sidebar + Topbar.
8. `studio/src/app/(studio)/overview/page.tsx` — placeholder.
9. `studio/src/app/(studio)/library/page.tsx` — tabs shell (data wiring in Phase 2).
10. `studio/src/app/(studio)/detail/[type]/[id]/page.tsx` — tabs shell (data wiring in Phase 3).

Each file ports from the mockup but uses TypeScript + React 19 + Tailwind v4 idioms. No raw inline styles except where tokens aren't yet available (should be rare).
