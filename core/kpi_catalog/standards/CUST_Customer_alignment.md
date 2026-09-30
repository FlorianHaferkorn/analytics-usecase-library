# Customer & Market KPIs — standards alignment & drift audit

> **Standards:** ISO 10002 (complaints), IFRS 15 (lifetime revenue base), and named CRM/marketing conventions (CLV, active/churn/retention, revenue-at-risk); NPS is proprietary (Bain). **Method:** each governed KPI is mapped with an explicit `alignment`
> (exact / partial / none) + drift note in `standard_ref`, naming the discipline where there is no
> governing standard. Part of the per-domain standards program (SCM→SCOR, Finance→IFRS,
> Operations→ISO 22400, Service→ITIL/ISO 20000, Commercial→IFRS 15/convention).

## Read

Customer is a **mostly-convention** domain, like Commercial. Only two KPIs touch a real standard: complaint handling (ISO 10002) and the revenue base of lifetime revenue (IFRS 15). CLV, active/churned/retention and revenue-at-risk are established **marketing-analytics conventions** — pin their window/base definitions rather than claim a standard. **NPS is proprietary Bain**, duplicated with `svc.nps.index` — consolidate to one governed NPS.

## Mapping table

| KPI | Standard / discipline | Alignment | Drift note / recommendation |
|---|---|---|---|
| `KPI-SVC-001` | `ISO 10002` Complaints handling — complaint volume | **partial** | Complaint count feeds the ISO 10002:2018 complaints-handling process (the standard governs how complaints are captured/handled, not a specific count formula). Related to crm.nps / svc.* customer-experience measures. |
| `KPI-CUS-005` | `IFRS 15` Customer lifetime revenue (accumulated) | **partial** | The revenue base is IFRS 15 (net sales per customer accumulated from first purchase); the lifetime accumulation itself is a CRM-analytics convention, not an IFRS construct. |
| `KPI-CUS-006` | `Marketing analytics — CRM (convention)` Active customer count | **none** | Active-customer count (distinct customers with a qualifying transaction) is a CRM-analytics convention; the 'qualifying' window is a definitional choice to pin, not a standard. |
| `KPI-CUS-004` | `Marketing analytics — CRM (convention)` Churned customer count | **none** | Churn count (active in look-back, inactive now) is a CRM-analytics convention; churn-window definition must be pinned. No governing standard. |
| `KPI-CUS-001` | `Marketing analytics — CRM (convention)` Customer Lifetime Value | **none** | CLV (discounted expected future gross margin per customer) is a well-established marketing-analytics model, not a governed standard. The GM base ties to IFRS 15 / IAS 2; the forward-looking model is convention. |
| `KPI-CUS-003` | `Bain NPS (proprietary)` Net Promoter Score | **none** | NPS is a proprietary Bain & Company methodology, not an open standard. Duplicate of svc.nps.index — consolidate to one governed NPS. ISO 10002 / general customer-satisfaction monitoring is the standards-based alternative. |
| `KPI-CUS-002` | `Marketing analytics — CRM (convention)` Customer retention rate | **none** | Retention (end/start active customers) is a CRM-analytics convention. Note it is not the complement of churn unless the customer base and windows are defined consistently — pin both. |
| `KPI-OPS-001` | `Marketing analytics — CRM (convention)` Revenue at risk (churn-weighted) | **none** | Revenue at risk (net sales x churn rate) is a composite CRM convention built on IFRS 15 revenue and the churn convention; no external standard defines it. |

**Alignment legend:** `exact` = same definition as the standard · `partial` = anchored to a real
standard with a documented difference · `none` = no governing standard (a named discipline convention
or the framework's own construct; the `standard` field says which).

_Sources: ISO 10002:2018 (complaints handling); ISO 30414:2018 (human capital reporting); IFRS 15
(revenue base); ISO 9001:2015 continual improvement as conceptual backdrop for the action-governance
layer. NPS cited as a proprietary Bain & Company methodology; CLV/RFM/retention cited as marketing-
analytics conventions rather than standards._
