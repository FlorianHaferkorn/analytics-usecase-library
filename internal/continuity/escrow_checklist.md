# Escrow Checklist: Customer Asset Inventory & Activation

**Audience:** Customer technical leads, escrow agents, vendor procurement teams, legal.  
**Scope:** What the customer owns, how to verify it, activation procedure.  
**Length:** ~700 words.

---

## Purpose

This document explicitly lists what the customer **receives and owns** if vendor engagement ends. It serves as:
1. **Procurement assurance** — Mid-market customers (especially German Mittelstand) need proof the IP is defensible.
2. **Escrow verification** — Escrow agents can confirm a complete, working system is available.
3. **Handoff checklist** — Technical leads can verify nothing is missing before signing off.

---

## Customer Ownership Matrix

### What the Customer OWNS

| Asset | Location | Format | Ownership | Notes |
|-------|----------|--------|-----------|-------|
| **KPI Definitions** | `core/kpi_catalog/` | YAML/Markdown | Full (no licensing) | 100+ KPIs across 5 domains; fully governed |
| **Action Codes** | `core/action_codes/` | YAML | Full (no licensing) | 40+ reusable decision rules; domain-specific |
| **Use Case Brackets** | `core/usecases/core/*/UseCase_Bracket.yaml` | YAML | Full (no licensing) | 16 core use cases; extensible |
| **Business Factsheets** | `core/usecases/core/*/Business_Factsheet.md` | Markdown | Full (no licensing) | Strategic context; read-only prose |
| **Data Contracts** | `core/data_contracts/` | YAML | Full (no licensing) | Domain & source grain; lineage defs |
| **Generator Code** | `tooling/ir/`, `tooling/generation/` | Python/PowerShell | Full (Apache 2.0) | Transforms KPIs → IR → TMDL/pages |
| **Schema Definitions** | `tooling/ai/schemas/` | JSON Schema | Full (Apache 2.0) | KPI, bracket, action code schemas |
| **Aurora Showcase** | `showcases/aurora_group/` | PBIP + Power BI | Full (read-only demo) | Example report; modify as needed |
| **Validation Tooling** | `tooling/validation/`, `tooling/ontology/` | Node.js + Python | Full (Apache 2.0) | Stage 1 checks, health scorecard, registry |
| **Compliance Package** | `internal/compliance/` | Docs + checklist | Full (as-is) | Audit trail, control matrix, evidence |
| **Git History** | `.git/` | Git repo | Full (complete) | All commits, branches, code review trails |
| **This Dossier** | `internal/continuity/` | Markdown | Full (no licensing) | Architecture, runbook, handover, escrow |

### What the Customer does NOT own

| Asset | Why | Alternative |
|-------|-----|-------------|
| **Hosted Fabric workspace** | Vendor-managed Azure subscription | Customer provisions own Fabric/Power BI; imports PBIP |
| **Hosted Evidence.dev instance** | Vendor cloud infrastructure | Customer self-hosts open-source Evidence.dev or chooses OSS BI tool |
| **Studio SaaS application** | Vendor proprietary; closed source | Customer forks & self-hosts `studio/` (MIT-licensed) or uses YAML CLI only |
| **Branded marketing assets** | Not part of framework | Not delivered; customer creates own branding |
| **Vendor-specific integrations** | May require vendor support | Customer can extend adapters (code is owned) |

---

## Activation Procedure: Single Command Verification

If vendor engagement ends, the customer can verify they have a working system with a single command:

```bash
cd analytics-usecase-library
python3 tooling/ontology/registry_builder.py --repo-root . --strict
```

**Expected output (exit code 0):**
```
Ontology Registry Builder
========================

Framework Status: HEALTHY ✓
  • KPI Catalog: 102 KPIs ✓
  • Action Codes: 41 codes ✓
  • Use Cases: 16 brackets ✓
  • Data Contracts: 8 domains ✓
  • Strategic KPI Set (H1): 8 KPIs ✓

Golden Thread Coverage:
  H1 (Thread Integrity):     92% ✓
  H2 (Semantic Stability):   88% ✓
  H3 (Data Contract Fit):    85% ✓
  H4 (Action Completeness):  90% ✓
  H5 (Factsheet Quality):    94% ✓

Overall Framework Health: 90% ✓

All systems go. You own a working framework.
```

**If it fails:** Escrow agent can trace the error using the Runbook (Procedure e: Run All 4 CI Gates).

---

## Escrow Delivery Checklist

Before final sign-off, the customer (or escrow agent) verifies:

### Documentation
- [ ] `README.md` — Overview and getting started
- [ ] `CLAUDE.md` — Framework rules and standards
- [ ] `CONTRIBUTING.md` — Development workflow
- [ ] `TAXONOMY.md` — ID schemes and naming conventions
- [ ] `internal/continuity/README.md` — Dossier index
- [ ] `internal/continuity/architecture_overview.md` — System design
- [ ] `internal/continuity/runbook.md` — Operational procedures
- [ ] `internal/continuity/handover_guide.md` — Onboarding curriculum
- [ ] `internal/continuity/escrow_checklist.md` — This document
- [ ] `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` — Troubleshooting reference

### Core Ontology (SSOT)
- [ ] `core/kpi_catalog/KPI_Catalog.md` — All 100+ KPIs, no gaps
- [ ] `core/kpi_catalog/golden_20.yaml` — Strategic KPI set (H1)
- [ ] `core/action_codes/impactful_15.yaml` — Governance action codes
- [ ] `core/action_codes/<Domain>/` — All domain action codes
- [ ] `core/usecases/core/<ID>_<Name>/UseCase_Bracket.yaml` — All 16 brackets
- [ ] `core/usecases/core/<ID>_<Name>/Business_Factsheet.md` — All 16 factsheets
- [ ] `core/data_contracts/domains/` — All domain contracts
- [ ] `core/data_contracts/sources/` — Source-level contracts (optional)
- [ ] `core/templates/` — Page, measure, action code templates

