---
id: "COR-003"
title: "ESG & Compliance Monitoring"
domain: "Corporate and Strategy"
owner: "Head of Sustainability / Compliance Office"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
supports_strategic_kpi: ["ESG-Aligned Revenue %", "Carbon Emission Intensity", "Compliance Incidents Count"]
supports_strategic_kpi_ids: ["esg.aligned_revenue.pct", "esg.co2.total.tco2e", "gov.compliance.incidents.count"]
action_codes: ["PC2", "C4", "O2", "O3", "SP1"]
expected_impact: "+10-20 % rating improvement; -10-15 % Scope 1-2 emissions; -30 % incident frequency"
required_kpi_ids: []
required_kpis: {}

dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: ["Org.Region>Area>Store","Product.Category>Subcategory>SKU","Channel","Time.Year>Month>Week"]
filters_default: ["Time: Last 12M","Org: All","Channel: All"]
qa_asserts: ["RI_OK"]

data_requirements:
  facts:
    - name: fact_main
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "Units Qty", type: int, role: quantity }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: Channel, type: string, role: channel }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_product
      grain: product
      primary_key: [ProductID]
  relationships:
    - { from: fact_main.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_main.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_main.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }

model_mapping:
  "Net Sales Amount": "fact_main[Net Sales Amount]"
  "Units Qty": "fact_main[Units Qty]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"---

# ESG & Compliance Monitoring

## 1. Business Goal
Integrate Environmental, Social, and Governance (ESG) metrics into business performance management to ensure transparency, regulatory compliance, and sustainable value creation.

## 3. Key Questions
- How do we perform against ESG and compliance KPIs (environmental, social, governance)?  
- Are we on track for CSRD and EU taxonomy disclosure requirements?  
- Which entities or sites pose compliance or sustainability risks?  
- What share of revenue and investments are taxonomy-aligned?  
- How do ESG improvements correlate with financial performance?

 

## 5. Required Attributes (Business-Level)
- Org (legal entity, plant, region)  
- Date (month or quarter end)  
- Energy Consumption, CO2 Emissions (Scope 1-3)  
- Revenue, Headcount, Hours Worked  
- Incident Type, Severity, Resolution Date  
- Optional: Supplier, Project, ESG Category (E/S/G), Certification Level  

 

## 7. Scope & Assumptions
- CO2 conversion factors based on GHG Protocol.  
- Scope 1 = direct emissions, Scope 2 = purchased energy, Scope 3 = value chain.  
- ESG-aligned revenue calculated per EU Taxonomy.  
- Compliance incidents recorded post-validation by Legal/Compliance.  
- Data aggregated monthly; restated quarterly for audit consistency.

 

## 9. Edge Cases & QA Rules
- Emissions cannot be negative.  
- ESG-Aligned Revenue % must not exceed 100 %.  
- Incident records must include resolution date.  
- Referential integrity >= 99.9 % across Date/Org/Category.  
- All metrics documented with source and methodology (audit trail).

 

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Implement energy efficiency initiatives and green sourcing | PC2 | CO2 -10-20 %; cost savings improve |
| Increase workforce diversity and inclusion programs | C4 | Diversity improves; engagement improves |
| Strengthen safety programs in high-risk sites | O2 | LTIFR -30 % |
| Automate ESG data collection and validation workflows | O3 | Reporting latency reduces; audit reliability improves |
| Align sustainability KPIs with executive compensation | SP1 | Accountability improves; ESG target compliance improves |

 

## 13. Related Processes
Sustainability Reporting -> Risk & Compliance Management -> Audit & Assurance -> Supplier Assessment -> Corporate Governance.

 

## 15. Cross-References
- Related Use Cases:  
  `[COR-004 Strategic KPI Dashboard](../COR-004_Strategic_KPI_Dashboard/FactSheet.md)`  
  `[OPS-003 Purchase Price Variance](../../02_Operational_Efficiency/OPS-003_Purchase_Price_Variance/FactSheet.md)`  
  `[COM-002 Gross Margin Analysis](../../01_Commercial/COM-002_Gross_Margin_Analysis/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

 

_Last updated: 04.11.2025_



