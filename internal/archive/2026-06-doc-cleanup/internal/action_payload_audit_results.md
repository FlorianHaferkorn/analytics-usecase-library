# Action-Payload Audit: Step Text vs Evidence Grain

**Date:** 2026-02-14
**Scope:** All action codes subscribed by the 15 core use cases.
**Criteria:**
1. **Entity reference** — does the step text mention the entity implied by the subscribing bracket's `evidence_grain`?
2. **Verb voice** — is the step phrased in prescriptive (imperative, active) voice or descriptive (passive, distanced) voice?

**Convention:**
- Good (prescriptive): `CHECK this invoice line against the price floor.`
- Bad (descriptive): `The user should check the invoice line.`

---

## Legend

- **Entity ref**: YES = at least one step references the grain entity or synonym; NO = none do.
- **Voice**: P = prescriptive (imperative verb-first); D = descriptive (passive/third-person).
- **Verdict**: OK = both criteria met; REWRITE = needs rewording.

---

## COM-001 / COM-002 — Grain: `invoice_line`

| Action Code | Step 1 (verbatim) | Entity Ref | Voice | Verdict |
|-------------|-------------------|------------|-------|---------|
| C-M2.1 | Identify Region/Channel/SKU combinations below realization threshold | NO | P | REWRITE |
| C-S1.1 | Identify regions/channels breaching GM threshold | NO | P | REWRITE |
| C-S1.2 | Identify regions/channels breaching plan thresholds | NO | P | REWRITE |

**Assessment:** Steps use prescriptive voice (imperative verbs: Identify, Freeze, Enforce, Review) but never reference the evidence entity (invoice line). Steps operate at Region/Channel/SKU level — needs grain-level anchoring.

---

## COM-002 additional — Grain: `invoice_line`

| Action Code | Step 1 (verbatim) | Entity Ref | Voice | Verdict |
|-------------|-------------------|------------|-------|---------|
| C-M2.2 | Identify regions/channels with persistent negative mix effect | NO | P | REWRITE |
| C-P4.1 | Identify promotions with repeated negative ROI | NO (promotion, not invoice) | P | REWRITE |

---

## COM-003 — Grain: `customer_month`

| Action Code | Step 1 (verbatim) | Entity Ref | Voice | Verdict |
|-------------|-------------------|------------|-------|---------|
| C-M2.2 | Identify regions/channels with persistent negative mix effect | NO | P | REWRITE |
| C-P4.1 | Identify promotions with repeated negative ROI | NO | P | REWRITE |
| C-S1.2 | Identify regions/channels breaching plan thresholds | NO | P | REWRITE |

**Assessment:** No step references "customer" or "account". All steps are region/channel scoped.

---

## COM-004 — Grain: `promotion`

| Action Code | Step 1 (verbatim) | Entity Ref | Voice | Verdict |
|-------------|-------------------|------------|-------|---------|
| C-M2.1 | Identify Region/Channel/SKU combinations below realization threshold | NO | P | REWRITE |
| C-S1.1 | Identify regions/channels breaching GM threshold | NO | P | REWRITE |
| C-M2.2 | Identify regions/channels with persistent negative mix effect | NO | P | REWRITE |
| C-P4.1 | Identify promotions with repeated negative ROI | YES (promotion) | P | OK |
| C-S1.2 | Identify regions/channels breaching plan thresholds | NO | P | REWRITE |

**Assessment:** Only C-P4.1 references "promotion". Other actions are reused from COM-001/002 and lack entity anchoring for the promotion grain.

---

## FIN-001 — Grain: `entity_month`

| Action Code | Step 1 (verbatim) | Entity Ref | Voice | Verdict |
|-------------|-------------------|------------|-------|---------|
| F-C1.1 | Detect sustained deterioration in CCC or cash vs plan | NO | P | REWRITE |
| F-C1.2 | Identify customers driving DSO deterioration | NO (customer != entity) | P | REWRITE |
| F-C1.3 | Identify categories and warehouses driving DIO increase | NO | P | REWRITE |
| F-C1.4 | Identify suppliers driving early payment behaviour | NO | P | REWRITE |

