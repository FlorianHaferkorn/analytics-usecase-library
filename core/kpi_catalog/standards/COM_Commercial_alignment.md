# Commercial / Sales KPIs — standards alignment & drift audit

> **Standards:** [IFRS 15](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/)
> (Revenue from Contracts with Customers) for the revenue *amounts*; **managerial-accounting variance
> convention** (CIMA Official Terminology / IMA Statements on Management Accounting) for the PVM
> decomposition; and named **discipline conventions** (trade-promotion management, retail analytics,
> RFM marketing) for everything else. **Method:** each governed Commercial KPI is mapped with an
> explicit `alignment` (exact / partial / none) + drift note in `standard_ref`. Fifth run of the
> per-domain program after SCM→SCOR, [Finance→IFRS](FIN_IFRS_alignment.md),
> [Operations→ISO 22400](OPS_ISO22400_alignment.md), [Service→ITIL/ISO 20000](SVC_ITIL_ISO20000_alignment.md).

## The distinctive finding: this is where external standards run out

Unlike supply chain (SCOR), finance (IFRS), operations (ISO 22400) or service (ISO 20000),
**Commercial has no single governing standard**. That is the finding, not a gap in the audit. The
domain decomposes into three governance tiers, and the `standard` field names the tier for every KPI
so the boundary is explicit:

1. **IFRS 15 governs the revenue amount.** Net sales, net/transaction price — these are real
   financial-reporting figures. IFRS 15 correctly excludes VAT (third-party collection) and treats
   returns/rebates as variable consideration; align to that and the amounts are audit-grade.
2. **Managerial-accounting convention governs PVM.** Price/volume/mix variance is a well-established
   *convention* (CIMA/IMA), taught and applied consistently — but it is not an ISO/IFRS standard, and
   it has real definitional variants (per-row vs blended volume basis) that change the mix residual.
   Label it as management-accounting variance analysis and pin the basis.
3. **Discipline convention governs the rest.** Trade-promotion (baseline/uplift/ROI/cannibalization),
   retail basket (ATV/UPT/cross-sell/attach), and RFM segmentation are standard *practice* with no
   governing body. Mark them convention, not standard — over-claiming a standard here would be
   dishonest with a client.

This is the same "one standard per concept, and name where there is none" discipline the earlier runs
applied (SCM forecast → IBF/APICS; Service NPS → proprietary Bain).

## Headline findings

1. **Only the revenue amounts are standard-anchored.** `KPI-COM-005` /
   `KPI-COM-002` map to IFRS 15 (partial); everything downstream (growth %, realization,
   variances) is convention built on that base.
2. **PVM has a genuine definitional fork.** The volume-effect basis (per-row Δqty × plan price vs
   blended plan price) determines whether mix is material — a convention choice that must be pinned so
   price + volume + mix reconcile to total variance. (This is the same decomposition the COM-001
   waterfall depends on.)
3. **Trade-promotion spend may be a revenue deduction under IFRS 15.** Several `sales.promo.cost`-type
   figures are conventionally treated as expense, but IFRS 15 may require certain trade spend to reduce
   revenue — a classification check with real reporting impact.
4. **Everything else is convention — and that's fine, if labelled.** The value of this run is the
   honest tiering: audit-grade IFRS 15 amounts, recognised managerial convention for PVM, and clearly
   labelled practice conventions for promo/retail/RFM.

## Mapping table

