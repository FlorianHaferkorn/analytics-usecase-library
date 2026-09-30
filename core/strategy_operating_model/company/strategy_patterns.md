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

1. KPI-COM-013, KPI-FIN-017  
2. KPI-COM-003  
3. KPI-FIN-015, KPI-FIN-016, KPI-FIN-014  
4. KPI-COM-004, KPI-FIN-013  

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

1. KPI-FIN-007, KPI-FIN-009, KPI-FIN-010  
2. KPI-FIN-006, KPI-FIN-001, KPI-FIN-004, KPI-FIN-005  
3. KPI-SCM-001, KPI-SCM-016, KPI-SCM-002  
4. KPI-COM-013 (guardrail: do not sacrifice margin for volume that hurts cash)  

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

1. KPI-COM-005, KPI-COM-009, KPI-COM-008  
2. KPI-CUS-001, KPI-CUS-002, KPI-CUS-004, KPI-OPS-001  
3. KPI-COM-013 (guardrail), KPI-COM-010, KPI-COM-011, KPI-COM-004  
4. KPI-COM-016, KPI-COM-021 (if promotion-heavy)  

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
- **KPI Catalog:** All Strategic KPIs listed in patterns must exist in `core/kpi_catalog/`.
- **Use Case Inventory:** `core/usecases/UseCase_Inventory.md` — use-case IDs and Key Questions align with the clusters above.
- **Golden Thread:** `operating_model/golden_thread_strategy_to_action.md` — strategy patterns feed Step 1 (Business Strategy) and Step 2 (Strategic KPIs → Key Questions).

---

## 8. Urgency rules (for tooling)

These rules make the strategy pattern **precise enough for tooling** so that urgency derivation (e.g. which deviation or action to surface first) can be automated from governed artifacts.

**Inputs:**

- **Active pattern(s):** One or two of `Margin-First`, `Cash-First`, `Growth-First`. When blending, primary pattern wins for top tiers.
- **Strategic KPI priority:** Per pattern, sections 3–5 above define a fixed order (1 = highest, 2, 3, 4). That order is the **KPI urgency tier** (tier 1 = highest urgency when in deviation).
- **Use-case cluster priority:** Per pattern, the tables in sections 3–5 define **use-case cluster priority** (1 = highest). Use-case IDs in each cluster are listed in those tables.

**Rule (relative urgency):**

1. **By KPI deviation:** A deviation or trigger on a Strategic KPI in **tier 1** (first numeric list in the pattern) has higher relative urgency than a deviation on tier 2, and so on. Tooling can rank actions or use cases by the highest-priority KPI they address.
2. **By use-case cluster:** For ordering use cases (e.g. which to implement or surface first), use the **Priority** column (1, 2, 3, 4) in the pattern’s use-case cluster table. Lower number = higher urgency.
3. **Blended patterns:** When two patterns are blended, primary pattern defines tiers 1–2; secondary adds tier 3–4. Guardrails from both apply; do not promote urgency of a guardrail KPI above the primary pattern’s tier 1.

**Tooling contract (summary):**

| Input | Source in this document | Use for urgency |
|-------|-------------------------|-----------------|
| Pattern id | Section 3 / 4 / 5 heading (Margin-First, Cash-First, Growth-First) | Select KPI and use-case priority tables |
| KPI priority order | Numbered list under "Strategic KPIs (priority order)" per pattern | Tier 1 = highest urgency when KPI in deviation |
| Use-case cluster priority | Table "Use-case clusters (priority)" per pattern; column Priority (1–4) | Cluster 1 = highest urgency for ordering use cases |

Implementation of a script or API that consumes this document (or an exported schema) is in backlog; see [urgency_derivation_spec.md](../../../tooling/ir/urgency_derivation_spec.md) (tooling hook for urgency derivation).

---

## 9. Pattern-selection decision guide

Use these questions to select or blend patterns. Work top-to-bottom; the first branch that matches determines the primary pattern. A secondary pattern can be added in the next pass.

