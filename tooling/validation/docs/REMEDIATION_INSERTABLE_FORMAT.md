# Insertable Remediation Format (SSOT)

Audits that find missing or inconsistent SSOT content MUST output remediation so that it **can be inserted directly** into the respective SSOT file without reformatting. Each finding includes an **InsertableRemediation** block.

## Structure (per finding)

- **ssot_type:** `kpi_catalog` | `usecase_bracket` | `data_contract` | `aurora_domain_mapping`
- **file_path:** Relative path from repo root (e.g. `core/kpi_catalog/KPI_Catalog.md`)
- **insert_location:** Human-readable hint where to insert (e.g. "In the YAML block with kpi_id: KPI-COM-016, under depends_on_measures:")
- **insertable_content:** Exact string to paste. Matches the file's indentation and style.

Optional:
- **insert_after_line:** If machine-applicable: line content or pattern after which to insert (for tooling).
- **replace_section:** If the fix is a replacement (e.g. replace entire depends_on_measures list), the exact replacement block.

---

## 1. KPI Catalog (core/kpi_catalog/KPI_Catalog.md)

### 1.1 Add one entry to depends_on_measures

- **When:** Formula references `[Measure Name]` but that KPI ID is not in `depends_on_measures`.
- **insert_location:** "In the YAML block with kpi_id: \<kpi_id\>, under technical.depends_on_measures:"
- **insertable_content:** One line, 4 spaces + list item. Example:
```yaml
    - KPI-COM-014
```
- Insert as new line after the last existing `- <id>` under `depends_on_measures:` (or after `depends_on_measures:` if empty).

### 1.2 Add a new KPI (full block)

- **When:** Referenced measure has no KPI in catalog (e.g. [Promo Cost] used but no kpi_id with dax_name "Promo Cost").
- **insert_location:** "In core/kpi_catalog/KPI_Catalog.md, inside the ```yaml block, before the next - kpi_id: or at end of block. Prefer inserting after KPI \<suggest_after_kpi_id\>."
- **insertable_content:** Full KPI block in same style as existing entries (indentation 2 spaces for top-level keys, 4 for nested). Example:
```yaml
- kpi_id: KPI-COM-014
  kpi_key: Promo Cost
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag: [Commercial]
  use_case_ref:
  - COM-002
  - COM-003
  - COM-004
  action_code_ref:
  - C-P4.1
  calc_type: amount
  business:
    purpose: "Total promotion cost for ROI and spend analysis."
    definition: "Sum of promo cost from promo systems."
    grain_scope: "Promo / period."
    unit_format: "EUR (2 decimals)"
    interpretation: "Input to Promo ROI %."
  technical:
    dax_name: "Promo Cost"
    formatString: "#,0.00"
    description: "Total promotion cost."
    dax_expression: |
      SUM ( fact_promo[Promo Cost] )
    depends_on_measures: []
    lineage:
    - fact_promo.Promo Cost
  governance:
    business_owner: "Head of Marketing Controlling"
    data_owner: "BI Engineering"
    steward: "Trade Marketing Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules: []
    version: "v1.0"
  metadata_quality:
    completeness_score: 1.0
    last_review: "<YYYY-MM-DD>"
```

---

## 2. Use Case Bracket (core/usecases/core/\<UC\>/UseCase_Bracket.yaml)

### 2.1 Add KPI to influencing_kpi_ids

- **When:** KPI is referenced by use case but not in orchestration.influencing_kpi_ids.
- **insert_location:** "Under orchestration.influencing_kpi_ids: in UseCase_Bracket.yaml"
- **insertable_content:** One line, 2 spaces + list item. Example:
```yaml
  - KPI-COM-014
```

### 2.2 Add action_code_id

- **When:** Action code should be subscribed but is missing from action_code_ids.
- **insert_location:** "Under orchestration.action_code_ids:"
- **insertable_content:**
```yaml
  - C-P4.1
```

---

## 3. Data Contract (core/data_contracts/domains/\<domain\>.yaml)

### 3.1 Add column to existing table

- **When:** DAX references table[Column] but column is not in contract for that table.
- **insert_location:** "In \<domain\>.yaml, under table '\<table_name\>', columns:"
- **insertable_content:** One line in contract column style (spaces to align with other columns). Example:
```yaml
      - {name: Promo Cost, type: currency, agg: sum}
```
Use same indentation as sibling columns (typically 6 spaces for fact columns).

### 3.2 Add new table to contract

- **When:** DAX references a table that does not exist in the domain contract.
- **insert_location:** "In \<domain\>.yaml, under dimension: or fact:, after table '\<suggest_after_table\>'."
- **insertable_content:** Full table block (name, description, purpose, grain, columns) in same YAML style as existing tables in that file.

---

## 4. Aurora Domain Mapping (products/fabric/powerbi/orchestrator/map_aurora_domains.ps1)

### 4.1 Add table to required tables for a domain

- **When:** KPI lineage references a table that is in the domain contract but not in AuroraDomainRequiredTables for that domain.
- **insert_location:** "In map_aurora_domains.ps1, in \$script:AuroraDomainRequiredTables, for key '\<DomainName\>', add the table to the array."
- **insertable_content:** Exact PowerShell line. The whole array is one line per domain. Example: add "fact_experience" to Commercial:
  - Before: `Commercial  = @("dim_date", "dim_org", ..., "fact_nps")`
  - insertable_content is the **full updated line** so it can replace the existing line:
```powershell
    Commercial  = @("dim_date", "dim_org", "dim_product", "dim_customer", "dim_promo", "fact_sales", "fact_plan_sales", "fact_promo", "fact_customer_events", "fact_customer_value", "fact_experience", "fact_nps")
```
So the remediation includes the complete array for that domain with the new table added.

---

## Report output

- **Markdown report:** For each finding, after "Remediation:", add a fenced block "Insertable (SSOT: \<type\>):" with the exact insertable_content and insert_location.
- **JSON report:** Each finding object has optional fields: `InsertableRemediation` with `ssot_type`, `file_path`, `insert_location`, `insertable_content`.

Workflow: Run audit → Review findings → Confirm which remediations to apply → Insert the insertable_content at the given location (manually or via tool/agent).

**Note:** Reports may show `insertable_content` in a generic code block; for `ssot_type: aurora_domain_mapping` the content is PowerShell and belongs in `map_aurora_domains.ps1`.
