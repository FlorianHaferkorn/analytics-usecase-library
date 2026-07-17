# People & Culture KPIs — ISO 30414 alignment & drift audit

> **Standards:** ISO 30414:2018 (Human Capital Reporting) for turnover/retention; digital adoption is change-management, not an HR standard. **Method:** each governed KPI is mapped with an explicit `alignment`
> (exact / partial / none) + drift note in `standard_ref`, naming the discipline where there is no
> governing standard. Part of the per-domain standards program (SCM→SCOR, Finance→IFRS,
> Operations→ISO 22400, Service→ITIL/ISO 20000, Commercial→IFRS 15/convention).

## Read

ISO 30414:2018 is the genuine standard for human-capital metrics (turnover, retention, workforce cost/skills/availability). `people.attrition_risk.pct` maps to its turnover/retention family as a **predictive overlay** — align the realised-turnover base to ISO 30414. `people.digital_adoption.pct` is a digital-transformation metric outside ISO 30414's scope (marked none with the pointer).

## Mapping table

| KPI | Standard / discipline | Alignment | Drift note / recommendation |
|---|---|---|---|
| `people.attrition_risk.pct` | `ISO 30414` Human capital — turnover / retention | **partial** | ISO 30414:2018 (human capital reporting) defines turnover and retention-rate metrics. Attrition RISK here is a predicted probability — a modelling variant of the ISO turnover family; align the realised-turnover base to ISO 30414 and treat the risk score as a forward-looking overlay. |
| `people.digital_adoption.pct` | `ISO 30414` (digital adoption — change management) | **none** | Digital adoption (digital / total transactions for eligible processes) is a digital-transformation / change-management metric, not part of ISO 30414's human-capital areas. No governing HR standard; loosely relates to ISO 30414 workforce skills & capabilities. |

**Alignment legend:** `exact` = same definition as the standard · `partial` = anchored to a real
standard with a documented difference · `none` = no governing standard (a named discipline convention
or the framework's own construct; the `standard` field says which).

_Sources: ISO 10002:2018 (complaints handling); ISO 30414:2018 (human capital reporting); IFRS 15
(revenue base); ISO 9001:2015 continual improvement as conceptual backdrop for the action-governance
layer. NPS cited as a proprietary Bain & Company methodology; CLV/RFM/retention cited as marketing-
analytics conventions rather than standards._