```
START
  │
  ▼
Q1: Is cash position or CCC currently the most critical leadership concern?
  ├── YES → Primary: Cash-First
  │         (re-enter for secondary if margin or growth also under pressure)
  └── NO
       │
       ▼
      Q2: Is gross margin or EBIT significantly below plan or trend?
        ├── YES → Primary: Margin-First
        │         (add Cash-First as secondary if DSO or DIO also elevated)
        └── NO
             │
             ▼
            Q3: Is top-line growth the primary strategic commitment for the period?
              ├── YES → Primary: Growth-First
              │         (add Margin-First as secondary if guardrail KPIs approach boundary)
              └── NO → Blend or escalate to leadership for priority reset
```

**When blending:** the primary pattern governs tier 1–2 KPI urgency. The secondary pattern contributes tier 3–4 and adds its guardrail conditions to the decision boundary. Never invert guardrail KPIs above tier 1 of the primary pattern.

---

## 10. Reference guardrails (orientation only)

These values are **illustrative reference points** — not mandatory thresholds. They provide starting orientation for teams that have not yet defined their own thresholds. Each company must calibrate to its own industry, business model, and operating context.

### Margin-First — reference guardrails

| Dimension | Orientation value | Rationale |
|-----------|-------------------|-----------|
| GM% deviation vs. plan | > −2pp sustained over 2+ periods triggers spine activation | Industry-typical sensitivity before structural action is justified |
| Price realization | < 95% sustained signals systematic discounting or mix erosion | 5pp buffer for normal variation; below this, pricing discipline review warranted |
| COGS vs. plan | > +3% sustained over 1 quarter without structural explanation | Distinguishes noise from systematic cost drift |
| Revenue growth guardrail | Growth actions acceptable if GM% remains > agreed floor | Prevents volume growth that dilutes margin below strategic minimum |

### Cash-First — reference guardrails

| Dimension | Orientation value | Rationale |
|-----------|-------------------|-----------|
| OCF vs. plan | < 90% of planned OCF for 2+ periods triggers escalation | 10% buffer for normal timing differences; below this, structural lever review warranted |
| CCC trend | Rising CCC (DSO + DIO − DPO) for 2+ consecutive periods | Directional deterioration signal regardless of absolute level |
| DSO deviation | > +5 days vs. plan sustained | Indicates collections or terms issue beyond normal customer behaviour |
| DIO deviation | > +7 days vs. plan sustained | Distinguishes seasonal buffer from structural overstock |
| Service level guardrail | Inventory reduction actions require OTIF to remain above agreed floor | Prevents cash optimization at the expense of service delivery |

### Growth-First — reference guardrails

| Dimension | Orientation value | Rationale |
|-----------|-------------------|-----------|
| Revenue vs. plan | < 95% of planned Net Sales for 2+ periods triggers spine activation | 5% buffer for normal phasing; below this, structural demand review warranted |
| CLV trend | Declining CLV cohort trend over 3+ periods | Indicates structural customer value erosion vs. one-time churn |
| Margin guardrail | Growth actions require GM% to remain above agreed floor | Prevents revenue growth that dilutes profitability below strategic minimum |
| Cash guardrail | Revenue initiatives must not reduce OCF below agreed liquidity floor | Prevents growth investment that creates structural cash risk |

---

## 11. Urgency conflict resolution

When two patterns are active simultaneously and both signal deviation at the same urgency tier, apply this resolution order:

1. **Cash guardrail always wins over margin or growth** — liquidity risk is existential; no margin improvement or growth initiative proceeds if it breaches an active cash guardrail.
2. **Margin guardrail overrides growth** — if growth actions are driving margin below the agreed floor, the growth lever is paused until margin stabilizes.
3. **Tie within the same pattern tier** — rank by financial impact magnitude (absolute deviation × weighting factor defined in KPI Catalog). Surface the larger-impact deviation first.
4. **Cross-domain escalation** — if conflict involves KPIs owned by different domains, escalate to the Executive Cross-Domain Governance spine (`DEC-SPINE-XD-EXEC`) for prioritization.

