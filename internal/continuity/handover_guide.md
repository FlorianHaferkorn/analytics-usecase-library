# Handover Guide: First Two Weeks

**Audience:** New engineers joining the team, interns, onboarding technical staff.  
**Scope:** Day-by-day curriculum, critical meetings, first real task, glossary.  
**Duration:** 2 weeks (10 working days).  
**Length:** ~1100 words.

---

## Overview

This guide structures the first 14 days to move you from "What is this?" to "I can add a feature." Each day includes:
- **Reading assignments** (repo docs, code comments)
- **Hands-on tasks** (clone, run checks, extend a feature)
- **Meetings** (with business, data, infra teams)

By **Friday of Week 2**, you will have:
- ✓ Cloned and regenerated the framework from source
- ✓ Understood the Golden Thread (strategy → KPI → action)
- ✓ Extended an action code end-to-end
- ✓ Run all 4 CI gates
- ✓ Deployed a change to a test workspace (if Fabric is available)

---

## Week 1: Foundations

### Day 1 (Monday): Welcome & System Setup

**Goal:** Get the repo cloned, dependencies installed, tests passing.

**Reading (60 min):**
- `README.md` (skip to "How to get started" section)
- `docs/reference/TAXONOMY.md` (skim; focus on domain prefixes and ID schemes)
- `.claude/settings.json` (understand pre-commit hooks and validation)

**Hands-on (90 min):**
1. Clone the repo:
   ```bash
   git clone <repo-url> && cd analytics-usecase-library
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   cd tooling/validation && npm ci && cd ../..
   ```

3. Run Stage 1 to verify everything works:
   ```powershell
   .\tooling\run_stage1_checks.ps1
   ```
   **Expected:** All checks pass (PASS: KPI Catalog, Action Codes, Use Case Brackets, Golden Thread consistency).

4. Run health scorecard:
   ```bash
   python3 tooling/health_scorecard.py
   ```
   **Expected:** H1–H5 scores ≥70%.

5. Check in with your manager: "System is installed and healthy. Ready for Day 2."

---

### Day 2 (Tuesday): Strategy & Golden Thread

**Goal:** Understand why this framework exists and how it connects business to action.

