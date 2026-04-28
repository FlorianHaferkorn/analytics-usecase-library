# Studio Rebuild — Locked Product Decisions

**Status:** LOCKED 2026-04-24 by Flo. These decisions are **not up for debate** during execution. If a decision needs to change, stop and ask before proceeding.

**Purpose:** Give the executing agent (Sonnet 4.6) an unambiguous set of product choices so implementation never has to guess.

---

## D1 — Visual target = uploaded design reference

The `studio/docs/design-reference/` folder (JSX + HTML uploads from 2026-04-24) is the **visual and interaction source of truth**. The rebuild must reproduce:

- Shell: Sidebar + Topbar + content area.
- Navigation model: Dashboard / Canvas / Library / Detail / Wizard / Settings / Tweaks (scoped).
- Typography: Inter display + IBM Plex Mono or equivalent pairing logic (see `TOKEN_SPEC.md`).
- Color system: OKLCH tokens, dark default, light toggle.
- Density modes: airy / balanced / dense.
- Density, font and theme toggles live in **Settings** (Studio-wide), **not** in a floating Tweaks panel in Studio.

**Do not copy the JSX 1:1** into Next.js components. These uploads are Babel-in-browser prototypes. Port them to TypeScript + React 19 + Tailwind v4 idioms.

---

## D2 — Framework = the Core is the backend

The rebuild **reuses** the existing loaders in `src/lib/core/*-loader.ts` and the existing API routes under `src/app/api/*`. No new backend modules are introduced unless an explicit gap is identified in `DATA_WIRING.md`.

Non-negotiable wiring rules:

- **KPI definitions** are read from `core/kpi_catalog/` via `catalog-loader.ts`. Never redefine a KPI in the UI.
- **Action codes** are read from `core/action_codes/` via `action-loader.ts`.
- **Data contracts / sources** are read via `contract-loader.ts`.
- **Use cases** are read via `bracket-loader.ts` and `factsheet-loader.ts`.
- **Golden Thread lineage** is read from `lineage-builder.ts` and `golden20.ts`.

The UI **edits these files** (via existing mutation endpoints or new thin ones) — it does not maintain a parallel model.

---

## D3 — Two tools, one shell

The design uploads contain two distinct tools that share the shell language:

1. **Studio** — authoring UI for the Core (KPIs, Data Sources, Action Codes, Use Cases, Factsheets, Brackets).
2. **Report Templates** — T1–T4 page gallery used to generate Power BI themes and Evidence themes.

Report Templates is a **separate top-level tool** under the same shell, reached via the sidebar. The **Tweaks panel** lives **only** in Report Templates — it is the theme editor. It does **not** appear in Studio.

In Studio, the same affordance for user-wide preferences is a **Settings** modal (density, font pairing, theme mode, AI model, workspace).

---

## D4 — Dark theme is default

- `theme="dark"` is the initial class on `<html>`.
- Users can toggle to light via Settings (persisted per user).
- Both themes must pass WCAG AA for body text (4.5:1) and AA-large for headings (3:1). See `TOKEN_SPEC.md`.

---

## D5 — Factsheet + Bracket editing = Tabs on the same Detail View (with Compare toggle)

When a user opens a Use Case from the Library, the Detail View shows **tabs**, not split panels:

```
┌─ Use Case: COM-001 Sales Performance ────────────────────────┐
│  [Overview] [Factsheet]* [Bracket]* [Data Contracts] [History]│
│                                                                │
│  (active tab content)                                          │
│                                                                │
└────────────────────────────────────────────────────────────────┘
   *  editable tabs
   [Compare view] toggle in Topbar → splits Factsheet + Bracket side-by-side
```

**Why tabs and not permanent split:**

- Less cognitive load — one document at a time.
- Works on smaller viewports.
- Matches the mockup's visual rhythm.

**Why a Compare toggle:**

- Power users need to see prose and spec at the same time when refactoring.
- Toggle is explicit, not automatic.

**Cascading principle (see D7):** a change in any editable tab proposes a patch for the other tabs via the AI engine — user approves or rejects.

---

## D6 — "New Element" flow uses the Wizard

The sidebar "New Element" button opens the **Wizard** (3-step modal from `primitives.jsx` / `Wizard` export). The wizard handles:

1. **KPI** — pick domain, describe intent, AI drafts catalog YAML, user edits, save to `core/kpi_catalog/`.
2. **Data Source** — describe source, AI drafts contract YAML, save via `contract-loader`.
3. **Action Code** — pick triggering KPI, describe action, AI drafts playbook YAML, save to `core/action_codes/`.
4. **Use Case** — pick strategic KPI + influencing KPIs + action codes, AI drafts Factsheet **and** Bracket together, user edits either tab, save.

Wizard is AI-first: every field has an "AI draft" button. Users can also start from a blank template.

---

## D7 — Cascading AI is the editing protocol

All edits in Studio go through the **Cascading AI engine** (existing `/api/ai/factsheet-draft` + new orchestration wrapper):

- User edits Factsheet prose → engine proposes Bracket YAML patch ("Added KPI reference `ORDERS_CONVERSION_RATE` → add to `orchestration.influencing_kpi_ids`?").
- User edits Bracket YAML → engine proposes Factsheet prose patch ("Removed action code `RESTOCK_L2` → remove from KPI & Action Code Overview section?").
- User edits Data Contract → engine flags affected KPIs that reference the changed field.

Patches are **diffs the user accepts or rejects**. Never auto-apply silently.

---

## D8 — Existing feature triage (keep / drop / defer)

Features in the current `studio/` Next.js app that are **not** in the uploaded mockup:

| Feature | Decision | Rationale |
|---|---|---|
| 4 route groups `(auth)/(forge)/(registry)/(studio)` | Keep auth + studio, fold forge + registry into main Library/Detail views | Separation doesn't help customers build the Core |
| 55 API routes | Audit — keep only those the new shell uses | Most will survive; dead ones archived to `studio/archive/` |
| KPI lineage graph (xyflow) | Keep as the **Canvas view** | Matches `data.jsx` mockup |
| Wizard flow | Keep, replace UI with uploaded `primitives.jsx` Wizard | Existing backend stays |
| Monaco YAML editor | Keep for Bracket tab | Power users need real YAML editing |
| Schema-based form generation (ajv + json-schema-to-typescript) | Keep for Factsheet metadata + wizard forms | Already solves the problem |
| Separate Dashboards / Reports pages | **Drop** from Studio — moves to Report Templates tool | Clarifies tool boundaries |
| Inline theme editor in Studio | **Drop** — moved to Tweaks panel in Report Templates | See D3 |
| Per-page tweaks panel | **Drop** from Studio — Settings modal replaces it | See D3 |

---

## D9 — Accessibility + performance floors

- Keyboard-first: every action in Topbar and Sidebar reachable via shortcuts. Command Palette (⌘K / Ctrl+K) is mandatory.
- Focus ring visible in both themes.
- No interaction requires hover-only.
- First meaningful paint of Dashboard view ≤ 1.5 s on a warm cache with the full Core loaded.

---

## D10 — Non-goals for this rebuild

Out of scope until a later phase:

- Multi-user real-time collab on a single Factsheet.
- Version control beyond the existing git workflow.
- PBIP/Evidence generation from the Tweaks panel (stub the export button, implement later).
- Mobile layout (viewport ≥ 1280 px assumed).
- Internationalization (German copy only where user-facing strings already exist; English everywhere else).

---

## Change log

| Date | Change | Reason |
|---|---|---|
| 2026-04-24 | Initial lock | End of planning phase with Flo |
