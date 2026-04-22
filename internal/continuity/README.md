# Vendor Continuity Dossier

**Purpose:** Enable a new engineer, a customer, or an escrow agent to operate and regenerate the Analytics Strategy-to-Action Framework without the original team.

This dossier provides everything needed to:
- Understand the system architecture and critical dependencies
- Clone the repository and regenerate the framework from source
- Provision missing infrastructure and deploy to production
- Rotate credentials and activate security controls
- Run all validation gates locally
- Onboard a new engineer from day one
- Verify what the customer owns if vendor escrow is activated

---

## Contents

### 1. [Architecture Overview](architecture_overview.md)
**1500–2500 words.** Technical deep dive covering:
- System context diagram and data flow (YAML → IR → TMDL → PBIP)
- Key directories and their purposes (Core, Products, Tooling, Studio, Showcases)
- Top 10 critical dependencies with license and maintainer info
- **Critical path:** Files that must survive for the system to work at all
- Platform-specific implementation notes (Fabric/Power BI, Evidence.dev, OSS adapters)

**Read this if:** You are a new engineer, architect, or escrow agent needing to understand what this system does and how it works.

---

### 2. [Runbook](runbook.md)
**1000–1500 words.** Step-by-step operational procedures:
- **(a)** Fresh clone → run Aurora regeneration (end-to-end)
- **(b)** Provision missing fact tables (KNOWN_GAPS)
- **(c)** Deploy to a Fabric workspace
- **(d)** Rotate all credentials (Azure, Fabric, Metabase, etc.)
- **(e)** Run all 4 CI gates locally and interpret results

All commands are copy-pasteable and verified against CLAUDE.md and README.md.

**Read this if:** You are deploying to a new environment or troubleshooting a failed deployment.

---

### 3. [Handover Guide](handover_guide.md)
**800–1200 words.** Two-week onboarding curriculum for a new engineer:
- Day-by-day reading list pointing into the repo
- Critical meetings to have with business and infrastructure teams
- First task: Extend action code X-NEW.1 (end-to-end example of adding a feature)
- Glossary of key terms and abbreviations

**Read this if:** You are starting as a new engineer on this codebase or team.

---

### 4. [Escrow Checklist](escrow_checklist.md)
**400–800 words.** Explicit inventory of customer assets and activation procedure:
- **Customer OWNS:** KPI catalog, action codes, brackets, generator code, schemas, Aurora showcase, compliance package
- **Customer does NOT own:** Hosted SaaS infrastructure, branded marketing assets
- **How to activate:** Single command to verify the system is working (`python3 tooling/ontology/registry_builder.py --repo-root . --strict`)
- Testing matrix for 4 major deployment scenarios

**Read this if:** You are executing a vendor escrow agreement or verifying the customer has a working system.

---

## Quick Navigation

| Role | Start here |
|------|-----------|
| **New engineer** | Handover Guide → Architecture Overview |
| **Deployment engineer** | Runbook (skip to section c) |
| **Customer technical lead** | Architecture Overview → Escrow Checklist |
| **Escrow agent** | Escrow Checklist → Runbook (section e) |
| **Enterprise architect** | Architecture Overview (Critical Path section) |

---

## Document Maintenance

- **Last updated:** 2026-04-22
- **Framework version:** 2.0
- **Dossier version:** 1.0
- **Maintainer:** Analytics Platform Team

When the framework changes significantly (new products, major refactoring, credential rotation), update all 4 documents. Use this README as a checklist.

---

## Ownership

This dossier is owned by the vendor (original team). The customer receives a copy via:
1. **Live repository:** Always in sync; updated with each commit.
2. **Escrow delivery:** Packaged as part of the escrow package; snapshot as of delivery date.
3. **License transfer:** If applicable, transfer includes the right to regenerate and modify.

For questions, contact the Analytics Platform Team or your implementation lead.
