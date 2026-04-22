# Runbook: Operations & Deployment

**Audience:** Deployment engineers, DevOps, infrastructure leads, on-call teams.  
**Scope:** Operational procedures for deploying, provisioning, rotating credentials, and validating the system.  
**Length:** ~1200 words.

---

## Prerequisites

Before starting any procedure, verify you have:

| Tool | Required for | Verify with |
|------|-------------|-------------|
| **Git** | Clone repo | `git --version` (≥2.30) |
| **Python 3.9+** | Tooling, generation, health checks | `python3 --version` |
| **PowerShell 7+** | Stage 1 checks, TMDL generation, orchestration (Windows/macOS) | `pwsh --version` |
| **Node.js 18+** | Schema validation, Studio (optional) | `node --version` |
| **Fabric CLI (fab)** | Fabric workspace operations (optional) | `fab auth status` |
| **Azure CLI (az)** | Azure infrastructure (optional) | `az --version` |

**Note:** All commands must run from the **repository root** (`analytics-usecase-library/`).

---

## Procedure (a): Fresh Clone → Run Full Framework Regeneration

Use this procedure when:
- Onboarding a new team member
- Setting up a new CI/CD pipeline
- Recovering from a corrupted environment
- Verifying the framework is buildable from source

### Steps

#### 1. Clone the Repository
```bash
git clone https://github.com/your-org/analytics-usecase-library.git
cd analytics-usecase-library
git checkout main
```

#### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

**Expected output:** `Successfully installed pyyaml jsonschema typer rich ...` (no errors)

#### 3. Install Node.js Validation Dependencies
```bash
cd tooling/validation && npm ci && cd ../..
```

**Expected output:** `added X packages in Y seconds` (no errors)

#### 4. Verify Critical Files Exist
```bash
# Unix/Linux/macOS
ls -la core/kpi_catalog/KPI_Catalog.md
ls -la core/action_codes/impactful_15.yaml
ls -la core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml
find core/usecases/core -name "UseCase_Bracket.yaml" | wc -l  # Should print ≥16
```

**Expected output:** All files exist; 16+ use case brackets found.

#### 5. Run Stage 1 Validation (Required Before Any Generation)
```powershell
# Windows/PowerShell
.\tooling\run_stage1_checks.ps1
```

```bash
# macOS (via Homebrew PowerShell)
pwsh -NoProfile -Command "& { . ./tooling/run_stage1_checks.ps1 }"
```

**Expected output:**
```
PASS: KPI Catalog schema validation
PASS: Action Code schema validation
PASS: Use Case Bracket validation
PASS: Golden Thread consistency
===== SUMMARY: 4/4 PASS =====
```

**If it fails:** Read error message carefully. Check `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` for symptom | cause | fix. Do not proceed until Stage 1 passes.

#### 6. Run Health Scorecard (Advisory)
```bash
python3 tooling/health_scorecard.py
```

**Expected output:**
```
H1 (Golden Thread):       85% ✓
H2 (Semantic Stability):  90% ✓
H3 (Data Contracts):      80% ✓
H4 (Action Completeness): 88% ✓
H5 (Factsheet Quality):   92% ✓
============================
Overall framework health: 87% ✓
```

**Note:** Health scores below 70% warrant investigation, but do not block generation.

#### 7. Regenerate TMDL Measures (Windows + PowerShell)
```powershell
# This generates all measures for all domains
# Output: products/fabric/powerbi/dist/<Domain>.SemanticModel/tables/_Measures.tmdl
.\tooling\generation\generate_tmdl_measures.ps1
```

**Expected output:**
```
Generating TMDL measures for 16 use cases...
  COM: 45 measures → _Measures.tmdl (✓)
  FIN: 32 measures → _Measures.tmdl (✓)
  OPS: 28 measures → _Measures.tmdl (✓)
  SCM: 24 measures → _Measures.tmdl (✓)
  XD:  18 measures → _Measures.tmdl (✓)
====================================
Generated 147 measures in 23 seconds.
```

#### 8. Validate Generated TMDL (Optional, Fabric-Only)
```powershell
# If Fabric is installed and you want to compile TMDL
.\products\fabric\powerbi\tooling\run_fabric_checks.ps1
```

**Expected output:** All TMDL files parse correctly, no syntax errors.

#### 9. Build Full Semantic Model (Fabric Only, Optional)
```powershell
# Advanced: Builds complete PBIP from generated TMDL and pages
# Requires Fabric installed; output goes to ./dist/
.\products\fabric\powerbi\orchestrator\orchestrate_full_model.ps1
```

**Expected output:**
```
Building semantic model from TMDL...
  • Loading KPI catalog...
  • Building measure tables...
  • Creating relationships...
  • Validating DAX...
  • Assembling PBIP...
Model build complete: ./products/fabric/powerbi/dist/Domain.SemanticModel
```

---

## Procedure (b): Provision Missing Fact Tables

