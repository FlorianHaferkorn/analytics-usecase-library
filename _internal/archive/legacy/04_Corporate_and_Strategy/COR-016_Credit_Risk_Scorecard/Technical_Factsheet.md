# Credit Risk Scorecard (PD/LGD/EAD) - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_credit_risk
  grain: exposure
  primary_key:
  - ExposureID
  required_columns:
  - name: ExposureID
    type: string
    role: attribute
  - name: OrgID
    type: string
    role: org_key
  - name: CustomerID
    type: string
    role: customer_key
  - name: Product
    type: string
    role: attribute
  - name: Portfolio Type
    type: string
    role: attribute
  - name: PD %
    type: decimal
    role: attribute
  - name: LGD %
    type: decimal
    role: attribute
  - name: EAD Amount
    type: decimal
    role: amount
  - name: Default Flag
    type: bool
    role: indicator
  - name: Default Date
    type: date
    role: helper
dims:
- name: dim_org
  grain: org
  primary_key:
  - OrgID
  required_columns:
  - name: Region
    type: string
  - name: LegalEntity
    type: string
- name: dim_customer
  grain: customer
  primary_key:
  - CustomerID
  required_columns:
  - name: Segment
    type: string
relationships:
- from: fact_credit_risk.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_credit_risk.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
```

## 2. Semantic Model Requirements
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- Required facts/dims per contract above.
- Ensure relationships are single-direction many-to-one (role-playing dates if needed).
- Provide conformed Org/Product/Initiative hierarchies.

## 3. Measures (DAX + Description)
Following KPIs require measures (DAX delivered separately):
- Probability of Default (PD) % (ID: fin.risk.pd.pct)
- Loss Given Default (LGD) % (ID: fin.risk.lgd.pct)
- Exposure at Default (EAD) Amount (ID: fin.risk.ead.amount)

## 4. Defaults & Formatting
- Apply correct format strings (currency, %, integer).
- Use display folders (01_Strategic, 02_Variance, etc.).
- Set data categories for Org/Initiative/Timeline fields.

## 5. Visual / Interaction Requirements
- Map visuals (cards, bridges, funnels) to required fields.
- Define drill paths for Org, Initiative, Time.
- Specify tooltip fields and sort-by logic.

## 6. Performance & Refresh
- Storage mode: Import (unless monthly snapshot suggests Hybrid).
- Refresh cadence aligned with corporate close cadence.
- Partitioning by FiscalPeriod where data volume is high.

## 7. RLS/OLS Requirements
- Org-based RLS (Region/Entity).
- Optional Initiative-based restrictions for project owners.

## 8. QA & Validation Rules
- Model_Validated
- Exposure_Reconciles

## 9. Model Mapping Reference
- PD % -> fact_credit_risk[PD %]
- LGD % -> fact_credit_risk[LGD %]
- EAD Amount -> fact_credit_risk[EAD Amount]
- Org -> dim_org[OrgID]
- Customer -> dim_customer[CustomerID]
