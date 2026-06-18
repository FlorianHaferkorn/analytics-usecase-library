---
id: COM-IND-R001
factsheet_type: business
---

# COM-IND-R001 - Basket & Category Cross-Sell

## Business Factsheet

> **Tier:** Industry-variant (Retail) use case — see [ADR-0004](../../../../../docs/architecture/adr/0004-industry-variant-use-case-tier-taxonomy.md) for the `XXX-IND-<S>NNN` taxonomy and folder convention. It references governed KPIs, action codes, and the decision spine exactly like a core use case.

---

## 0. Metadata (Mandatory)

- **Use Case ID:** COM-IND-R001
- **Domain:** Commercial / Retail
- **Business Owner:** Head of Category Management / Trade Marketing Lead
- **KPI Owner:** Category Manager
- **Decision Owner:** Commercial Director + Head of Category Management
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** core/data_contracts/domains/commercial_sales.yaml
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Aurora: showcases/aurora_group/semantic_models/Commercial.SemanticModel (domain model for COM-*).

---

## 1. Business Summary

**Purpose:** Grow average basket value and category cross-sell by acting on category-affinity signals, promotion attachment, and store-level placement performance — maximising revenue per visit without increasing traffic.
**Business Value:** Higher revenue per transaction and broader baskets through margin-accretive attachment; better return on promotion spend; a repeatable placement-and-mechanics playbook by store format.
**Out of Scope:** Promotion ROI deep dives (COM-004); customer lifetime value and churn (COM-003); assortment/range-review decisions (separate merchandising process).

---

## 2. Core Business Questions

- Which category pairs have untapped cross-sell potential, and where is cross-sell rate declining?
- Is basket breadth (items per transaction) growing or eroding by store format and channel?
- Are promotions pulling margin-accretive attachment, or only standalone deal-seeking?
- Which frequent-visit customer cohorts respond best to cross-sell prompts?
- Should we act via placement, promotion mechanics, or digital recommendation?

---

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| retail.category.crosssell_rate.pct | Strategic |
| retail.basket.items_per_transaction | Influencing |
| retail.basket.value.average | Influencing |
| retail.promotion.attachment_rate.pct | Influencing |
| customer.rfm.frequency_score | Influencing |

**Action Codes:** C-M3.1

**Cross-Sell Rate Definition:** `retail.category.crosssell_rate.pct` is the share of transactions that contain items from two or more distinct product categories. It is the use case's north-star measure of basket breadth: it isolates genuine category cross-sell from single-category baskets, and is read alongside `retail.basket.value.average` so that breadth is never grown at the expense of basket economics.

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

## 4. Action Codes (Summary)

**C-M3.1 — Category Cross-Sell & Basket Optimization**
Fires when the category cross-sell rate falls persistently below target for two or more consecutive months while basket volume remains sufficient, signalling that high-affinity category pairs are underactivated. Owned by the Category Manager. Identifies the top high-affinity underperforming category pairs, ranks them by incremental basket-value potential, executes a placement directive or attachment promotion, and reviews cross-sell rate and average basket value monthly. Expected to improve cross-sell rate by 2–8 pp within 1–3 months. Inherits the `DEC-SPINE-COM-BASKET_CROSSSELL` decision spine. Not triggered while the affected assortment is in range review, in small-format stores where adjacent placement is impossible, or where an active campaign in the category pair must be measured first.

> Full machine-readable trigger conditions, thresholds, and routing in `UseCase_Bracket.yaml` (SSOT).

---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Category Cross-Sell Rate %
- Average Basket Value
- Items per Transaction
- Promotion Attachment Rate %
- RFM Frequency Score

_Filter Interaction: Product Category slicer cascades to all cross-sell and attachment visuals. Store Format slicer is independent and applies to the 30-second basket-economics chart only._

### 5.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| Average Basket Value Trend | Line | dim_date[Month] | [Average Basket Value] | Store Format | L12M | Basket economics guardrail |
| Cross-Sell vs Attachment | Column | dim_product[Category] | [Category Cross-Sell Rate %], [Promotion Attachment Rate %] | Channel | Current quarter | Identify weak activation |
| Items per Transaction by Category | Bar | dim_product[Category] | [Items per Transaction] | Store Format | Current quarter | Basket breadth detail |

