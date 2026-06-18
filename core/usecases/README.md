# Use Case Library

> **New to the repo?** Start with [`ONBOARDING.md`](../../ONBOARDING.md) at the repo root. This folder's README describes the structure for contributors who already know the framework.

## Purpose

The **Use Case Library** documents all business and technical use cases that the  
**ActionReady Analytics Framework** supports - from strategy-aligned core use cases to extended and industry-specific scenarios.

It represents the *WHAT*:  
What analytics delivers.  
What decisions it enables.  
What actions it triggers.

This folder is the bridge between business strategy (WHY) and technical implementation (HOW).

## Scope

Included:

- Core use cases relevant for every organization  
- Extended use cases for advanced analytics maturity  
- Industry-specific use cases tailored to vertical needs  
- Business & technical factsheets  
- Use case templates, mappings, and inventories

Not included:

- Semantic model implementation (see `core/semantic_models/`)  
- Data contracts (see `core/data_contracts/`)  
- Page templates (see `core/templates/`)  
- Customer-specific use cases (kept in separate project repos)

## Structure

```yaml
core/usecases/
  UseCase_Inventory.md      - Master list of all use cases
  templates/                - Business factsheet template and UseCase_Bracket template
    usecase_factsheet_business.md
    UseCase_Bracket_TEMPLATE.yaml
  core/                     - Core use cases (universal)        — IDs: XXX-NNN
  extended/                 - Advanced / extended use cases     — IDs: XXX-EXT-NNN
  industry/<sector>/        - Industry-specific scenarios       — IDs: XXX-IND-<S>NNN
```

> **Tier ID taxonomy:** the `EXT`/`IND-<sector-letter>` scheme, the folder trees above, and the sector-letter register (R=Retail, L=Logistics, M=Manufacturing) are ratified in [ADR-0004](../../docs/architecture/adr/0004-industry-variant-use-case-tier-taxonomy.md). Extension-tier use cases reference governed KPIs, action codes, and decision spines and pass the **same** Golden Thread gates as core use cases.

### UseCase_Inventory.md

The single source of truth for all use cases in the framework.  
Contains IDs, domains, KPIs, and status.  
Use Case → Action Code subscriptions are declared in each use case's `UseCase_Bracket.yaml` (`orchestration.action_code_ids`).

### templates/

Reusable templates for consistent documentation:

- Business Factsheet  
- UseCase_Bracket.yaml (technical configuration)  
These ensure every use case meets the same standard.

### core/

The fundamental use cases every company needs:

- Revenue / Margin performance  
- Pricing & discounting  
- Inventory insights  
- Forecast vs. Actual  
- Operational efficiency  
Core use cases are tightly coupled with Action Codes and the ActionReady semantic design.

### extended/

For organizations with higher analytical maturity:

- Customer churn prediction  
- Marketing attribution  
- Cashflow forecasting  
- Workforce efficiency  
Extended use cases typically require machine learning or advanced modeling.

### industry/

Tailored use cases for specific verticals (Retail, Manufacturing, CPG, Logistics):

- Store clustering  
- Space productivity  
- OEE breakdown  
- Production scrap analytics  
- ESG & sustainability scoring

**Instantiated:** `industry/retail/COM-IND-R001_Basket_Category_CrossSell/` — Basket & Category Cross-Sell (Retail), the first use case authored under the ADR-0004 tier taxonomy. The remaining industry/extension use cases tracked in `internal/project_mgmt/KNOWN_GAPS.md` §7 are authored deliberately, one governed slice at a time.

## Usage

### For Customers

- Identify which use cases are relevant for their strategy.  
- Understand how each use case links to KPIs, domains, and actions.  
- Prioritize a roadmap based on impact vs. complexity.

### For Delivery Teams

- Use templates to create consistent, actionable use cases.  
- Sync each use case with:
  - Domain (from Company Layer)  
  - Data Contract  
  - Semantic Model  
  - Action Codes (subscriptions via `UseCase_Bracket.yaml` `orchestration.action_code_ids`)  
  - Page Template (3-30-300)  
- Maintain UseCase_Inventory.md as the controlled governance artifact.

### For Framework Evolution

- Add new use cases only when they provide real cross-customer value.  
- Keep industry use cases optional and clearly marked.  
- Link all use cases to Action Codes for ROI and actionability tracking.

## Relations

- **WHY ->** Use cases originate from key questions and strategic KPIs in the Company Layer.  
- **HOW ->** Use cases rely on semantic, UX, and operational standards defined in the Operating Model.  
- **WITH WHAT ->** Action Codes, templates, and KPI Catalog turn use cases into consistent, repeatable assets.  
- **TEMPLATES ->** Use case templates ensure uniform structure and quality.

## Next Step

Start with:

1. `UseCase_Inventory.md`  
2. Then open `templates/usecase_factsheet_business.md`  
3. And explore core use cases under `core/`

This establishes a complete understanding of how analytics drives actionability and measurable business impact.

