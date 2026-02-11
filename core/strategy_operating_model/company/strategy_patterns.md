# Strategy Patterns

## 1. Purpose

Strategy patterns are **reusable, predefined steering configurations** that translate high-level intent ("we want to be more profitable", "we need to protect cash") into a small set of Strategic KPIs, trade-offs, and priority use-case clusters.

Companies can adopt one pattern, blend several, or use them as a starting point to define their own strategy. The framework supplies structure and KPI/use-case mapping; strategy patterns reduce blank-page syndrome and align analytics to strategy from day one.

**Relationship:** Strategy patterns feed into the Golden Thread. They do not replace `company_strategy.md`; they extend it with concrete, repeatable options.

---

## 2. How to Use Strategy Patterns

1. **Choose or blend** — Select the pattern(s) that best match current strategic priorities.
2. **Anchor KPIs** — The pattern lists Strategic KPIs that must be in the KPI Catalog and semantic model.
3. **Prioritize use cases** — Use the linked use-case clusters to scope implementation order (e.g. Phase 1: margin + cash; Phase 2: growth).
4. **Adapt if needed** — Add or remove KPIs/use cases for company-specific context; keep ownership and definitions governed.

---

## 3. Pattern: Margin-First

**Intent:** Protect and improve profitability. Margin quality and cost control take precedence over top-line growth.

**Strategic KPIs (priority order):**

1. margin.gm.pct, margin.gm.vs_plan.pct  
2. sales.price.realization_pct  
3. cost.unit.amount, margin.cogs.pct, cost.opex.vs_plan.pct  
4. sales.pvm.mix_effect.amount, cost.cogs_per_unit.amount  

**Trade-offs:**

- Revenue growth is acceptable only if margin is maintained or improved.
- Discount and price exceptions are governed; realization is monitored.

**Use-case clusters (priority):**

| Priority | Use Cases | Rationale |
|----------|-----------|-----------|
| 1 | COM-002 Margin & Price Performance, FIN-002 Cost Performance | Direct margin and cost levers |
| 2 | COM-001 Sales Performance, COM-004 Promotion Effectiveness | Revenue visibility with margin guardrails |
| 3 | OPS-003 Quality & Yield, SCM-001 Inventory Performance | Cost of quality and working capital |
| 4 | XD-003 Executive KPI Overview | Unified view including margin |

**Key questions (examples):** Why is margin deteriorating despite stable revenue? Which cost components or price/mix effects drive the gap? Which actions move GM fastest with lowest risk?

---

## 4. Pattern: Cash-First

**Intent:** Secure liquidity and working capital. Cash conversion and balance sheet efficiency override short-term revenue or margin maximization where they conflict.

**Strategic KPIs (priority order):**

1. fin.cash.balance, fin.cash.ocf, fin.cash.vs_plan.pct  
2. wc.ccc.days, wc.dso.days, wc.dio.days, wc.dpo.days  
3. inv.dio.days, inv.turnover, inv.stockout.pct  
4. margin.gm.pct (guardrail: do not sacrifice margin for volume that hurts cash)  

**Trade-offs:**

- Inventory and receivables are optimized for cash conversion; service level is a guardrail, not the sole objective.
- Payment terms and working capital levers are explicitly steered.

**Use-case clusters (priority):**

| Priority | Use Cases | Rationale |
|----------|-----------|-----------|
| 1 | FIN-001 Cash & Liquidity Performance, SCM-001 Inventory Performance | Cash, CCC, and inventory levers |
| 2 | SCM-002 Supply Reliability & OTIF, SCM-003 Forecast vs Actual | Service and planning impact on cash |
| 3 | COM-001 Sales Performance, COM-002 Margin & Price Performance | Revenue and margin as context for cash |
| 4 | XD-003 Executive KPI Overview | Unified view including cash and CCC |

**Key questions (examples):** What is cash position vs plan and how is OCF trending? Which customers/suppliers or inventory positions drive cash conversion issues? What actions improve cash quickly with minimal business risk?

---

## 5. Pattern: Growth-First

**Intent:** Prioritize revenue growth and market position. Top-line and customer value take precedence, with margin and cash as guardrails.

**Strategic KPIs (priority order):**

1. sales.net_sales.amount, sales.net_sales.delta_pct.plan, sales.net_sales.delta_pct.ly  
2. crm.clv.amount, crm.retention.pct, crm.churned_customers.count, crm.revenue_at_risk.amount  
3. margin.gm.pct (guardrail), sales.pvm.price_effect.amount, sales.pvm.volume_effect.amount, sales.pvm.mix_effect.amount  
4. sales.promo.roi.pct, sales.promo.incremental.amount (if promotion-heavy)  

**Trade-offs:**

- Margin and cash are monitored; growth actions must not breach agreed guardrails.
- Customer retention and CLV are steered explicitly.

**Use-case clusters (priority):**

| Priority | Use Cases | Rationale |
|----------|-----------|-----------|
| 1 | COM-001 Sales Performance, COM-003 Customer Value | Revenue and customer levers |
| 2 | COM-002 Margin & Price Performance, COM-004 Promotion Effectiveness | Margin guardrails and promo ROI |
| 3 | FIN-001 Cash & Liquidity Performance | Cash as guardrail |
| 4 | XD-003 Executive KPI Overview | Unified view including growth and CLV |

**Key questions (examples):** Where do Net Sales deviate vs Plan and vs LY? Which segments drive CLV and where is churn rising? Which actions close revenue gaps and improve CLV without breaching margin/cash guardrails?

---

## 6. Blending Patterns

Companies often combine patterns (e.g. "Margin-first with strong cash discipline"). When blending:

- **Primary pattern** defines the top 2–3 Strategic KPIs and the first wave of use cases.
- **Secondary pattern** adds the next KPI tier and use-case cluster; guardrails from both patterns apply.
- **Executive view (XD-003)** always includes KPIs from all active patterns so leadership sees trade-offs in one place.

---

## 7. Relationship to Other Artifacts

- **Company strategy:** `company_strategy.md` — defines focus areas and principles; strategy patterns are one way to instantiate them.
- **KPI Catalog:** All Strategic KPIs listed in patterns must exist in `framework/kpi_catalog/`.
- **Use Case Inventory:** `framework/usecases/UseCase_Inventory.md` — use-case IDs and Key Questions align with the clusters above.
- **Golden Thread:** `operating_model/golden_thread_strategy_to_action.md` — strategy patterns feed Step 1 (Business Strategy) and Step 2 (Strategic KPIs → Key Questions).