### 5.3 Required Slicers (Mandatory)

- Date (Month/Quarter)
- Region / Channel
- Product Category
- Store Format

### 5.4 300-Second Layer (Diagnostics)

- Top-N high-affinity category pairs by untapped cross-sell potential and declining cross-sell rate over the last 3 periods.
- Promotion attachment matrix by category pair, channel, and store format, separating margin-accretive attachment from standalone deal-seeking.
- Basket-economics guardrail view confirming that cross-sell growth is not eroding average basket value or margin.
- Frequent-visit cohort view (RFM frequency) showing which segments respond to cross-sell prompts, to target placement and mechanics where repeat behaviour exists.

---

## 6. Data Requirements Summary

- Required facts: fact_sales for transaction-line detail (category, promotion, customer keys) and basket aggregation.
- Required dimensions: dim_date, dim_org, dim_product, dim_store, dim_customer, and security_user_org.
- Required grain: invoice_line (fact_sales) for governed transaction-line detail, aggregated to category pair and store format for cross-sell and attachment prioritisation.
- Required time range: 52+ weeks history so category-affinity scoring is stable across seasonality.
- Required slicers: Date, Region/Channel, Product Category, Store Format.
- **Data latency SLA:** Transaction and basket data refreshed daily within 1 business day; category-affinity scores recomputed weekly; any basket data >3 business days stale triggers a data quality alert before the monthly category review.

### Evidence grain

Evidence is governed at invoice_line grain (fact_sales, commercial_sales.yaml). Basket, cross-sell, and attachment metrics are computed from transaction-line detail and aggregated by category pair and store format for the action matrix.

---

## 7. Dependencies, Assumptions & Constraints

- Category-affinity (association) model is current; affinity scores are stale during major range changes and must not drive placement until retraining completes.
- Store-format taxonomy stable so adjacency feasibility is correctly applied.
- Promotion participation logs are joinable to transaction lines for attachment measurement.
- OneLake canonical dims (dim_date, dim_org, dim_product, dim_store, security_user_org) used.

### 7.4 Data Protection & Privacy (DSGVO / GDPR)

This use case operates on aggregated transaction and category data and is designed to avoid individual-level personal data in the analytical layer.

**Legal basis:** Reporting at category-pair, store-format, and segment grain does not process individual customer records, so no Art. 6 legal basis for personal-data processing is required for the dashboard itself. The RFM frequency score enters only as a segment-level average derived in the upstream customer model. Legal basis review is required if individual-customer targeting enters scope.

**Data minimisation:** Only category, basket, promotion, and store attributes required for cross-sell analysis are retained in the analytical layer. No name, address, or contact fields are included. The customer key behind the RFM aggregate is a pseudonymous internal ID held in the upstream customer model, not exposed here.

**Retention:** Aggregated basket and cross-sell data follow the applicable retention schedule in the data contract. Purge processes are automated and documented in the data retention register.

**Data subject rights:** Because no individual customer records are surfaced, erasure (Art. 17) and access (Art. 15) requests are fulfilled in the upstream customer model; this use case inherits those removals through the segment aggregate.

**Access restriction:** Basket and cross-sell views are classified Internal. Access is restricted to Category Management and Trade Marketing roles and enforced via Row-Level Security in the semantic model. Bulk export is blocked at report level.

**DSGVO owner:** Data Protection Officer. Review cycle: annual review; interim review required if processing scope changes (e.g. individual-customer targeting).

---

## 8. Success Criteria

- **Impact:** Category cross-sell rate up ≥3 pp in targeted category pairs within two quarters, with average basket value stable or growing in the same scope.
- **Adoption:** Dashboard used in the monthly Category Review (Category Manager + Trade Marketing); ≥80% of L2/L3 cross-sell flags result in a documented C-M3.1 placement or attachment action within 10 business days.
- **Quality:** Cross-sell rate reconciles within ±2% of POS transaction counts monthly; attachment measurement validated against promotion participation logs quarterly.
- **Decision Frequency:** Monthly (Category Review); quarterly affinity-model recalibration; Action Code closures tracked by Category Management within 45 days.