| KPI | Standard / discipline | Alignment | Drift note / recommendation |
|---|---|---|---|
| `KPI-COM-005` | `IFRS 15` Revenue from contracts with customers | **partial** | Net sales is a presentation of IFRS 15 revenue: net of VAT (correctly excluded — amounts collected on behalf of third parties are not revenue) and net of returns (IFRS 15 variable consideration — recognise a refund liability, not revenue). Aligns when returns/rebates are treated as IFRS 15 variable consideration. |
| `KPI-COM-002` | `IFRS 15` Transaction price (net of discounts) | **partial** | Net price is the IFRS 15 transaction price after trade discounts and variable consideration. Aligns conceptually; ensure discounts/rebates follow IFRS 15 variable-consideration measurement rather than ad-hoc netting. |
| `KPI-COM-004` | `Management accounting (CIMA/IMA)` Sales mix variance (residual) | **partial** | Mix effect is the residual (total − price − volume) in the standard three-way variance decomposition. Its magnitude depends on the volume-effect basis (see sales.pvm.volume_effect) — a convention choice, not a governed standard. |
| `KPI-COM-010` | `Management accounting (CIMA/IMA)` Sales price variance | **partial** | Price effect follows the managerial-accounting sales-price-variance convention (CIMA Official Terminology; IMA Statements on Management Accounting) — not a governed ISO/IFRS standard. Our formula (Δprice × actual quantity) is the standard convention; label it management-accounting variance analysis, not a financial-reporting standard. |
| `KPI-COM-011` | `Management accounting (CIMA/IMA)` Sales volume variance | **partial** | Volume effect follows the sales-volume-variance convention. NOTE a real definitional variant: per-row (Δqty × plan unit price) collapses mix to zero, whereas the blended-plan-price basis makes mix material — pin which convention is used so price+volume+mix reconcile to total variance. |
| `KPI-CUS-007` | `Marketing analytics — RFM (convention)` RFM frequency score | **none** | RFM (Recency-Frequency-Monetary) scoring is a long-standing direct-marketing segmentation model (Hughes/DMA lineage), a convention rather than a governed standard. |
| `KPI-SCM-013` | `Retail analytics (convention)` Order line count | **none** | Order-line count is an operational volume element, not a standard-defined KPI. |
| `KPI-COM-023` | `Retail analytics (convention)` Units per transaction (UPT) | **none** | Items per transaction (UPT) is a retail-analytics convention; no governing standard. |
| `KPI-COM-024` | `Retail analytics (convention)` Average transaction value | **none** | Average basket value (net sales / transactions) is a standard retail KPI but a market convention, not a governed standard. |
| `KPI-COM-022` | `Retail analytics (convention)` Cross-sell rate | **none** | Cross-sell rate (multi-category transactions / total) is a retail/CRM analytics convention, not standard-defined. |
| `KPI-COM-025` | `Retail analytics (convention)` Attachment rate | **none** | Promotion attachment rate is a retail merchandising-analytics convention; no external standard. |
| `KPI-COM-008` | `IFRS 15` Net sales YoY growth | **none** | Year-over-year growth is a management trend metric; the underlying net-sales base is IFRS 15 revenue but the growth ratio is not standard-defined. |
| `KPI-COM-009` | `IFRS 15` Net sales vs plan variance | **none** | Net-sales-vs-plan is an internal budget-variance metric; the actual base is IFRS 15 revenue, the variance is convention. |
| `KPI-COM-001` | `IFRS 15` List/catalogue price | **none** | List price is a pre-discount catalogue figure — an input to discount/realization analysis, not an IFRS 15 figure (IFRS 15 measures the transaction price actually expected). No standard defines list price. |
| `KPI-COM-003` | `IFRS 15` Price realization (net/list) | **none** | Price realization (net/list) is a management pricing metric, not IFRS-defined. The discount it captures is IFRS 15 variable consideration, but the ratio itself is a commercial-analytics convention. |
| `KPI-COM-020` | `Trade Promotion Management (convention)` Promo baseline sales | **none** | Baseline (non-promoted) sales is a trade-promotion-management analytics concept (uplift modelling), not defined by any external standard. |
| `KPI-COM-018` | `Trade Promotion Management (convention)` Promo cannibalization | **none** | Cannibalization (cannibalized / uplift sales) is a TPM analytics concept, not standard-defined. |
| `KPI-COM-017` | `Trade Promotion Management (convention)` Cannibalized sales (proxy) | **none** | Cannibalized sales is a TPM concept, here a documented 15%-of-baseline proxy pending non-promo-segment actuals — a convention, not a standard. |
| `KPI-COM-014` | `Trade Promotion Management (convention)` Trade-promotion spend | **none** | Promo cost / trade spend is a TPM concept, not an external-standard figure (though under IFRS 15 certain trade spend is a reduction of revenue rather than an expense — check classification). |
| `KPI-COM-021` | `Trade Promotion Management (convention)` Promo incremental/uplift sales | **none** | Incremental (promo − baseline) uplift is a TPM convention; no governing standard. |
| `KPI-COM-015` | `Trade Promotion Management (convention)` Promo incremental gross margin | **none** | Incremental promo GM is a TPM metric; the GM base ties to IFRS 15 revenue / IAS 2 COGS, but the incremental construct itself is convention, not a standard. |
| `KPI-COM-016` | `Trade Promotion Management (convention)` Promo ROI | **none** | Promo ROI (incremental GM / promo cost) is a TPM convention; no governing standard. |
| `KPI-COM-012` | `IFRS 15` Sales volume (units) | **none** | Sold units is a volume element underlying revenue; not an IFRS 15 figure itself (IFRS 15 measures the consideration, not the count). |

**Alignment legend:** `exact` = same definition as the standard · `partial` = anchored to a real
standard (IFRS 15) or an established convention (CIMA/IMA) with a documented difference · `none` = no
governing standard — a named discipline convention (the `standard` field says which).

_Sources: IFRS 15 (ifrs.org) — revenue recognition, transaction price, variable consideration, VAT
exclusion; CIMA Official Terminology and IMA Statements on Management Accounting for the price/volume/
mix variance convention; trade-promotion-management, retail-analytics and RFM (Recency-Frequency-
Monetary) practice for the convention-level metrics, cited as conventions rather than standards._
