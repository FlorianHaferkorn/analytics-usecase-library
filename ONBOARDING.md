# Onboarding — First Week Guide

Welcome. This is the only doc you need on Day 1. Everything else is reference.

> **Goal of your first day:** clone the repo, install dependencies, run the Stage 1 gate, and read one use case end-to-end.

---

## 1. What this repo actually is (90-second version)

This repo is the **Analytics Strategy-to-Action Framework**. It turns business strategy into governed analytics artifacts:

```
Strategy → KPIs → Use Cases → Semantic Models → Reports → Actions
```

Three layers, three product lines:

| Layer | Where | What lives there |
|---|---|---|
| **Logic (tool-agnostic SSOT)** | `core/` | KPI catalog, action codes, use cases, data contracts, templates |
| **Interaction (UI)** | `studio/` | Next.js app for editing/exporting framework artifacts |
| **Execution (per platform)** | `products/` | Fabric/Power BI, Evidence.dev (OSS), adapter stubs |

Tooling that supports all three lives in `tooling/` (Python + PowerShell validators, generators, ontology builder).

---

## 2. Environment setup (Linux / macOS)

| Tool | Required for | Install |
|---|---|---|
| Python 3.11+ | Validators, registry builder, health scorecard | `python3 --version` |
| Node 18+ | Schema validation, Studio app | `node --version` |
| PowerShell 7 (`pwsh`) | Stage 1 / Fabric checks | `brew install --cask powershell` (mac), `apt install powershell` (linux) |

```bash
git clone <repo-url>
cd analytics-usecase-library

# 1. Python deps (used by validators, registry, health scorecard)
pip install -r requirements.txt

# 2. Node deps for JSON-schema validation (one-time)
cd tooling/validation && npm ci && cd ../..

# 3. Studio app deps (only if you'll work on the UI)
cd studio && npm ci && cd ..
```

**Verify it works:**
```bash
python3 tooling/health_scorecard.py        # should print H1–H5 metrics
pwsh ./tooling/run_stage1_checks.ps1       # should end with "Stage 1 OK"
```

If `pwsh` isn't available, you can still run most Python checks individually — see [`tooling/README.md`](tooling/README.md).

---

## 3. Day-1 reading order (≈90 minutes)

Read these in order. Skip everything else for now.

1. **`docs/README.md`** — entry point and audience map (5 min)
2. **`core/strategy_operating_model/operating_model/golden_thread_strategy_to_action.md`** — the central principle of the framework (15 min)
3. **`core/usecases/core/COM-001_Sales_Performance/Business_Factsheet.md`** — one full use case (15 min)
4. **`core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml`** — its machine-readable counterpart (10 min)
5. **`TAXONOMY.md`** — IDs and naming you'll see everywhere (10 min)
6. **`GLOSSARY.md`** — acronyms (TMDL, PBIP, IR, …) (5 min)
7. **`CONTRIBUTING.md`** — workflow and validation gates (10 min)

---

## 4. First task suggestion

Pick one of these to feel productive on Day 2–3:

- **Easiest:** add or fix one row in `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` for an error you hit during setup.
- **Small change:** add a new KPI to `core/kpi_catalog/extended_playbook.md` and reference it in one Use Case Bracket. Run Stage 1.
- **Real feature:** pick an open item from `KNOWN_GAPS.md` or `internal/technical_backlog.md`.

Always run `pwsh ./tooling/run_stage1_checks.ps1` before pushing.

---

## 5. Where do I look when…?

| Question | File / Folder |
|---|---|
| What is a KPI ID? Action code ID? | `TAXONOMY.md` |
| What is TMDL / PBIP / IR? | `GLOSSARY.md` |
| How do I name a script or file? | `SYSTEM_NAMING.md` |
| How do I add a new use case? | `CONTRIBUTING.md` § "Adding a new use case" |
| Which validation gate must pass before merge? | `CONTRIBUTING.md` § "Validation gates" |
| What's deferred / not implemented? | `KNOWN_GAPS.md` |
| How does the Fabric pipeline work? | `products/fabric/powerbi/README.md` |
| How does the Evidence/OSS stack work? | `products/open_source_stack/` |
| How do I work on the Studio UI? | `studio/CLAUDE.md` |
| How do AI agents (Claude, Cursor, Copilot) interact with this repo? | `CLAUDE.md` (Claude), `AGENTS.md` (others) |
| What changed recently? | `CHANGELOG.md` |

---

## 6. The three CI gates (memorise these)

| Gate | Scope | Command |
|---|---|---|
| **Stage 1** (mandatory before merge) | Tool-agnostic — `core/`, `tooling/`, `docs/` | `pwsh ./tooling/run_stage1_checks.ps1` |
| **Fabric** | TMDL, DAX, PBIP, measures | `pwsh ./products/fabric/powerbi/tooling/run_fabric_checks.ps1` |
| **OSS** | Evidence, dbt, OSS adapters | `bash products/open_source_stack/tooling/run_oss_checks.sh` |

Stage 1 is the one that blocks merges. The others run only when you change product code.

---

## 7. Conventions cheat sheet

- **Branch names:** `<type>/<short-name>` — `feat/`, `fix/`, `docs/`, `refactor/`.
- **Commit style:** conventional (`feat:`, `fix:`, `docs:` …).
- **Run scripts from the repo root.** Always.
- **KPIs are referenced, never redefined.** Source of truth: `core/kpi_catalog/`.
- **Action logic is referenced, never redefined.** Source of truth: `core/action_codes/`.
- **Business Factsheets are prose-only.** All machine-readable config goes in `UseCase_Bracket.yaml`.

---

## 8. When you get stuck

1. Search `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` for the error symptom — it's a curated symptom→cause→fix table.
2. Check `CHANGELOG.md` for recent breaking changes.
3. Ask in your team's channel — link the file path you're stuck on (`file:line`).

After fixing a new class of error, add a row to `KNOWN_ERRORS_AND_FIXES.md`. That's the learning loop.

---

## 9. What to ignore on Day 1

You will *not* need these in your first week. Don't get lost in them:

- `internal/` — maintainer-only strategy and audit notes.
- `showcases/aurora_group/` — large generated demo dataset.
- `.cursor/`, `.github/copilot-instructions.md` — generated agent configs (don't edit by hand).
- `products/fabric/powerbi/dist/` — generated TMDL output.
- `products/oss_adapters/` — three adapter stubs, mostly placeholders.

Welcome aboard.
