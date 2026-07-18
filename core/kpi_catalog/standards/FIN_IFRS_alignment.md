# Finance KPIs — IFRS / APM alignment & definition-drift audit

> **Standards:** [IFRS / IAS](https://www.ifrs.org/issued-standards/list-of-standards/) (IFRS
> Foundation) for statement line items; the [ESMA Guidelines on Alternative Performance
> Measures](https://www.esma.europa.eu/document/esma-guidelines-alternative-performance-measures-apms)
> for non-GAAP measures (EBITDA, margin ratios); and [SCOR-DS AM.1.1 Cash-to-Cash](https://scor.ascm.org/performance/asset-management)
> for working-capital days (cross-domain with supply chain). **Method:** each governed Finance KPI
> is mapped to its nearest standard, with an explicit `alignment` (exact / partial / none) and a
> drift note — recorded per-KPI in `standard_ref` (schema
> `tooling/generator/schemas/kpi_definition.schema.json`). Second run of the per-domain program
> after [SCM ↔ SCOR](SCM_SCOR_alignment.md).

## Why not FIBO?

The obvious "finance ontology" candidate — **FIBO** (Financial Industry Business Ontology, EDM
Council) — is deliberately **out of scope** here. FIBO models *financial instruments, contracts,
legal entities, and market data* (what a bond, loan, or counterparty **is**); it does not define
*management P&L / working-capital KPIs* (what EBITDA margin or DSO **mean** as performance
measures). For this KPI set the correct authorities are **IFRS/IAS** (statement figures), the
**ESMA APM Guidelines** (non-GAAP measures), and **SCOR** (cash-cycle days). This is the same
"one standard per concept, not one standard for everything" principle the SCM audit surfaced with
the forecast metrics → IBF/APICS. FIBO stays relevant for a *future* instrument/entity-reference
domain, not for management KPIs.

## Headline findings

1. **EBITDA is not an IFRS metric — it is an APM/MPM.** `margin.ebitda.pct` must be labelled a
   non-GAAP Alternative Performance Measure and, per the **ESMA APM Guidelines**, reconciled to the
   nearest IFRS line item with a comparative. Under **IFRS 18** (effective **1 Jan 2027**, replacing
   IAS 1) an EBITDA-type figure used in public communication becomes a **Management-defined
   Performance Measure (MPM)** requiring a dedicated reconciliation note; IFRS 18's closest *defined*
   analogue is **OPDAI** (operating profit before depreciation, amortisation and impairments). This
   is the single most important governance flag in the Finance domain.
2. **IFRS 18 is coming (2027) and it touches our margin/variance stack.** It defines operating
   subtotals and mandates MPM reconciliation. Our margin ratios and vs-plan variances are exactly the
   management measures IFRS 18 governs — treat this audit as the pre-work for IFRS 18 MPM disclosure.
3. **Gross profit is partly IFRS, the gross-margin *ratio* is an APM.** `margin.gm.amount` aligns to
   the IAS 1 gross-profit subtotal (when Net Sales = IFRS 15 revenue, COGS = IAS 2 cost of sales);
   `margin.gm.pct` / `margin.cogs.pct` are APM ratios of IFRS-clean inputs — label them as APMs.
4. **Working-capital days are NOT IFRS line items — they are SCOR Cash-to-Cash (AM.1.1).** DSO / DPO /
   DIO / CCC map cross-domain to SCOR Asset-Management, consistent with `wc.dio.days` from the SCM
   run. This is where finance and supply-chain standards meet — reuse SCOR, don't invent a parallel
   finance definition.
5. **Duplicate CCC surfaced by the mapping.** `wc.ccc.days` (fact-based) and
   `ops.working_capital.ccc.days` (fixed-ratio proxy) are the same Cash-to-Cash concept —
   consolidation candidate, mirroring the DIO/OTIF duplicates the SCM audit found.

## Mapping table

| KPI | Standard | Alignment | Drift note / recommendation |
|---|---|---|---|
| `cost.cogs.amount` | `IFRS IAS 2` Inventories — cost of sales | **exact** | COGS is the IAS 2 carrying amount of inventories recognised as an expense when the related revenue is recognised (IAS 2.34), presented as 'cost of sales' under the IAS 1 function-of-expense method. Definition aligns. |
| `fin.cash.balance` | `IFRS IAS 7` Cash and cash equivalents | **exact** | Cash and cash equivalents is defined by IAS 7.6–9 (short-term, highly liquid, insignificant risk of value change, typically ≤3-month maturity). Ensure scope matches the IAS 7 definition, not a broader treasury balance. |
| `fin.cash.ocf` | `IFRS IAS 7` Cash flows from operating activities | **exact** | Maps to the IAS 7 operating-activities cash-flow section. Aligns; IAS 7 permits the direct or indirect method — pin which one is used so period-over-period comparisons are stable. |
| `fin.liquidity.inventory.amount` | `IFRS IAS 2` Inventories carrying amount | **exact** | Closing inventory measured at the lower of cost and net realisable value (IAS 2). Our note allows 'standard or average cost' — IAS 2 prohibits LIFO; confirm the cost formula is FIFO or weighted-average and standard cost approximates actual. |
| `wc.ccc.days` | `SCOR-DS AM.1.1` Cash-to-Cash Cycle Time | **exact** | CCC (DSO + DIO − DPO) is definitionally SCOR AM.1.1 Cash-to-Cash Cycle Time — a cross-domain finance↔supply-chain metric with no single IFRS equivalent. Duplicate concept of ops.working_capital.ccc.days (proxy variant) — consolidate toward this fact-based version. |
| `cost.opex.base.amount` | `IFRS IAS 1` Operating expenses | **partial** | Operating expenses map to IAS 1 expense presentation (by nature or by function). The 'base' scoping is an internal reporting choice, not an IFRS concept — align the expense population to the IAS 1 classification actually reported. |
| `fin.liquidity.payables.amount` | `IFRS IAS 1` Trade and other payables | **partial** | Trade payables are an IAS 1 statement-of-financial-position line (a financial liability under IFRS 9). Aligns for trade payables; ensure non-trade accruals/provisions are excluded when this feeds DPO. |
| `fin.overdue_ar.pct` | `IFRS IFRS 9` Trade receivables — credit-risk ageing | **partial** | Overdue-AR ageing underpins the IFRS 9 expected-credit-loss simplified (provision-matrix) approach, but the overdue-% itself is a credit-management KPI, not an IFRS-defined figure. Receivables base per IFRS 9 / IAS 1. |
| `margin.cogs.pct` | `ESMA-APM` Cost-of-sales ratio (APM) | **partial** | Inverse of the gross-margin ratio; same APM treatment. Inputs are IFRS (IAS 2 cost of sales / IFRS 15 revenue). |
| `margin.gm.amount` | `IFRS IAS 1` Gross profit subtotal | **partial** | Gross profit (Revenue − Cost of sales) is an illustrative IAS 1 by-function subtotal, not a mandated line item. Aligns when Net Sales = IFRS 15 revenue and COGS = IAS 2 cost of sales. IFRS 18 (eff. 1 Jan 2027) formalises defined operating subtotals. |
| `margin.gm.pct` | `ESMA-APM` Gross margin ratio (APM) | **partial** | A ratio of two IFRS figures (IFRS 15 revenue, IAS 2 cost of sales); the percentage itself is a non-GAAP APM. Inputs are IFRS-clean — label the ratio as an APM in external reporting. |
| `ops.working_capital.ccc.days` | `SCOR-DS AM.1.1` Cash-to-Cash Cycle Time (proxy) | **partial** | Same CCC concept as SCOR AM.1.1 but computed from fixed-ratio Net Sales/COGS proxies (Experience-domain executive view where the receivables/inventory/payables facts are unavailable). Consolidate toward wc.ccc.days where those facts exist. |
| `wc.dpo.days` | `SCOR-DS AM.1.1` Cash-to-Cash Cycle Time — DPO component | **partial** | Days Payables Outstanding is the payables-days input of SCOR Cash-to-Cash Cycle Time (AM.1.1). Not an IFRS line item; the payables base is IAS 1 / IFRS 9. |
| `wc.dso.days` | `SCOR-DS AM.1.1` Cash-to-Cash Cycle Time — DSO component | **partial** | Days Sales Outstanding is the receivables-days input of SCOR Cash-to-Cash Cycle Time (AM.1.1 = DSO + Inventory Days − DPO). Not an IFRS line item; the receivables base is IFRS 9 / IAS 1. |
| `cost.base_volume.amount` | `IFRS IAS 2` Cost-base baseline (variance analysis) | **none** | Internal variance-analysis baseline; no external standard. Underlying cost is IAS 2 inventory cost. |
| `cost.cogs_per_unit.amount` | `IFRS IAS 2` Unit COGS (cost accounting) | **none** | Internal cost-accounting metric; the COGS input is IAS 2 cost of sales but per-unit COGS is not an IFRS-defined figure. |
| `cost.material.pct` | `IFRS IAS 2` Material-cost ratio | **none** | Management cost-structure ratio (material cost share of sales); not an IFRS-defined figure. Material cost is an IAS 2 inventory cost input. |
| `cost.opex.vs_plan.pct` | `IFRS IAS 1` Operating-expense budget variance | **none** | Internal budget-variance management metric; no external financial-reporting standard defines it. Actual and plan inputs trace to IAS 1 operating expenses. |
| `cost.unit.amount` | `IFRS IAS 2` Unit cost (cost accounting) | **none** | Internal cost-accounting metric (total cost / units); no external financial-reporting standard. Cost inputs relate to IAS 2 inventory costing. |
| `fin.cash.vs_plan.pct` | `IFRS IAS 7` Cash budget variance | **none** | Internal budget-variance metric; no external standard defines it. Cash input traces to IAS 7 cash and cash equivalents. |
| `margin.ebitda.pct` | `ESMA-APM` EBITDA margin — Alternative Performance Measure | **none** | EBITDA is NOT defined by IFRS. It is an Alternative Performance Measure: under the ESMA APM Guidelines it must be labelled as non-GAAP, reconciled to the most directly reconcilable IFRS line item, and shown with a comparative. Under IFRS 18 (eff. 1 Jan 2027) an EBITDA-type figure used in public communication is a Management-defined Performance Measure (MPM) requiring a dedicated reconciliation note to the nearest IFRS subtotal — IFRS 18's closest defined analogue is OPDAI ('operating profit before depreciation, amortisation and impairments'). Do not present as an IFRS metric. |
| `margin.gm.vs_plan.pct` | `IFRS IAS 1` Gross-margin budget variance | **none** | Internal budget-variance metric; no external standard. Inputs trace to IAS 1 gross profit / IFRS 15 revenue. |
| `margin.promo.gm.pct` | `ESMA-APM` Promo gross-margin ratio | **none** | Internal commercial / trade-promotion metric (incremental GM during promo); not an IFRS or ESMA-named measure. Treated as an internal analytic ratio. |

**Alignment legend:** `exact` = same definition as the standard line item · `partial` = same concept
with a documented definitional difference (grain, reference date, GAAP vs non-GAAP) · `none` = no
external-standard equivalent (internal management/variance metric; note points to the nearest
standard input).

_Sources: IFRS Foundation issued standards (ifrs.org — IAS 1, IAS 2, IAS 7, IFRS 9, IFRS 15,
IFRS 18); ESMA Guidelines on Alternative Performance Measures (ESMA/2015/1415); ESMA public
statement on IFRS 18 implementation (2026); SCOR Digital Standard, ASCM (scor.ascm.org).
IFRS 18 effective for annual periods beginning on or after 1 January 2027._
