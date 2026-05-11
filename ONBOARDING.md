# Onboarding — One Hour to Productive

This is the only doc you need on Day 1. Everything else is reference material.

Read it in order. Each section has a time budget — try to hold to it.

---

## 0–10 min: What this repo is and why it exists

This repo implements the **Analytics Strategy-to-Action Framework**.

Most analytics projects fail not because data is missing, but because there is no structure to connect strategy to the reports people actually use.
This framework provides that structure explicitly:

```
Strategy → KPIs → Use Cases → Semantic Models → Reports → Actions
```

Every artifact in the repo traces back to a strategic intent through this chain — called the **Golden Thread**.
Every KPI has one definition, one owner, and one place it is stored.
Reports reference governed definitions; they never redefine them.

**Architecture in three layers:**

| Layer | Folder | What lives there |
|---|---|---|
| Logic (tool-agnostic SSOT) | `core/` | KPI catalog, action codes, use cases, data contracts, templates |
| Interaction (UI) | `studio/` | Next.js editor for browsing and editing framework artifacts |
| Execution (per platform) | `products/` | Fabric/Power BI, Evidence.dev (OSS), adapter stubs |

Shared automation lives in `tooling/`. Reference examples live in `showcases/`. Maintainer-only material lives in `internal/`.

Continue to the next section when you can answer: *what is the Golden Thread?*

---

## 10–20 min: Folder roles and source vs. generated

**Source vs. generated — the most important boundary in the repo:**

| Type | Folders | Rule |
|---|---|---|
| Source (edit these) | `core/`, `products/fabric/powerbi/orchestrator/`, `tooling/`, `docs/` | Governed, versioned, tested |
| Generated (do not edit manually) | `products/fabric/powerbi/dist/`, `tooling/ontology/out/` | Re-created by scripts; edits are overwritten |
| Reference examples | `showcases/` | Read-only examples; not delivered to customers |
| Maintainer-only | `internal/` | Strategy notes, archives, CI specs; ignore on Day 1 |

**Quick folder scan — open the repo root and read each top-level folder name:**

- `core/` — the brain. KPIs, use cases, action codes, data contracts, templates. No platform logic here.
- `products/` — the hands. Platform implementations. `fabric/powerbi/` is the main one.
- `tooling/` — the guardrails. Validators, generators, ontology builder, pre-commit hooks.
- `studio/` — a Next.js app for visual editing over `core/`.
- `showcases/` — worked examples (Aurora Group). Useful for reference; not for production.
- `docs/` — entry points and architecture docs for all audiences.
- `internal/` — maintainer notes, archive, CI specs. Ignore until needed.

**One key naming convention:** Use case IDs follow the pattern `<DOMAIN>-<NNN>`: e.g. `COM-001`, `FIN-002`, `OPS-003`.
KPI IDs use dots: `sales.net_sales.amount`, `fin.cash.balance`. See [`TAXONOMY.md`](TAXONOMY.md) for the full scheme.

---

## 20–35 min: Walk one use case end-to-end

Open these four files in order. Read, don't skim.

**Step 1 — The business context (5 min)**

Open [`core/usecases/core/COM-001_Sales_Performance/Business_Factsheet.md`](core/usecases/core/COM-001_Sales_Performance/Business_Factsheet.md).

Notice:
- It is prose only. No YAML, no DAX, no schema.
- It describes the business decision, the KPIs that answer it, and the actions that follow from deviations.
- KPIs are listed by ID (e.g. `sales.net_sales.amount`). They are referenced here, never defined.

**Step 2 — The machine-readable counterpart (5 min)**

Open [`core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml`](core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml).

This is the same use case, but as structured config: orchestration settings, action code IDs, value driver model, UX layout rules.
When a generator or validator runs, it reads this file — not the Factsheet.

**Step 3 — Where KPIs are defined (3 min)**

Open [`core/kpi_catalog/golden_20.yaml`](core/kpi_catalog/golden_20.yaml) and search for `sales.net_sales.amount`.

That entry is the single source of truth for that KPI: definition, unit, owner, DAX expression stub.
The Factsheet references it. The Bracket references it. The measure dictionary implements it. Nothing else defines it.

**Step 4 — Where actions are defined (2 min)**

Open [`core/action_codes/Commercial/`](core/action_codes/Commercial/) and look at one action code YAML.

Each action code has a trigger (threshold, trend), impact category, the KPIs that fire it, and concrete execution steps.
Reports surface these dynamically when KPIs deviate — they do not embed action logic themselves.