---

## 9. Risks & Wrong Interpretations (Short)

- **Risk:** Cross-sell rate rises while average basket value falls — breadth is being bought with low-value attachment.
  **Owner:** Category Manager.
  **Detection:** Cross-sell rate up >3 pp in same period as average basket value down >2%.
  **Mitigation:** Read cross-sell rate only alongside the basket-value guardrail; block placement actions that degrade basket economics.
  **Escalation:** If divergence persists 2 months, Commercial Director reviews mechanics with Trade Marketing.

- **Risk:** Affinity scores are stale after a range review, so placement directives target obsolete category pairs.
  **Owner:** Trade Marketing BI Lead.
  **Detection:** SKU change >15% in a category without a corresponding affinity-model retrain.
  **Mitigation:** Gate C-M3.1 on affinity-model freshness; suppress placement actions during range review.
  **Escalation:** If a stale-affinity directive is issued, the BI Lead freezes the category's affinity scores until retraining completes.

- **Risk:** Online basket affinity is applied to physical stores where adjacency is impossible.
  **Owner:** Category Manager.
  **Detection:** Placement directive issued for a small-format store (<500m² sales floor).
  **Mitigation:** Channel-split affinity; exclude small-format stores from placement-based actions.
  **Escalation:** If small-format placement directives recur, escalate to Head of Merchandising for format-specific mechanics.

---

## 10. Typical Decision Scenarios

These scenarios illustrate how this use case drives decisions in practice. They are examples — not exhaustive.

### Scenario A: Declining Cross-Sell in a High-Affinity Pair

**Situation:** Cross-sell rate between two complementary categories has fallen from 24% to 19% over three months in core stores. Average basket value is flat; the affinity model is current.

**Decision question:** Should we act via adjacent placement, promotion mechanics, or digital recommendation?

**Who decides:** Category Manager + Trade Marketing.

**Consequence of inaction:** Sustained leakage of revenue per visit in the highest-affinity pair; basket breadth erodes as habit weakens.

**Action Code triggered:** C-M3.1 (Category Cross-Sell & Basket Optimization) — L2 RequiredIntervention issues a placement directive for the top-3 high-affinity underperforming pairs with a planogram update inside 10 business days.

### Scenario B: Attachment Rate Flat Despite Heavy Promotion

**Situation:** A promoted category shows strong unit uplift, but promotion attachment rate is flat — shoppers buy the deal item and leave. Margin is being given away without basket breadth.

**Decision question:** Is the promotion pulling margin-accretive attachment, or only standalone deal-seeking?

**Who decides:** Trade Marketing + Category Manager.

**Consequence of inaction:** Continued margin give-away with no cross-sell return; promotion ROI overstated if read without attachment.

**Action Code triggered:** C-M3.1 (PrescriptiveExecution) — full promotional-mechanics review co-owned with Marketing; A/B test required before full rollout.

### Scenario C: Strong Affinity Signal in a Small-Format Estate

**Situation:** The affinity model flags a high-potential category pair, but the affected stores are small-format (<500m² sales floor) where the two categories cannot be placed adjacently.

**Decision question:** Should C-M3.1 fire a placement directive, or is a different mechanic required?

**Who decides:** Category Manager + Head of Merchandising.

**When NOT to act:** If the store format physically prevents adjacent placement, the placement-based action is not applicable and must not fire — per the `DEC-SPINE-COM-BASKET_CROSSSELL` spine, small-format constraint is an explicit do-not-act condition. Likewise, if the category is in active range review, affinity scores are stale and no placement directive should be issued until retraining completes. Verify store-format feasibility and affinity-model freshness before launching any intervention.

**Action Code triggered:** None for placement in small-format stores. Route instead to a digital-recommendation or checkout-prompt mechanic, or defer until range review and affinity retraining complete.

---
