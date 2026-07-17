# KPI Catalog

> **Canonical definitions:** [KPI_Catalog.md](KPI_Catalog.md).  
> This README is for navigation and overview only; it must not redefine KPI semantics.

> **Standards alignment (industry-standard definitions, per domain):** KPIs carry an optional
> `standard_ref` mapping their definition to an external standard/ontology (SCOR-DS, FIBO/IFRS,
> ESRS, ISO-30414…) with an explicit alignment + drift note — *reference, don't redefine*.
> Per-domain audits live under [`standards/`](standards/): supply chain →
> [SCM ↔ SCOR alignment & drift audit](standards/SCM_SCOR_alignment.md); finance →
> [Finance ↔ IFRS/APM alignment & drift audit](standards/FIN_IFRS_alignment.md); operations →
> [Operations ↔ ISO 22400 alignment & drift audit](standards/OPS_ISO22400_alignment.md); service →
> [Service ↔ ITIL 4 / ISO/IEC 20000 alignment & drift audit](standards/SVC_ITIL_ISO20000_alignment.md);
> commercial → [Commercial ↔ IFRS 15 / managerial-convention alignment & drift audit](standards/COM_Commercial_alignment.md);
> customer → [Customer & Market alignment & drift audit](standards/CUST_Customer_alignment.md); people →
> [People & Culture ↔ ISO 30414 alignment & drift audit](standards/HR_ISO30414_alignment.md); governance →
> [Enterprise & Governance alignment & drift audit](standards/GOV_ActionGovernance_alignment.md).

## Purpose

The **KPI Catalog** provides a governed, cross-domain inventory of all KPIs and measures used in the  
**ActionReady Analytics Framework**.  
It ensures consistency, clarity, and alignment between business, analytics, AI/Copilot, and reporting.

This catalog forms the foundation for semantic modeling, actionability, and long-term governance.

---

## Scope

Included:

- Strategic and operational KPIs per domain
- Measure dictionary references
- Calculation logic, naming rules, formats
- KPI → Domain → Use Case → Action Code mapping (action code subscriptions per use case in `UseCase_Bracket.yaml` `orchestration.action_code_ids`)
- Authoritative definitions required for AI/Copilot

Not included:

- Tool-specific implementation (covered in semantic models)
- Report/page design (see templates)
- Customer-specific KPIs (kept outside the framework)

---

## Usage

### For Customers

- Validate KPI consistency across business units  
- Ensure alignment between strategy and analytics  
- Use as onboarding reference for new teams or processes  
- Provide a single source of truth for AI/Copilot semantic grounding

### For Delivery Teams

- Implement KPIs consistently across projects  
- Reuse calculation logic and measure patterns  
- Synchronize KPI definitions with Action Codes and page templates  
- Ensure every measure has:  
  - Purpose  
  - Definition  
  - Grain  
  - Unit/Format  
  - Lineage  
  - QA check  

### For Framework Evolution

- Add new KPIs only if they provide cross-customer value  
- Version major changes through semantic model governance  
- Keep dictionaries clean, non-duplicated, and fully linked

---

## Supporting KPIs and data requirements

- **Supporting KPIs** (e.g. `sales.price.list.amount`, `sales.price.net.amount`) are defined in the catalog with `kpi_role: supporting`. They are referenced in `depends_on_measures` by strategic/diagnostic KPIs (e.g. `sales.price.realization_pct`) and must be listed in the use case’s `orchestration.influencing_kpi_ids` so the measure generator emits them.
- **Data requirement:** Each KPI’s `technical.lineage` lists the fact/dimension columns required for its measure (e.g. `fact_sales.List Price Amount`). The **semantic model** must provide these tables and columns; they are defined by the **domain data contracts** (`core/data_contracts/domains/`). The pipeline that builds the semantic model from the contract (e.g. Fabric table_ops) ensures the model satisfies this data need. When adding or changing KPIs, ensure the corresponding domain contract includes the required columns.
- **Measure dependencies:** If a KPI’s DAX formula references another measure by name (e.g. `[Net Sales Amount]`, `[Cost of Goods Sold Amount]`), set `technical.depends_on_measures` to the list of **KPI IDs** whose `dax_name` matches those measure names. The TMDL measure generator (IR-first) resolves this closure and emits measures in dependency order so that referenced measures exist before dependents. This avoids “measure not found” errors when adding use cases or building shared semantic models.
- **Same issue in another domain or report:** Fix only in the **KPI catalog** (SSOT). Add the referenced KPI ID to the **dependent** KPI's `technical.depends_on_measures`. Do not duplicate dependency information in brackets or reports. Stage 1 validates: no duplicate IDs within a KPI's `depends_on_measures` list, and every listed ID must exist in the catalog. Then run `tooling/ir/build_ir.py --kpi-catalog core/kpi_catalog` and regenerate measures.
- **Tool-agnostic vs. tool-specific:** The catalog is the SSOT for **calculation logic** (formula, operands, lineage). Measure **naming** (e.g. `dax_name` for TMDL/DAX) is tool-specific; in a strict tool-agnostic setup it would be derived from the formula and naming conventions rather than stored here. Run **`tooling/validation/audit_ssot_content.ps1`** to proactively surface in-content issues (semantic duplicates, formula refs not in depends_on_measures, duplicate dax_name) for human review.

---

## Relations

- **WHY ?** Strategic KPIs from the Company Layer define what belongs here.  
- **HOW ?** Semantic Layer & Measure System govern design, naming, and logic.  
- **WITH WHAT ->** Action Codes and Templates use this catalog as input.
- **TEMPLATES ->** Factsheet templates reference KPIs directly.

---

**Location:**  
`core/kpi_catalog/README.md`