**Golden Thread for COM-001, from top to bottom:**

```
Strategy pattern (Margin-First)
  └─ KPI: sales.net_sales.amount  [core/kpi_catalog/]
       └─ Use Case: COM-001        [core/usecases/core/COM-001_Sales_Performance/]
            └─ Measure: Net Sales  [products/fabric/powerbi/dist/Commercial.SemanticModel/]
                 └─ Report page    [products/fabric/powerbi/dist/COM-001_Sales_Performance.Report/]
                      └─ Action: C-M1.1  [core/action_codes/Commercial/]
```

---

## 35–50 min: Run Stage 1 and understand what it proves

**One-time setup (do this if you haven't yet):**

```bash
# Python 3.11+ required
pip install -r requirements.txt

# Node deps for JSON-schema validation
cd tooling/validation && npm ci && cd ../..
```

On Windows with PowerShell 7:
```powershell
.\tooling\bootstrap.ps1 -InstallNodeDeps -InstallPythonDeps
```

**Run the main validation gate:**

```bash
# Linux / macOS
pwsh ./tooling/run_stage1_checks.ps1

# Windows PowerShell
.\tooling\run_stage1_checks.ps1
```

Stage 1 validates the **entire tool-agnostic layer** (`core/`, `tooling/`, `docs/`):
- Schema compliance of all YAML artifacts
- KPI references in factsheets and brackets match the catalog
- Action code IDs referenced in brackets exist
- No duplicate IDs across domains
- Golden Thread coverage (H1 metric via health scorecard)

It should end with `Stage 1 checks passed.`

**If it fails**, consult [`internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md`](internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md) — it is a curated symptom → cause → fix table.

**When you change Fabric / Power BI output**, also run:
```powershell
.\products\fabric\powerbi\tooling\run_fabric_checks.ps1
```

---

## 50–60 min: First safe change and getting unstuck

**Three options for your first change — pick the one that fits your role:**

| Role | First task |
|---|---|
| Analyst / Domain lead | Add a row to `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` for an error you hit during setup |
| Power BI developer | Open one report under `products/fabric/powerbi/dist/` in Power BI Desktop. Confirm it loads. Note any issue. |
| Data engineer | Read one domain data contract in `core/data_contracts/domains/` and check if it matches your source |
| Everyone | Run `python tooling/health_scorecard.py` — review the H1–H5 scores |

**When you get stuck:**

1. Search [`internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md`](internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md) first.
2. Check [`CHANGELOG.md`](CHANGELOG.md) for recent breaking changes.
3. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) for workflow and conventions.
4. Ask a colleague and link the file path you are stuck on.

**After fixing a new error class**, add a row to `KNOWN_ERRORS_AND_FIXES.md`. That is the self-learning loop.

---

## Quick reference

| Question | Where to look |
|---|---|
| What is a KPI ID? What is an action code ID? | [`TAXONOMY.md`](TAXONOMY.md) |
| What does TMDL / PBIP / IR / MCP mean? | [`GLOSSARY.md`](GLOSSARY.md) |
| How do I name a file or script? | [`SYSTEM_NAMING.md`](SYSTEM_NAMING.md) |
| How do I add a new use case? | [`CONTRIBUTING.md`](CONTRIBUTING.md) → "Adding a new use case" |
| Which gate must pass before merge? | Stage 1: `.\tooling\run_stage1_checks.ps1` |
| What is deferred or not yet implemented? | [`KNOWN_GAPS.md`](KNOWN_GAPS.md) |
| How does the Fabric/Power BI pipeline work? | [`products/fabric/powerbi/README.md`](products/fabric/powerbi/README.md) |
| How does the Evidence/OSS stack work? | [`products/open_source_stack/README.md`](products/open_source_stack/README.md) |
| How do AI agents (Cursor, Claude, Copilot) work here? | [`AGENTS.md`](AGENTS.md) |
| What changed recently? | [`CHANGELOG.md`](CHANGELOG.md) |

---

## What to ignore on Day 1

These are real and useful — but you do not need them yet:

- `internal/` — maintainer strategy and audit notes.
- `showcases/aurora_group/` — large generated demo dataset used for reference.
- `.cursor/`, `.github/copilot-instructions.md` — generated agent configs; do not edit by hand.
- `products/fabric/powerbi/dist/` — generated TMDL and PBIR output; read but do not edit directly.
- `products/oss_adapters/` — adapter stubs for Grafana, Metabase, Superset; mostly placeholders.
- `studio/` — useful once you need to work on the UI editor.

Welcome aboard.
