# Onboarding

This is the entry point for every new colleague, no matter your background. Pick the track that fits you and follow it.

---

## Which track are you?

| Track | Who | Time | Requires |
|---|---|---|---|
| **Reader** | Business lead, domain expert, new analyst, anyone curious | 45–60 min | A browser or text editor, no installation |
| **Contributor** | Developer, data engineer, Power BI specialist | 60+ min | Python, Node, PowerShell 7 |

> **Not sure?** Start with the Reader track. You can switch to Contributor at any time.

---

## Reader Track — understand the framework in one hour

### What this repo is (and is not)

**In everyday language:**
This repo is a governed rulebook — templates, definitions, validators, and worked examples — that turns business goals into analytics artefacts (reports, models, action recommendations) in a structured, repeatable way.

It is **not** a finished product you install and run. It is **not** a database of company data. It is **not** a Power BI tutorial.

**The central idea — the Golden Thread:**

```
A company has a strategy goal
  → someone defines a KPI to measure it
    → a use case frames the business question
      → a data contract names the data fields needed
        → a semantic model calculates the measures
          → a report shows the result
            → when the KPI deviates, an action code recommends what to do
```

Every file in this repo traces back to the start of this chain. Nothing defines KPI meaning twice. Nothing embeds action logic inside a report.

> **After this section you should be able to answer:** What is the Golden Thread?

---

### What lives where (10 min)

Open the repo root and look at the top-level folder names. Here is what each one does:

| Folder | Role | Edit? |
|---|---|---|
| `core/` | All governed definitions: KPIs, use cases, action codes, data contracts, templates | Yes — source of truth |
| `products/` | Platform implementations (Power BI/Fabric is the main one) | Orchestrator scripts yes, `dist/` no |
| `tooling/` | Validators, generators, registry builder, pre-commit checks | Yes, with care |
| `docs/` | Navigation and architecture docs for all audiences | Yes |
| `showcases/` | Worked examples (Aurora Group demo company) | Read only |
| `studio/` | Next.js browser editor for `core/` artifacts | When you work on the UI |
| `internal/` | Maintainer notes, roadmaps, audit archives | Ignore on Day 1 |

**Source vs. generated — the most important distinction:**

- `core/`, `tooling/`, `docs/`, orchestrator scripts — **source**: governed, versioned, tested.
- `products/fabric/powerbi/dist/`, `tooling/ontology/out/` — **generated**: recreated by scripts; manual edits are overwritten.

For a visual folder map see [`docs/architecture/README.md`](docs/architecture/README.md).

> **After this section you should be able to answer:** Which folder should you never edit manually?

---

### How to read a use case (5 min)

Every use case has exactly two files:

| File | Purpose | Who reads it |
|---|---|---|
| `Business_Factsheet.md` | Prose description: business question, relevant KPIs, expected actions | Humans |
| `UseCase_Bracket.yaml` | Machine-readable config: strategic KPI, influencing KPIs, action code IDs, UX layout | Generators and validators |

The Factsheet and the Bracket describe the same use case. The Factsheet is the explanation; the Bracket is the instruction set for the tooling.

**Factsheet sections at a glance:**

| Section | What it contains | Where it lives in the Bracket |
|---|---|---|
| §0 Metadata | Owner, domain, reporting level | `governance.owner_role`, `governance.steward_role` |
| §1 Business Summary | Why this use case exists | Human context only |
| §2 Core Business Questions | The exact decisions the report must support | Human context only |
| §3 KPI & Action Code Overview | Which KPIs are tracked, which actions fire | `orchestration.strategic_kpi_id`, `orchestration.action_code_ids` |
| §5 Page Layout | Visual structure of the two report pages | `ux_layout_rules` |
| §6 Data Requirements | Which tables and fields are needed | `overrides.data_contract_ref` |

Before diving into a specific use case, scan the full inventory:
[`core/usecases/UseCase_Inventory.md`](core/usecases/UseCase_Inventory.md) — one row per use case, with domain, strategic KPI, and action codes.

---

### Walk COM-001 end-to-end (15 min)

COM-001 (Sales Performance) is the simplest complete example. Follow these four steps.

**Step 1 — The business context (5 min)**

Open [`core/usecases/core/COM-001_Sales_Performance/Business_Factsheet.md`](core/usecases/core/COM-001_Sales_Performance/Business_Factsheet.md).

