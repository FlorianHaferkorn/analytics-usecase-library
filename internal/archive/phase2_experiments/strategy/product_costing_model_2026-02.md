# Product Costing Model (2026-02)

Purpose: define a consistent costing and effort model for all products and
the required customer roles. This is a template and can be parameterized by
rate cards and scope.

Status: proposal only. No commercial rates included.

---

## 1) Products in scope

P1. Core Framework Adoption (Silver -> Action Ready)
P2. Platform Product: Fabric / Power BI implementation
P3. Proposal Costing Product
P4. Automation and CI/CD enablement
P5. Operating Model and Governance enablement

Optional add-ons (if required):
- Data platform integration beyond Silver readiness
- Additional platform products (Tableau, Looker, etc.)

---

## 2) Estimation model (how to cost)

Total cost = sum( role_day_rate * role_days )

Scope drivers (primary):
- Number of use cases (UC)
- Number of data domains (DD)
- Number of source systems (SS)
- Number of environments (ENV: dev/test/prod)
- Number of report pages (RP)
- Number of KPIs (KPI)

Scaling rules (baseline multipliers):
- +1 use case: +40-60% of base effort
- +1 data domain: +20-30% of base effort
- +1 source system: +10-20% of base effort
- +1 environment: +10-15% of base effort
- +1 report page: +5-10% of base effort

Assumption baseline for "Day-1 greenfield":
- UC = 1, DD = 1, SS = 1, ENV = 1 (dev only), RP = 3-5, KPI = 8-12
- Silver layer exists and passes data contract validation
- Standard security model, no custom RLS/OLS

---

## 3) Delivery roles (provider) and customer roles

Delivery roles (provider):
- Solution Architect (SA)
- Data Architect (DA)
- Data Engineer (DE)
- Analytics Engineer (AE)
- BI Developer (BI)
- UX / Report Designer (UX)
- QA / Validation Engineer (QA)
- Project Manager (PM)

Customer roles required:
- Product Owner / Business Sponsor (PO)
- Business SME (SME)
- Data Owner / Steward (DO)
- Platform Admin (PA)
- Security / Compliance (SEC)
- Finance / Controlling (FIN) for costing product

Minimum customer engagement (per use case):
- PO: prioritization + acceptance
- SME: KPI definitions and decision logic
- DO: data access and data quality sign-off
- PA/SEC: workspace and access provisioning

---

## 4) Effort matrix (baseline day-1, UC=1, DD=1, SS=1)

### P1. Core Framework Adoption (Silver -> Action Ready)

Deliverables:
- Use case factsheets (Business + Technical)
- KPI mapping to catalog
- Silver data contract pack (domain + source)
- Action code alignment

Effort (person-days):
- SA: 1.0
- DA: 1.0
- AE: 1.5
- DE: 1.0
- PM: 0.5
- QA: 0.5
Total: 5.5

Customer roles needed:
- PO (0.5), SME (1.0), DO (0.5)

### P2. Platform Product: Fabric / Power BI implementation

Deliverables:
- Core semantic model skeleton
- Measures generated from KPI catalog
- Report scaffold (3-5 pages)
- Workspace setup and pipeline stub

Effort (person-days):
- SA: 0.5
- AE: 1.5
- BI: 2.0
- UX: 1.0
- DE: 0.5
- QA: 0.5
- PM: 0.5
Total: 6.5

Customer roles needed:
- PO (0.5), SME (0.5), PA (0.5), SEC (0.25)

### P3. Proposal Costing Product

Deliverables:
- Cost driver catalog and assumptions
- Allocation and pricing logic
- Scenario model and output templates

Effort (person-days):
- SA: 0.5
- DA: 0.5
- AE: 1.5
- BI: 1.0
- UX: 0.5
- QA: 0.5
- PM: 0.5
Total: 5.0

Customer roles needed:
- FIN (1.0), SME (0.5), PO (0.25)

### P4. Automation and CI/CD enablement

Deliverables:
- Stage 1 validation integration
- Product checks integration
- Release pipeline stub

Effort (person-days):
- SA: 0.5
- AE: 1.0
- DE: 0.5
- QA: 0.5
- PM: 0.25
Total: 2.75

Customer roles needed:
- PA (0.5), SEC (0.25)

### P5. Operating Model and Governance enablement

Deliverables:
- Operating model onboarding
- Governance roles and RACI
- Quality gates and sign-off flow

Effort (person-days):
- SA: 1.0
- PM: 0.5
- QA: 0.25
Total: 1.75

Customer roles needed:
- PO (0.5), SME (0.5), DO (0.25)

---

## 5) Total baseline effort (day-1 bundle)

Provider effort (sum P1..P5): 21.5 person-days
Customer effort: 6.5 person-days

This yields a realistic "greenfield-in-a-day" outcome when:
- Base scope assumptions are met
- Silver data is ready
- Customer roles are available for decisions and access

---

## 6) Scaling example (additional use cases)

For each additional use case:
- P1 +50% (factsheets, mapping, action codes)
- P2 +40% (semantic + report)
- P3 +30% (if costing is in scope for that domain)
- P4 +10% (if pipeline extends)
- P5 +0-10% (if governance already set)

Example UC=3, DD=2, SS=2:
Baseline * 2.0 to 2.5 total effort depending on data complexity.

---

## 7) Exclusions and risk factors

Exclusions (not in baseline):
- Silver layer build, data remediation, MDM
- Custom RLS/OLS models
- Complex forecasting or ML
- Multi-region tenancy constraints

Risk factors that increase effort:
- Poor data quality or missing Silver layer
- Unclear KPI ownership or definitions
- Multiple conflicting stakeholder requirements
- Custom security or audit requirements

---

## 8) Next steps to finalize pricing

Required inputs:
- Agreed rate card (role_day_rate)
- Confirmed scope drivers (UC, DD, SS, ENV, RP)
- Data readiness assessment for Silver layer
- Confirmed platform and tenant access

Output:
- Fixed price or T&M range
- Delivery plan with role allocation
- Customer responsibility matrix

Location: _internal/strategy/product_costing_model_2026-02.md