**Example:** Cash-First (primary) + Margin-First (secondary) are both active. DSO is elevated (Cash-First tier 1) and GM% is below plan (Margin-First tier 1 for the secondary). Resolution: DSO action takes priority because cash guardrail is in force; GM% action is tracked but subordinated until cash trajectory improves.

---

## 12. Automated reasoning scope

Scope and limits of **automated reasoning** (AI urgency, action suggestion from governed logic, triage, assisted authoring) are defined in a single place so that tooling and product stay aligned:

- **[internal/vision/automated_reasoning_scope_and_limits.md](../../../internal/vision/automated_reasoning_scope_and_limits.md)** — what is in scope, what is out of scope or limited, and how it relates to strategy patterns, urgency rules (§8), and conflict resolution (§11).

---

## Sources & Grounding

The "strategy patterns" in this document (Margin-First, Cash-First, Growth-First) are this
framework's own KPI-and-use-case packaging. Their underlying logic — that a company should make
an explicit strategic choice, accept trade-offs and guardrails, and align its operating focus to
that choice — draws on the canonical strategy frameworks below:

- **Porter's generic strategies** (a firm must choose a clear strategic position — cost
  leadership, differentiation, or focus — rather than be "stuck in the middle"; the basis for the
  "choose or blend a pattern" logic and explicit trade-offs) — Michael E. Porter, *Competitive
  Strategy: Techniques for Analyzing Industries and Competitors*, Free Press (1980); Harvard
  Business School Institute for Strategy and Competitiveness, Strategic Positioning:
  <https://www.isc.hbs.edu/strategy/business-strategy/Pages/strategic-positioning.aspx>
- **Porter's Five Forces** (industry structure as the context that makes a given strategic
  emphasis — margin, cash, or growth — appropriate) — Michael E. Porter, *How Competitive Forces
  Shape Strategy*, Harvard Business Review (1979):
  <https://hbr.org/1979/03/how-competitive-forces-shape-strategy> · Harvard Business School
  Institute for Strategy and Competitiveness:
  <https://www.isc.hbs.edu/strategy/business-strategy/Pages/the-five-forces.aspx>
- **Treacy & Wiersema value disciplines** (market leaders pick one value discipline —
  operational excellence, customer intimacy, or product leadership — and align everything to it;
  the conceptual parallel to choosing a primary pattern) — Michael Treacy & Fred Wiersema,
  *Customer Intimacy and Other Value Disciplines*, Harvard Business Review (1993):
  <https://hbr.org/1993/01/customer-intimacy-and-other-value-disciplines>
- **Blue Ocean Strategy / value innovation** (the simultaneous pursuit of differentiation and
  low cost; basis for treating margin and growth as steerable trade-offs rather than fixed
  opposites) — W. Chan Kim & Renée Mauborgne (INSEAD), *Blue Ocean Strategy*, Harvard Business
  School Press (2005): <https://www.blueoceanstrategy.com/what-is-blue-ocean-strategy/> · Value
  Innovation: <https://www.blueoceanstrategy.com/tools/value-innovation/>
- **Balanced Scorecard** (each pattern anchors a small set of Strategic KPIs that must live in
  the KPI Catalog and semantic model — the BSC principle of translating strategy into governed
  measures) — Kaplan & Norton, *The Balanced Scorecard—Measures That Drive Performance*, Harvard
  Business Review (1992):
  <https://hbr.org/2005/07/the-balanced-scorecard-measures-that-drive-performance>

> The specific KPI IDs, use-case clusters, guardrail values, and urgency rules in this document
> are framework-internal constructs; only the strategic-choice methodology they instantiate is
> grounded above. The reference guardrail values in §10 are explicitly illustrative, not sourced
> thresholds.