**Assessment:** Steps refer to customers, categories, warehouses, suppliers — never to "entity" or "business unit" which is the grain.

---

## FIN-002 — Grain: `plant_line_product_month`

| Action Code | Step 1 (verbatim) | Entity Ref | Voice | Verdict |
|-------------|-------------------|------------|-------|---------|
| F-K2.1 | Detect sustained unit cost deterioration | NO | P | REWRITE |
| F-K2.2 | Identify plants/products with rising material cost share | YES (plant, product) | P | OK |
| F-K2.3 | Identify lines and shifts with productivity decline | YES (line) | P | OK |
| F-K2.4 | Identify cost centers exceeding OpEx plan | NO | P | REWRITE |

---

## OPS-001 — Grain: `line_day`

| Action Code | Step 1 (verbatim) | Entity Ref | Voice | Verdict |
|-------------|-------------------|------------|-------|---------|
| O-O1.1 | Identify top recurring downtime categories | NO | P | REWRITE |
| O-O1.2 | Identify lines with sustained performance loss | YES (line) | P | OK |
| O-O1.3 | Identify lines with sustained quality loss | YES (line) | P | OK |
| O-O1.4 | Identify plants missing throughput plan | NO (plant != line) | P | REWRITE |

---

## OPS-002 — Grain: `failure_event`

| Action Code | Step 1 (verbatim) | Entity Ref | Voice | Verdict |
|-------------|-------------------|------------|-------|---------|
| O-A2.1 | Detect sustained availability deterioration | NO | P | REWRITE |
| O-A2.2 | Identify assets with declining MTBF | YES (asset) | P | OK |
| O-A2.3 | Identify assets with prolonged repair times | YES (asset) | P | OK |
| O-A2.4 | Identify assets with declining PM compliance | YES (asset) | P | OK |
| O-A2.5 | Identify assets impacted by spare part stockouts | YES (asset) | P | OK |

---

## OPS-003 — Grain: `line_day`

| Action Code | Step 1 (verbatim) | Entity Ref | Voice | Verdict |
|-------------|-------------------|------------|-------|---------|
| O-Q3.1 | Detect sustained FPY deterioration | NO | P | REWRITE |
| O-Q3.2 | Identify top defect categories and process steps | NO | P | REWRITE |
| O-Q3.3 | Identify dominant scrap and rework drivers | NO | P | REWRITE |
| O-Q3.4 | Identify plants with rising COPQ | NO (plant != line) | P | REWRITE |
| O-Q3.5 | Identify products with rising complaint rates | NO (product != line) | P | REWRITE |

**Assessment:** No step references "line" or "production line" or "shift". Steps operate at defect/plant/product level.

---

## SCM-001 — Grain: `location_sku_month`

| Action Code | Step 1 (verbatim) | Entity Ref | Voice | Verdict |
|-------------|-------------------|------------|-------|---------|
| S-I1.1 | Detect sustained DIO deviation | NO | P | REWRITE |
| S-I1.2 | Identify SKUs with structurally high DIO | YES (SKU) | P | OK |
| S-I1.3 | Identify SKUs with rising stockout risk | YES (SKU) | P | OK |
| S-I1.4 | Identify obsolete and aging inventory beyond demand horizon | YES (inventory) | P | OK |
| S-I1.5 | Identify SKUs with persistent forecast instability | YES (SKU) | P | OK |

---

## SCM-002 — Grain: `shipment_line`