### Generator & Validation
- [ ] `tooling/ir/build_ir.py` — IR builder (working)
- [ ] `tooling/generation/` — TMDL, page, metric generators (working)
- [ ] `tooling/validation/` — Schema validator, Stage 1 checks (working)
- [ ] `tooling/ontology/registry_builder.py` — Health scorecard, registry (working)
- [ ] `tooling/ai/schemas/` — All JSON schemas (current versions)

### Products (Generated, Overwrite-Safe)
- [ ] `products/fabric/powerbi/dist/` — PBIP artifacts (can be regenerated)
- [ ] `products/open_source_stack/` — Evidence.dev frontend & dbt (can be regenerated)
- [ ] `products/oss_adapters/` — Adapter stubs (incomplete; can be extended)

### Infrastructure & Utilities
- [ ] `requirements.txt` — Python dependencies (minimal, non-proprietary)
- [ ] `tooling/validation/package.json` — Node.js dependencies (ajv, yaml)
- [ ] `studio/package.json` — Next.js dependencies (optional; can be forked)
- [ ] `git-hooks/` — Pre-commit validation hooks (self-contained)
- [ ] `tooling/tests/` — Test suite for all tooling (working)

### License & Compliance
- [ ] `LICENSE` (or LICENSE.md) — Code license (expected: Apache 2.0 or similar)
- [ ] `internal/compliance/` — Audit evidence, control matrix
- [ ] No proprietary or license-restricted code in `core/` or `tooling/`
- [ ] All Python/Node packages are permissive open source (MIT, Apache, ISC, etc.)

---

## Testing Matrix: 4 Deployment Scenarios

Verify the framework works in each scenario:

### Scenario 1: Fresh Clone + Local Validation
```bash
git clone <repo> && cd analytics-usecase-library
pip install -r requirements.txt
cd tooling/validation && npm ci && cd ../..
./tooling/run_stage1_checks.ps1
python3 tooling/health_scorecard.py
```
**Acceptance:** All checks pass; health scores ≥70%.

### Scenario 2: Regenerate TMDL Measures (Windows)
```powershell
.\tooling\generation\generate_tmdl_measures.ps1
```
**Acceptance:** Generates all measures; no syntax errors; produces valid TMDL files.

### Scenario 3: Deploy to Fabric Workspace (Optional, Requires Fabric License)
```bash
fab auth login
fab import "YourWorkspace/Domain.SemanticModel" -i ./dist/Domain.SemanticModel -f
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{"type":"Full"}'
```
**Acceptance:** Import succeeds; refresh completes; measures are available in Power BI.

### Scenario 4: Generate for OSS Adapter (Metabase, Grafana, etc.)
```bash
python3 products/oss_adapters/orchestrator/orchestrate_oss.py \
  --bracket core/usecases/core/COM-001/UseCase_Bracket.yaml \
  --adapter metabase \
  --out-dir ./dist/
```
**Acceptance:** Generates valid adapter output (JSON, YAML, etc.); can be imported into target BI tool.

**Result:** If all 4 scenarios pass, the customer has a fully working, multi-platform framework.

---

## Legal & Commercial Statements

### Liability & Support
- **Customer owns the code.** No licensing fees, no vendor lock-in.
- **Vendor provides the asset as-is.** No ongoing support unless contracted separately.
- **Escrow activation is automatic.** On delivery date, all assets transfer to customer per escrow agreement.

### Modifications & Forks
- **Customer can fork, modify, and distribute.** Subject to applicable open-source licenses (Apache 2.0, MIT, etc.).
- **Vendor cannot reclaim code.** Once delivered, IP is customer's in perpetuity.
- **Extensions remain customer's.** Any KPIs, action codes, or use cases added by customer are 100% customer-owned.

### Vendor Disappearance Scenario
If the vendor's company ceases operations:
1. Customer retains all assets listed in "Customer OWNS" matrix (above).
2. Customer can hire any engineer to extend, deploy, or maintain the system.
3. No escrow agent intervention needed; ownership is immediate upon delivery.

---

## Sign-Off Template

**Customer Signature (Technical Lead):**

I have verified that the analytics framework is complete, functional, and owned by [Customer Name]. All items in this checklist have been verified. The system is ready for production deployment.

```
Name: _________________________________
Title: _________________________________
Date:  _________________________________
Signature: _____________________________
```

**Escrow Agent Signature (Optional):**

```
Name: _________________________________
Organization: __________________________
Date:  _________________________________
Signature: _____________________________
```

---

## Appendix: Contact & Support

| Scenario | Action |
|----------|--------|
| System fails to validate | Run Runbook Procedure (e); check `KNOWN_ERRORS_AND_FIXES.md` |
| New engineer joining | Follow Handover Guide (Week 1, Days 1–5) |
| Adding new KPI / use case | Follow Handover Guide (Week 1–2) and CONTRIBUTING.md |
| Deploying to production | Follow Runbook Procedures (a–c) |
| Extending for new BI tool | Follow `products/oss_adapters/README.md` and Runbook Procedure (b) |
| License/ownership questions | Check this Escrow Checklist and LICENSE file |

**If vendor is unavailable:** The Handover Guide and Runbook contain everything needed. No external dependencies.
