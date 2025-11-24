# Cybersecurity Incident Monitoring - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_security_incidents
  grain: incident
  primary_key:
  - IncidentID
  required_columns:
  - name: IncidentID
    type: string
    role: attribute
  - name: Detected Date
    type: date
    role: date_key
  - name: Resolved Date
    type: date
    role: helper
  - name: Severity
    type: string
    role: status
  - name: Category
    type: string
    role: attribute
  - name: Source System
    type: string
    role: attribute
  - name: OrgID
    type: string
    role: org_key
dims:
- name: dim_org
  grain: org
  primary_key:
  - OrgID
  required_columns:
  - name: Region
    type: string
  - name: BusinessUnit
    type: string
- name: dim_date
  grain: date
  primary_key:
  - Date
  required_columns:
  - name: Year
    type: int
  - name: Month
    type: int
relationships:
- from: fact_security_incidents.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_security_incidents."Detected Date"
  to: dim_date.Date
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
- Cybersecurity Incident Count (ID: sec.incident.count)
- Critical Incidents Count (ID: sec.incident.critical.count)
- Mean Time to Resolve (MTTR) Hours (ID: sec.incident.mttr.hours)

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
- RI_OK
- Incidents_Tracked
- Severity_Classification_Consistent

## 9. Model Mapping Reference
- Incident ID -> fact_security_incidents[IncidentID]
- Severity -> fact_security_incidents[Severity]
- Category -> fact_security_incidents[Category]
- Detected Date -> fact_security_incidents[Detected Date]
- Resolved Date -> fact_security_incidents[Resolved Date]
- Org -> dim_org[OrgID]
- Date -> dim_date[Date]