| Action Code | Step 1 (verbatim) | Entity Ref | Voice | Verdict |
|-------------|-------------------|------------|-------|---------|
| S-R2.1 | Detect sustained OTIF deterioration | NO | P | REWRITE |
| S-R2.2 | Identify lanes/DCs with recurring late deliveries | NO (lane/DC != shipment) | P | REWRITE |
| S-R2.3 | Identify SKUs/lanes with rising in-full failures | NO | P | REWRITE |
| S-R2.4 | Identify lanes with recurring penalties or expedites | NO | P | REWRITE |
| S-R2.5 | Identify cycles with repeated last-minute plan changes | NO | P | REWRITE |

**Assessment:** Steps reference lanes, DCs, SKUs — never "shipment" or "delivery" or "order".

---

## SCM-003 — Grain: `location_sku_month`

| Action Code | Step 1 (verbatim) | Entity Ref | Voice | Verdict |
|-------------|-------------------|------------|-------|---------|
| S-F3.1 | Detect sustained forecast accuracy deterioration | NO | P | REWRITE |
| S-F3.2 | Identify SKUs with persistent forecast bias | YES (SKU) | P | OK |
| S-F3.3 | Identify SKUs/locations with forecast-driven service loss | YES (SKU, location) | P | OK |
| S-F3.4 | Identify cycles with excessive replans | NO | P | REWRITE |

---

## XD-001 — Grain: `case`

| Action Code | Step 1 (verbatim) | Entity Ref | Voice | Verdict |
|-------------|-------------------|------------|-------|---------|
| X-S1.1 | Detect sustained SLA deterioration | NO | P | REWRITE |
| X-S1.2 | Identify queues with sustained backlog growth | NO (queue != case) | P | REWRITE |
| X-S1.3 | Identify queues/agent groups with low FCR | NO | P | REWRITE |
| X-S1.4 | Identify queues with rising AHT | NO | P | REWRITE |

**Assessment:** No step references "case", "ticket", or "incident". All steps are queue/agent-group scoped.

---

## XD-002 — Grain: `agent_day`

| Action Code | Step 1 (verbatim) | Entity Ref | Voice | Verdict |
|-------------|-------------------|------------|-------|---------|
| X-R2.1 | Detect sustained utilization band violations | NO | P | REWRITE |
| X-R2.2 | Identify queues with sustained utilization imbalance | NO | P | REWRITE |
| X-R2.3 | Identify queues with elevated shrinkage | NO | P | REWRITE |
| X-R2.4 | Identify queues with recurring overtime | NO | P | REWRITE |

**Assessment:** No step references "agent" or "representative" or "resource". All queue-scoped.

---

## XD-003 — Grain: `entity_month`

| Action Code | Step 1 (verbatim) | Entity Ref | Voice | Verdict |
|-------------|-------------------|------------|-------|---------|
| X-E3.2 | Aggregate downside deviation per KPI | NO | D (passive aggregation) | REWRITE |
| X-E3.3 | Track routed Action Codes and execution status | NO | D (tracking, not action) | REWRITE |

**Assessment:** Steps are descriptive/passive (aggregation, tracking). No entity reference. Needs both voice and entity fix.

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total action-code-to-use-case subscriptions | 56 |
| Unique action codes audited | 50 |
| Entity reference present (YES) | 17 |
| Entity reference missing (NO) | 39 |
| Prescriptive voice (P) | 54 |
| Descriptive voice (D) | 2 (X-E3.2, X-E3.3) |
| Verdict OK | 17 |
| Verdict REWRITE | 39 |

### Pattern

- **Orchestrator action codes** (*.1 suffix — the first action in each group) almost always lack entity references because they diagnose at an aggregate level. These need the most significant rewording.
- **Execution action codes** (*.2–*.5 suffix) are more specific but still frequently omit the grain entity.
- **Voice** is already prescriptive in 54/56 cases. Only X-E3.2 and X-E3.3 (Executive) use descriptive/passive voice.

### Recommendation

All 39 REWRITE cases need step text updated to:
1. Include the grain entity noun (or `{entity}` placeholder for shared actions).
2. Use imperative verb-first phrasing where not already done.