**Reading (120 min):**
- `core/strategy_operating_model/company/company_strategy.md` (10 min; executives' view)
- `core/strategy_operating_model/operating_model/golden_thread_strategy_to_action.md` (30 min; core concept)
- `core/strategy_operating_model/operating_model/operating_model_overview.md` (30 min; how analytics translates strategy)
- `core/kpi_catalog/README.md` (30 min; KPI governance principles)
- `internal/continuity/architecture_overview.md` (20 min; system design)

**Hands-on (60 min):**
1. Open `core/kpi_catalog/KPI_Catalog.md` and find the `KPI-COM-013` KPI definition. Read the entire entry:
   - Purpose
   - Definition & formula
   - Data lineage
   - Target/range
   - Connected use cases
   
   Ask yourself: "How does this KPI support strategy?"

2. Open `core/usecases/core/COM-001_Sales_Performance/Business_Factsheet.md` and read the "Decision Question" and "Value Drivers" sections.
   Ask yourself: "Which KPIs from the catalog does this use case need?"

3. Open the same use case's `UseCase_Bracket.yaml` and find `orchestration.influencing_kpi_ids`. Verify 3 KPIs from step 1 are in the list.

**Meeting (30 min):**
- Schedule: Meet with your direct manager + business lead (Sales/Commercial domain)
- Discuss: "What business decision does COM-001 enable?" and "When is this decision critical?"
- Note: This is your first exposure to "why" we built this. Listen carefully.

---

### Day 3 (Wednesday): KPI Catalog & Measure System

**Goal:** Learn the KPI catalog structure and how KPIs become measures.

**Reading (90 min):**
- `core/kpi_catalog/KPI_Catalog.md` (skim; read 5 domain entries fully: sales, margin, cost, inventory, cash)
- `core/templates/kpi_catalog_templates/KPI_Definition_Template.md` (20 min)
- `CLAUDE.md` — Framework section only (15 min; governance rules)

**Hands-on (90 min):**
1. **Add a new operational KPI to the Finance domain:**
   - Find: `core/kpi_catalog/KPI_Catalog.md`
   - Go to Finance section
   - Copy the template for an operational KPI (e.g., `finance.receivables.days.outstanding`)
   - Create a new KPI: `finance.payables.days.outstanding` with:
     - Purpose: Measure days sales outstanding for payables (working capital mgmt)
     - Definition: (Accounts Payable / Daily COGS)
     - Grain: [date, company, cost_center]
     - Lineage: [fact_payables.Payable_Amount, fact_cogs.Daily_Amount]
   - Validate: Run Stage 1 to ensure schema is valid
     ```powershell
     .\tooling\run_stage1_checks.ps1
     ```

2. **Create a corresponding data contract entry:**
   - Find: `core/data_contracts/domains/finance.yaml`
   - Add column to `fact_payables` table:
     ```yaml
     - name: Payable_Amount
       type: decimal(18,2)
       lineage: "ERP.PAYABLES_REGISTER.AMOUNT"
       required_for_kpis: [finance.payables.days.outstanding]
     ```

3. Run Stage 1 again to verify:
   ```powershell
   .\tooling\run_stage1_checks.ps1
   ```
   **Expected:** All checks pass.

**Debrief:** "I added a KPI and linked it to data. That's the SSOT principle."

---

### Day 4 (Thursday): Action Codes & Decision Logic

**Goal:** Learn how KPI deviations trigger actions.

**Reading (90 min):**
- `core/action_codes/README.md` (30 min; action code philosophy)
- `core/action_codes/Action_Code_Patterns.md` (30 min; trigger types, execution steps)
- 3 example action codes from different domains:
  - `core/action_codes/Commercial/C-M2.1.yaml` (pricing action)
  - `core/action_codes/Finance/F-C1.1.yaml` (cost action)
  - `core/action_codes/SupplyChain/S-S1.1.yaml` (supply action)

**Hands-on (90 min):**
1. **Review an action code:**
   - Open `core/action_codes/Commercial/C-M2.1.yaml`
   - Answer these questions:
     - What KPI triggers this action? (look for `kpi_id` in `trigger.condition`)
     - What is the execution step 1? (look for `operational_execution.steps[0].description`)
     - Who is responsible? (look for `operational_execution.owner_role`)

2. **Extend an existing action code with a new sub-action:**
   - Find: `core/action_codes/Operations/O-P1.2.yaml` (a process improvement action)
   - Add a sub-action (`.3`) with:
     - Trigger: deviation from KPI `ops.cycle_time.hours` > 120% of target
     - Execution: "Re-run batch process; if still high, escalate to ops manager"
     - Guardrail: "Do not override quality checks"
   
   Save as: `core/action_codes/Operations/O-P1.3.yaml`

3. Validate:
   ```powershell
   .\tooling\run_stage1_checks.ps1
   ```
   **Expected:** All checks pass.

**Debrief:** "Actions are reusable, governed, and can be extended without redefining the KPI."

---

### Day 5 (Friday): Use Cases & Brackets

**Goal:** Learn the use case structure and how it ties everything together.

**Reading (90 min):**
- `core/usecases/UseCase_Inventory.md` (20 min; all 16 use cases at a glance)
- `core/templates/usecase_bracket_template_v2.0.yaml` (30 min)
- 2 complete use cases (read both factsheet + bracket):
  - `core/usecases/core/COM-001_Sales_Performance/` (commercial)
  - `core/usecases/core/FIN-001_Cash_Liquidity_Performance/` (finance)

**Hands-on (90 min):**
1. **Extend an existing use case to reference your new action code:**
   - Find: `core/usecases/core/OPS-001_Operations_Performance/UseCase_Bracket.yaml`
   - In `orchestration.action_code_ids`, add the action code you created on Day 4:
     ```yaml
     orchestration:
       action_code_ids:
         - O-P1.1
         - O-P1.2
         - O-P1.3  # <-- YOUR NEW ACTION CODE
     ```

2. Verify KPI linkage:
   - Find the KPI you created on Day 3 (`finance.payables.days.outstanding`)
   - Search the repo for any use case that would benefit from this KPI
   - Add it to `FIN-001_Cash_Liquidity_Performance/UseCase_Bracket.yaml`:
     ```yaml
     orchestration:
       influencing_kpi_ids:
         - finance.cash_balance.amount
         - finance.payables.days.outstanding  # <-- YOUR NEW KPI
     ```

3. Run full validation:
   ```powershell
   .\tooling\run_stage1_checks.ps1
   python3 tooling/health_scorecard.py
   ```
   **Expected:** All checks pass; H1 Golden Thread coverage unchanged or improved.

**Debrief:** "I've connected a new KPI to data, an action code to logic, and wired them into a use case. This is the Golden Thread."

---

## Week 2: Hands-On Implementation & Deployment

### Day 6 (Monday): Code Generation & TMDL

**Goal:** Generate measures from KPIs and understand the TMDL compilation.

**Reading (60 min):**
- `core/strategy_operating_model/operating_model/reference/TMDL_Allowed_Subset.md` (30 min; rules)
- `CLAUDE.md` — TMDL Conventions & Power BI sections (30 min)

**Hands-on (120 min):**
1. **Regenerate measures (includes your new KPI):**
   ```powershell
   .\tooling\generation\generate_tmdl_measures.ps1
   ```
   **Expected:** Generates ~150 measures including `[Finance Payables Days Outstanding]` in `_Measures.tmdl`.

2. **Inspect the generated TMDL:**
   ```bash
   grep -A 5 "Payables Days Outstanding" products/fabric/powerbi/dist/Finance.SemanticModel/tables/_Measures.tmdl
   ```
   **Expected:** Measure definition with DAX formula and comments.

3. **Run TMDL validation (Fabric-specific):**
   ```powershell
   .\products\fabric\powerbi\tooling\run_fabric_checks.ps1
   ```
   **Expected:** All TMDL files compile with no syntax errors.

**Debrief:** "KPIs → IR JSON → TMDL measures. The generator is the bridge."

---

### Day 7 (Tuesday): Deployment to Fabric (Optional; Requires Fabric)

**Goal:** Deploy your changes to a development Fabric workspace.

**Prerequisites:**
- Fabric workspace access + semantic model admin role
- Fabric CLI (`fab`) installed and authenticated

**Reading (30 min):**
- `CLAUDE.md` — Fabric CLI section

**Hands-on (120 min):**
1. **Authenticate to Fabric:**
   ```bash
   fab auth login
   fab auth status
   ```

2. **List workspaces and identify dev workspace:**
   ```bash
   fab ls
   ```

3. **Export current model as backup:**
   ```bash
   fab export "YourDevWorkspace/Finance.SemanticModel" \
     -o ./backup/Finance.SemanticModel
   ```

4. **Import your regenerated measures:**
   ```bash
   fab import "YourDevWorkspace/Finance.SemanticModel" \
     -i ./products/fabric/powerbi/dist/Finance.SemanticModel \
     -f
   ```
   **Expected:** Import succeeds; model is updated with new measures.

5. **Trigger a refresh:**
   ```bash
   WS_ID=$(fab get "YourDevWorkspace.Workspace" -q "id" | tr -d '"')
   MODEL_ID=$(fab get "YourDevWorkspace/Finance.SemanticModel" -q "id" | tr -d '"')
   fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" \
     -X post -i '{"type":"Full"}'
   ```
   **Expected:** Refresh starts; monitor in Power BI web UI.

6. **Verify measure appears in Power BI:**
   - Go to Power BI web UI
   - Open Finance semantic model
   - Refresh and search for "Payables Days Outstanding"
   - Verify measure is available and has data

**Debrief:** "I deployed a framework change to production infrastructure. CI gates passed; tests passed; users can now see the new measure."

---

### Day 8 (Wednesday): CI/CD & Pre-Commit Checks

**Goal:** Understand validation gates and how to prepare PRs.

**Reading (60 min):**
- `README.md` — "Stage 1 CI Gate" section
- `CONTRIBUTING.md` — full document
- `.claude/settings.json` — understand hooks

**Hands-on (120 min):**
1. **Create a feature branch:**
   ```bash
   git checkout -b feat/extend-payables-kpi
   ```

2. **Commit your changes (Days 3–7):**
   ```bash
   git add core/kpi_catalog/KPI_Catalog.md
   git add core/data_contracts/domains/finance.yaml
   git add core/action_codes/Operations/O-P1.3.yaml
   git add core/usecases/core/OPS-001_Operations_Performance/UseCase_Bracket.yaml
   git add core/usecases/core/FIN-001_Cash_Liquidity_Performance/UseCase_Bracket.yaml
   git commit -m "feat: add payables DSO KPI and extend O-P1 action; wire into FIN-001 and OPS-001"
   ```

3. **Run full pre-commit checks locally:**
   ```powershell
   .\tooling\run_stage1_checks.ps1
   python3 tooling/health_scorecard.py
   cd tooling/validation && npm ci && npm run validate && cd ../..
   python3 -m pytest tooling/tests/ -q
   ```
   **Expected:** All 4 gates pass.

4. **Push and create a PR:**
   ```bash
   git push -u origin feat/extend-payables-kpi
   # Go to GitHub and create PR; reference this branch
   ```

5. **Monitor CI pipeline:**
   - GitHub Actions runs all 4 gates automatically
   - Expect success within 2–3 minutes

**Debrief:** "I followed the full development workflow: feature branch → local validation → commit → push → CI → PR ready for review."

---

### Day 9 (Thursday): Troubleshooting & Debugging

**Goal:** Know what to do when something fails.

**Reading (60 min):**
- `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` (30 min; common issues)
- `README.md` — Learning Loop section (5 min)
- Skim relevant error logs in your Terminal

**Hands-on (90 min):**
1. **Intentionally break something and fix it:**
   - Edit `core/kpi_catalog/KPI_Catalog.md`: reference a non-existent KPI in a bracket
   - Run Stage 1:
     ```powershell
     .\tooling\run_stage1_checks.ps1
     ```
     **Expected:** FAIL: "KPI not found"
   
   - Check `KNOWN_ERRORS_AND_FIXES.md` for this symptom
   - Fix the reference
   - Re-run Stage 1: **Expected:** PASS

2. **Break TMDL syntax:**
   - Edit a generated TMDL file: change one `=` to `:=`
   - Run Fabric checks:
     ```powershell
     .\products\fabric\powerbi\tooling\run_fabric_checks.ps1
     ```
     **Expected:** FAIL: "Invalid DAX syntax"
   
   - Revert the change
   - Re-run: **Expected:** PASS

3. **Consult the team:**
   - Schedule a 30-min debugging session with your mentor
   - Ask: "What's the first place you look when CI fails?"

**Debrief:** "I know the common failure modes and how to find fixes in the repo."

---

### Day 10 (Friday): Retrospective & Next Steps

**Goal:** Summarize learning; plan for continued growth.

**Meeting (60 min):**
- Meet with your manager + framework lead
- Review what you accomplished:
  - ✓ KPI created and linked to data
  - ✓ Action code extended
  - ✓ Use cases updated
  - ✓ Measures regenerated and deployed
  - ✓ Full CI/CD workflow executed
  - ✓ PR reviewed and merged (if Day 8 was successful)

**Reading (60 min):**
- Read your first real code review feedback (if PR was merged)
- Explore one domain you're interested in deeper (e.g., if you're in Finance, read all Finance use cases and action codes)