Use this procedure when:
- A data source is added (new ERP, new warehouse, etc.)
- A domain contract is updated
- A new fact table grain is required

### Steps

#### 1. Update Domain Data Contract
Edit the relevant domain contract in `core/data_contracts/domains/`:

```bash
# Example: Add columns to sales domain
vi core/data_contracts/domains/sales.yaml
```

**Add columns to the fact table spec:**
```yaml
fact_tables:
  fact_sales:
    grain: [date, location, product, customer, sales_org]
    columns:
      - name: List_Price_Amount
        type: decimal(18,2)
        lineage: "ERP.SALES_ORDERS_ITEMS.LIST_PRICE"
        required_for_kpis: [sales.price.list.amount]
      # ... add new columns here
```

#### 2. Run Stage 1 to Validate Contract
```powershell
.\tooling\run_stage1_checks.ps1
```

**Expected output:** Contract schema validation passes.

#### 3. Provision Tables in Semantic Model
If using Fabric Direct Lake, use the Fabric table operations script:

```bash
# Export environment variables (Fabric specific)
export WS_NAME="MyWorkspace.Workspace"
export LAKEHOUSE_NAME="sales_lakehouse"

# Run table provisioning
python3 products/fabric/powerbi/tooling/scripts/create_direct_lake_model.py \
  --lakehouse "$LAKEHOUSE_NAME" \
  --workspace "$WS_NAME" \
  --domain sales \
  --fact-table fact_sales
```

**Expected output:** Table created in lakehouse; Direct Lake binding established.

#### 4. Verify Table Lineage
```bash
python3 tooling/ontology/registry_builder.py --repo-root . --strict
```

**Expected output:**
```
Fact table: fact_sales
  ├─ Columns: 24
  ├─ Grain: [date, location, product, customer, sales_org]
  ├─ KPIs covered: 8/8 ✓
  └─ Status: ACTIVE ✓
```

---

## Procedure (c): Deploy to Fabric Workspace

Use this procedure when:
- Deploying to a development, staging, or production workspace
- Refreshing the semantic model after a change

### Prerequisites

```bash
# Authenticate to Fabric
fab auth login                                # Opens browser, stores token
fab auth status                               # Verify authentication
fab config set mode command_line              # Required for non-interactive
fab ls                                        # List workspaces
```

### Steps

#### 1. Extract Workspace and Model IDs
```bash
WS_ID=$(fab get "YourWorkspace.Workspace" -q "id" | tr -d '"')
MODEL_ID=$(fab get "YourWorkspace/Domain.SemanticModel" -q "id" | tr -d '"')

echo "Workspace ID: $WS_ID"
echo "Model ID: $MODEL_ID"
```

#### 2. Export PBIP from Fabric (Optional, Backup)
```bash
fab export "YourWorkspace/Domain.SemanticModel" -o ./backup/Domain.SemanticModel
```

#### 3. Import/Update PBIP in Workspace
```bash
# Full update with measures + pages
fab import "YourWorkspace/Domain.SemanticModel" \
  -i ./products/fabric/powerbi/dist/Domain.SemanticModel \
  -f  # Force overwrite

# Expected output: Import complete; refresh triggered
```

#### 4. Trigger Full Refresh
```bash
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" \
  -X post \
  -i '{"type":"Full"}'

# Expected output: Refresh ID and status
```

#### 5. Monitor Refresh Status
```bash
# Check refresh history
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X get

# Wait for refresh to complete (usually 2–10 minutes)
# Check the Power BI web UI for live progress
```

#### 6. Publish Reports
```bash
# After refresh completes, publish all reports in workspace
fab ls "YourWorkspace.Workspace" | grep Report

# Reports are auto-published; point users to the workspace
```

---

## Procedure (d): Rotate All Credentials

Use this procedure when:
- A team member leaves
- A credential is suspected compromised
- Annual security audit rotation
- Preparing to hand off to customer (escrow activation)

### Steps

#### 1. Fabric Workspace Credentials
```bash
# Revoke old service principal
az ad sp credential delete \
  --id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
  --cert-id "cert-to-revoke"

# Create new service principal
az ad sp create-for-rbac \
  --name "analytics-sa-prod" \
  --role Contributor \
  --scope "/subscriptions/SUBSCRIPTION_ID"

# Store in secure config (e.g. Azure Key Vault)
az keyvault secret set \
  --vault-name "my-keyvault" \
  --name "fabric-sp-client-id" \
  --value "newly-generated-client-id"
```

#### 2. Fabric CLI Authentication
```bash
# Clear old token
fab auth logout

# Login with new service principal (or user)
fab auth login
fab auth status  # Verify new identity
```

#### 3. Azure Storage / Data Lake Credentials
```bash
# Rotate storage account keys
az storage account keys renew \
  --account-name "yourstorageaccount" \
  --resource-group "your-rg" \
  --key primary

# Update connection strings in any config files / notebooks
# (Do NOT commit plaintext credentials; use Key Vault)
```

