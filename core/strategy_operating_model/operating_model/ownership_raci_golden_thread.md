# Ownership and RACI for the Golden Thread

## 1. Purpose

This document defines **who is accountable and responsible** for each layer of the Golden Thread (Strategy → KPIs → Key Questions → Use Cases → Semantic Model → Measures → Reports → Actions).

Explicit ownership ensures that "governance before automation" and "first, pragmatic governance" are operable: changes have a clear owner, and drift can be traced back to accountability.

**RACI:** R = Responsible (does the work), A = Accountable (owns the outcome, single point), C = Consulted, I = Informed.

---

## 2. Golden Thread Layers and Ownership

| Layer | Artifact / Location | Accountable (A) | Responsible (R) | Consulted (C) | Informed (I) |
|-------|---------------------|-----------------|-----------------|---------------|--------------|
| **Strategy** | Company strategy, strategic focus areas, executive key questions | Executive / Strategy Owner | Strategy & Planning; Domain Leads | Domain Owners; Finance | Analytics; Delivery |
| **Strategic KPIs** | KPI Catalog (`core/kpi_catalog/`), KPI definitions | Domain Owner (per KPI or domain) | KPI Steward / Controlling Lead | Analytics; Semantic Model Owner | Delivery; Report Owners |
| **Key Questions** | Company layer (`reporting_principles.md`); Use Case Business Factsheets (Core Business Questions) | Domain Owner (per use case) | Use Case Owner / Business Analyst | Analytics | Delivery |
| **Use Cases** | Use Case Inventory; Business Factsheets & UseCase_Bracket.yaml (`core/usecases/`) | Domain Owner (primary domain of use case) | Use Case Owner / Product Owner Analytics | KPI Steward; Action Code Owner; Analytics | Delivery; Report Owners |
| **Action Codes** | Action Code YAML (`core/action_codes/`) | Domain Owner or Enterprise Governance (per action code) | Action Code Owner / Process Owner | Use Case Owner; Analytics | Delivery; Report Owners |
| **Data Contracts** | Domain and source contracts (`core/data_contracts/`) | Data Owner / Domain Owner | Data Engineer; Analytics | Semantic Model Owner | Delivery |
| **Semantic Model** | Model definition, measures, TMDL (implementation-specific) | Semantic Model Owner / Analytics Lead | BI Developer; Analytics | Domain Owner; KPI Steward | Delivery; Report Owners |
| **Reports (3-30-300)** | Page templates, report definitions (implementation-specific) | Report Owner / Domain or Executive | Report Developer; UX | Use Case Owner; Semantic Model Owner | End Users |

---

## 3. Domain Ownership Summary

Domains own **meaning and prioritization** for their slice of the Golden Thread.

| Domain | Typical Accountable (A) for KPIs, Use Cases, Action Codes in domain |
|--------|----------------------------------------------------------------------|
| Commercial | CCO / Head of Sales; Commercial Controlling Lead |
| Finance | CFO / Finance Controller; Treasury; Cost Controlling |
| Operations | COO / Head of Operations; Plant/Asset Manager |
| Supply Chain | VP Supply Chain; Demand/Supply Planning Lead |
| Experience & Service | Head of Customer Service; Operations (for XD-002 resource) |
| Enterprise (XD-003, cross-domain) | CEO / Executive Team; Strategy Office |

Ownership is **role-based**, not person-named, so it survives reorganizations. Customer implementations replace these with their own roles.

---

## 4. Change Flow (Who Triggers What)

- **Strategy or focus area change** → A: Executive / Strategy; flows to KPI relevance and use case prioritization.
- **New or changed KPI** → A: Domain Owner; KPI Catalog updated; use cases and semantic model follow (reference only).
- **New or changed Use Case** → A: Domain Owner; references existing KPIs and Action Codes; factsheets and inventory updated.
- **New or changed Action Code** → A: Domain or Enterprise Owner; `UseCase_Bracket.yaml` (`orchestration.action_code_ids`) updated if use case linkage changes.
- **Semantic model or measure change** → A: Semantic Model Owner; must stay aligned with KPI Catalog and use case requirements; Stage 1 / Fabric checks enforce consistency.

No layer may redefine meaning owned by another layer (e.g. use cases do not define KPI logic; reports do not define measures).

---

## 5. Relationship to Other Documents

- **Golden Thread logic:** `golden_thread_strategy_to_action.md`
- **Domain boundaries and scope:** `core/strategy_operating_model/company/domains.md`
- **Data governance (quality, lineage, security):** `data_governance.md`
- **Stage 1 and validation:** `AGENTS.md`, `tooling/run_stage1_checks.ps1`

This document defines **who** owns each layer; the other documents define **what** and **how**.