**Hands-on (60 min):**
1. **Pick your next task:**
   - Ask your manager for a small issue or feature request
   - Examples: "Add a new KPI to domain X," "Extend use case Y with a new action code," "Create a new use case"

2. **Plan the work:**
   - Review `docs/reference/TAXONOMY.md` for ID scheme
   - Sketch the Golden Thread: Strategy → KPI → Use Case → Action
   - Schedule 1-hour design review with your mentor

**Debrief:**
"I understand this framework. I've contributed end-to-end. I'm ready to own tasks independently."

---

## Glossary

| Term | Definition |
|------|-----------|
| **Golden Thread** | Traceability from Strategy → KPI → Use Case → Measure → Action. The core principle. |
| **SSOT** | Single Source of Truth (KPI Catalog, Action Codes). Not redefined in use cases. |
| **Bracket** | Use case YAML file (`UseCase_Bracket_v2.0.yaml`). Machine-readable config. |
| **Factsheet** | Use case prose document (`Business_Factsheet.md`). Human-readable context. |
| **KPI Catalog** | Centralized registry of all KPI definitions (`core/kpi_catalog/KPI_Catalog.md`). |
| **Action Code** | Reusable decision logic triggered by KPI deviations. Lives in `core/action_codes/`. |
| **IR** | Intermediate Representation. JSON bridge between YAML config and tool-specific output (TMDL, pages). |
| **TMDL** | Tabular Model Definition Language. YAML for Power BI semantic models. |
| **Data Contract** | Formal specification of table grain, column lineage, refresh cadence. Lives in `core/data_contracts/`. |
| **CI Gate** | Automated validation (Stage 1, health scorecard, schema, pytest). Must pass before merge. |
| **Measure** | DAX formula in semantic model that implements a KPI. Generated from KPI Catalog. |
| **Influencing KPI** | KPI that supports a strategic (H1) KPI. Listed in use case brackets. |
| **Domain** | Business area: Commercial (COM), Finance (FIN), Operations (OPS), Supply Chain (SCM), etc. |

---

## Resources & Contacts

| Topic | Contact | Meeting Cadence |
|-------|---------|-----------------|
| Framework design questions | Framework Lead | Weekly (Tue 10am) |
| KPI governance, definitions | Chief Data Officer + Domain leads | Bi-weekly (Thu 2pm) |
| Fabric deployment, infra | Fabric Admin + Cloud Engineering | As-needed |
| Use case feedback, business context | Sales/Finance/Ops domain leads | Weekly (respective domain meetings) |
| CI/CD, GitHub, pre-commit | DevOps / Engineering Lead | As-needed |

---

Welcome to the team. You've got this.