#### 4. OSS Tool Credentials (Metabase, Grafana, etc.)
```bash
# If deployed, log in and reset passwords
# Example Metabase:
curl -X POST http://metabase-host:3000/api/admin/users/1/password \
  -H "X-Metabase-Session: session-token" \
  -d '{"password": "new-secure-password"}'

# Example Grafana:
# Use web UI: Admin → Users → Edit → Update password
```

#### 5. Git Repository Credentials (if using HTTPS)
```bash
# Update Git credential manager
git credential-osxkeychain erase
# Or on Windows:
# Credential Manager → Windows Credentials → Edit GitHub entry

# Re-authenticate
git clone https://github.com/your-org/analytics-usecase-library.git
# Will prompt for new PAT or password
```

#### 6. Audit & Document
```bash
# List all active credentials
az ad sp credential list --id "analytics-sa-prod"

# Document rotation in:
internal/project_mgmt/credentials_rotation_log.md
# Entry: Date | System | Old ID | New ID | Rotated by | Notes
```

---

## Procedure (e): Run All 4 CI Gates Locally

Use this procedure when:
- Before committing changes
- Validating a PR branch
- Preparing for release
- Troubleshooting CI failures

### Gate 1: Stage 1 (Tool-Agnostic Validation)

```powershell
.\tooling\run_stage1_checks.ps1
```

**What it checks:**
- YAML syntax validity (KPI catalog, action codes, brackets)
- KPI reference integrity (all referenced KPIs exist)
- Use case ID uniqueness
- Data contract grain consistency
- Golden Thread linkage (strategic KPI → use case → action)

**Expected output:** All 4–6 checks pass. Exit code 0.

### Gate 2: Health Scorecard (Advisory Metrics)

```bash
python3 tooling/health_scorecard.py --json > health_report.json
```

**What it measures:**
- H1: Golden Thread coverage (% of strategic KPIs traced end-to-end)
- H2: Semantic Model stability (measure conflicts, orphaned measures)
- H3: Data contract coverage (% of KPI lineage satisfied)
- H4: Action code completeness (% of KPIs referenced by actions)
- H5: Factsheet quality (% with required sections)

**Interpretation:**
- ≥80%: Excellent; no action needed
- 70–79%: Good; minor gaps (review with team)
- <70%: Investigate; may indicate schema changes or missing artifacts

### Gate 3: Schema & Python Tests

```bash
# JavaScript schema validation (Ajv)
cd tooling/validation && npm ci && npm run validate && cd ../..

# Python test suite (pytest)
python3 -m pytest tooling/tests/ products/ -q
```

**What it checks:**
- JSON schema conformance (brackets, KPIs, actions)
- Data contract syntax
- IR builder correctness
- Measure generator outputs

**Expected output:** All tests pass. Exit code 0.

### Gate 4: Fabric Checks (Optional, Requires Fabric)

```powershell
# If you have Fabric installed and generated TMDL
.\products\fabric\powerbi\tooling\run_fabric_checks.ps1
```

**What it checks:**
- TMDL syntax (indentation, DAX validity)
- Measure naming conventions
- DAX formula correctness
- Relationship cardinality

**Expected output:** No syntax errors. Exit code 0.

---

## Troubleshooting Quick Reference

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Stage 1: KPI not found` | Bracket references undefined KPI | Verify KPI exists in `core/kpi_catalog/KPI_Catalog.md`; check spelling |
| `Health scorecard: H1 < 50%` | Golden Thread broken; KPI not traced through use cases/actions | Add KPI to use case bracket; link action code |
| `TMDL generation: Measure not found` | DAX formula references measure that isn't defined | Add missing KPI to bracket's `influencing_kpi_ids` |
| `Fabric import fails: JSON parse error` | Corrupted PBIP JSON | Regenerate TMDL (`generate_tmdl_measures.ps1`) and retry |
| `fab auth fails` | Token expired or invalid | Run `fab auth login` again; verify Azure subscription access |

---

## Appendix: Command Cheat Sheet

```powershell
# Full local validation before merge (run from root)
.\tooling\run_stage1_checks.ps1
python3 tooling/health_scorecard.py
cd tooling/validation && npm ci && npm run validate && cd ../..
python3 -m pytest tooling/tests/ -q

# Regenerate and build (Windows)
.\tooling\generation\generate_tmdl_measures.ps1
.\products\fabric\powerbi\orchestrator\orchestrate_full_model.ps1

# Fabric operations
fab auth login
fab ls
fab import "ws.Workspace/Model.SemanticModel" -i ./dist/Domain.SemanticModel -f
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{"type":"Full"}'

# Health check
python3 tooling/ontology/registry_builder.py --repo-root . --strict
```

---

## When to Escalate

Contact the framework team if:
- Stage 1 fails with errors you cannot resolve
- Health scorecard drops below 60% unexpectedly
- Fabric import succeeds but semantic model has incorrect measures
- KPI lineage is circular or undefined
- New domain or platform integration is needed