Notice:
- It is prose only. No YAML, no formulas.
- It describes the business question ("Where do Net Sales deviate vs Plan?") and the KPIs that answer it.
- KPIs are listed by ID (`margin.gm.pct`, `sales.net_sales.amount`). They are *referenced* here, never *defined*.
- Domain shorthand you will see: `GM%` = Gross Margin Percentage, `LY` = Last Year, `PVM` = Price-Volume-Mix analysis, `L12M` = Last 12 Months. Full definitions in [`GLOSSARY.md`](docs/reference/GLOSSARY.md).

**Step 2 — The machine-readable counterpart (5 min)**

Open [`core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml`](core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml).

Look at the `orchestration` block. You will see:
- `strategic_kpi_id: margin.gm.pct` — the top-level outcome this use case protects.
- `influencing_kpi_ids` — KPIs (including `sales.net_sales.amount`) that drive the strategic KPI.
- `action_code_ids: [C-M2.1, C-S1.1, C-S1.2]` — the actions triggered when the KPI deviates.

When a generator or validator runs, it reads this file — not the Factsheet.

**Step 3 — Where KPIs are defined (3 min)**

Open [`core/kpi_catalog/golden_20.yaml`](core/kpi_catalog/golden_20.yaml) and search for `margin.gm.pct`.

That entry is the single source of truth for that KPI: definition, unit, owner, DAX expression stub.
The Factsheet references it. The Bracket lists it as `strategic_kpi_id`. The measure dictionary implements it. Nothing else defines it.

While you are in the file, also find `sales.net_sales.amount` — it is there too, as an influencing KPI. You can see the distinction between `strategic` and `influencing` roles.

**Step 4 — Where actions are defined (2 min)**

Open [`core/action_codes/Commercial/C-M2.1.yaml`](core/action_codes/Commercial/C-M2.1.yaml).

Read the `operational_execution.steps` block. That plain text is what "action-ready" means: when `margin.gm.pct` deviates, the system knows which concrete steps to recommend.

**The Golden Thread for COM-001, top to bottom:**

```
Strategy pattern (Margin-First)
  └─ Strategic KPI: margin.gm.pct           [core/kpi_catalog/golden_20.yaml]
       └─ Use Case: COM-001                  [core/usecases/core/COM-001_Sales_Performance/]
            └─ Data contract                 [core/data_contracts/domains/commercial_sales.yaml]
            └─ Measure: Gross Margin %       [products/fabric/powerbi/dist/Commercial.SemanticModel/]
                 └─ Report page              [products/fabric/powerbi/dist/COM-001_Sales_Performance.Report/]
                      └─ Actions: C-M2.1, C-S1.1, C-S1.2  [core/action_codes/Commercial/]
```

The strategic KPI (`margin.gm.pct`) is the top-level outcome COM-001 protects. `sales.net_sales.amount` is one of several influencing KPIs that drive it — you will see this split in the Bracket's `orchestration` section.

---

### Reader track: done checklist

You have completed the Reader track when you can answer these without looking:

- [ ] What is the Golden Thread? Name all six links in the chain.
- [ ] Which folder holds KPI definitions? Which folder holds action logic?
- [ ] What is the difference between `Business_Factsheet.md` and `UseCase_Bracket.yaml`?
- [ ] What is the `strategic_kpi_id` for COM-001?
- [ ] Which folders must you never edit manually?

**Safe first activity for Reader track:**

- Open [`core/usecases/UseCase_Inventory.md`](core/usecases/UseCase_Inventory.md) and find the use case that is closest to your domain.
- Read its Factsheet and note one term you do not recognise.
- Check [`docs/reference/GLOSSARY.md`](docs/reference/GLOSSARY.md). If the term is missing, that is your first contribution: propose adding it (ask a colleague to review before merging).

**When you get stuck (Reader track):**

1. Check [`docs/reference/GLOSSARY.md`](docs/reference/GLOSSARY.md) for unknown terms.
2. Check [`docs/architecture/README.md`](docs/architecture/README.md) for structural questions.
3. Ask a colleague and include the file path you are stuck on.

---

## Contributor Track — environment setup and first change

> Start here only after completing the Reader track, or if you already know the framework and need the toolchain.

### Environment setup

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

Full setup details and troubleshooting: [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

### Run Stage 1 and understand what it proves

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

**If it fails**, consult [`internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md`](internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md) — curated symptom → cause → fix table.

**When you change Fabric / Power BI output**, also run:
```powershell
.\products\fabric\powerbi\tooling\run_fabric_checks.ps1
```

---

### First safe change

Pick the option that fits your role:

| Role | First task |
|---|---|
| Analyst / Domain lead | Read a Factsheet in your domain; propose a clarification or missing term in GLOSSARY |
| Power BI developer | Open one report under `products/fabric/powerbi/dist/` in Power BI Desktop. Confirm it loads. |
| Data engineer | Read one domain data contract in `core/data_contracts/domains/` and check it matches your source |
| Maintainer / Platform | Run `python tooling/health_scorecard.py` — review the H1–H5 scores |

**After fixing a new error class**, add a row to [`internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md`](internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md). That is the self-learning loop.

---

### Contributor track: done checklist

- [ ] `pip install -r requirements.txt` and `npm ci` both succeed.
- [ ] `.\tooling\run_stage1_checks.ps1` ends with `Stage 1 checks passed.`
- [ ] `python tooling/health_scorecard.py` runs and shows H1–H5 scores.
- [ ] You have opened one report in Power BI Desktop and it loaded without errors, or run one generator script successfully.

**When you get stuck (Contributor track):**

1. Search [`internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md`](internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md) for the error symptom.
2. Check [`CHANGELOG.md`](CHANGELOG.md) for recent breaking changes.
3. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) for workflow and conventions.
4. Ask a colleague and include the file path and error output.

---

## Quick reference

| Question | Where to look |
|---|---|
| What is a KPI ID? What is an action code ID? | [`TAXONOMY.md`](docs/reference/TAXONOMY.md) |
| What does TMDL / PBIP / IR / MCP / SSOT mean? | [`GLOSSARY.md`](docs/reference/GLOSSARY.md) |
| How do I name a file or script? | [`SYSTEM_NAMING.md`](docs/reference/SYSTEM_NAMING.md) |
| How do I add a new use case? | [`CONTRIBUTING.md`](CONTRIBUTING.md) — "Adding a new use case" |
| Which gate must pass before merge? | Stage 1: `.\tooling\run_stage1_checks.ps1` |
| What is deferred or not yet implemented? | [`KNOWN_GAPS.md`](internal/project_mgmt/KNOWN_GAPS.md) |
| How does the Fabric/Power BI pipeline work? | [`products/fabric/powerbi/README.md`](products/fabric/powerbi/README.md) |
| How does the Evidence/OSS stack work? | [`products/open_source_stack/README.md`](products/open_source_stack/README.md) |
| How do AI agents (Cursor, Claude, Copilot) work here? | [`AGENTS.md`](AGENTS.md) |
| What changed recently? | [`CHANGELOG.md`](CHANGELOG.md) |
| Full folder map and architecture diagrams | [`docs/architecture/README.md`](docs/architecture/README.md) |

---

## What to ignore on Day 1

These are real and useful — but do not need them yet:

- `internal/` — maintainer strategy and audit notes.
- `showcases/aurora_group/` — large generated demo dataset used for reference.
- `.cursor/`, `.github/copilot-instructions.md` — generated agent configs; do not edit by hand.
- `products/fabric/powerbi/dist/` — generated TMDL and PBIR output; read but never edit directly.
- `products/oss_adapters/` — adapter stubs for Grafana, Metabase, Superset; mostly placeholders.
- `studio/` — useful once you need to work on the UI editor.

---

## Document ownership note

This file leads, it does not repeat. Detailed definitions belong in their canonical homes:

| What | Canonical location | ONBOARDING.md role |
|---|---|---|
| KPI meaning | `core/kpi_catalog/` | Reference by ID only |
| Action logic | `core/action_codes/` | Reference by ID only |
| Folder map | `docs/architecture/README.md` | Link, summarise |
| Term definitions | `docs/reference/GLOSSARY.md` | Short inline hints, then link |
| ID naming rules | `docs/reference/TAXONOMY.md` | Link only |
| Setup steps | `CONTRIBUTING.md` | Link only |

If you spot duplication between this file and a canonical source, the canonical source wins and this file should be shortened to a link.
