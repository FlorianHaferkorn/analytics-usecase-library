# COM-004 – Promotion Effectiveness (Business Factsheet)

## 0. Metadata (Mandatory)
- **Use Case ID:** COM-004
- **Domain:** Commercial
- **Owner (Business):** CMO / Trade Marketing / Revenue Growth Mgmt
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/commercial_sales.yaml
- **Related Semantic Model:** semantic_models/core_action_ready/commercial_sales/model_definition.yaml

---

## 1. Summary
**Purpose:** Improve promotion ROI by measuring incremental sales and margin impact.  
**Business Value:** Fewer unprofitable promos, higher incremental GM, better channel/product targeting.  
**Out of Scope:** Long-term pricing strategy (COM-002); assortment optimization (separate UC).

---

## 2. Core Questions
- Which promotions generated true incremental sales and margin?
- Which channels/products deliver the highest promo ROI?
- How much did discounts erode price realization and GM?
- What depth/timing/mechanics should future promotions follow?
- Where do cannibalization or leakage offset uplift?

**Example Queries:**  
- “Which top-10 promos by channel delivered ROI >120 % and uplift >5 %?”  
- “Which mechanics drive lowest leakage and best ROI for category X?”  

---

## 3. KPI Set (Business View)

| KPI Name             | KPI ID (mandatory)              | Purpose                          | Definition (short)                          | Unit / Format | Target / Threshold          | Interpretation                 |
|----------------------|---------------------------------|----------------------------------|---------------------------------------------|---------------|-----------------------------|--------------------------------|
| Promo ROI %          | sales.promo.roi.pct             | Profitability of promotion       | (Incremental Margin – Promo Spend) / Spend  | %             | >100 %; ≥120 % ideal        | Value-creating promo           |
| Incremental Sales %  | sales.promo.incremental.pct     | Demand lift                      | (Promo – Baseline) / Baseline               | %             | >5 % (segment-specific)     | Positive = uplift              |
| Gross Margin %       | margin.promo.gm.pct             | Margin quality during promo      | (Promo Sales – COGS) / Promo Sales          | %             | ≥ target band               | Detect leakage                 |
| Price Realization %  | sales.price.realization_pct     | Discount discipline              | Net Price / List Price                      | %             | ≥90–95 %                    | Over-discounting if too low    |
| Cannibalization %    | sales.promo.cannibalization.pct | Impact on non-promoted items     | Sales loss in related items / Promo uplift  | %             | <30 % of uplift             | High = counterproductive       |

> Do: ensure KPI IDs/targets set; avoid non-KPI fields.

---

## 4. Business Logic & Thresholds
- Promo ROI <100 % = stop or redesign.
- Incremental Sales % <5 % with GM drop = avoid repeating.
- Price Realization % <90 % = depth too high.
- Cannibalization >30 % of uplift = redesign assortment/promo set.

**Trigger (formal):**
```
WHEN sales.promo.roi.pct < 100
OR   sales.promo.incremental.pct < 5
OR   sales.price.realization_pct < 90
OR   sales.promo.cannibalization.pct > 30
THEN propose D2/P2/M3/D1 as applicable
```

---

## 5. Action Codes

| Code | Name                     | Trigger (formal, KPIs)               | Description (business action)                 | Expected KPI Impact          |
|------|--------------------------|--------------------------------------|-----------------------------------------------|------------------------------|
| D2   | Promo Redesign           | ROI <100 % or low uplift             | Adjust mechanics, depth, timing               | Higher ROI, less leakage     |
| P2   | Price/Discount Guardrail | Price Realization % <90–95 %         | Enforce floor prices and caps                 | +0.3–0.7 pp GM %             |
| M3   | Assortment Focus         | High cannibalization, low GM         | Promote high-margin SKUs                      | Better promo mix             |
| D1   | Demand Boost Targeted    | Strong ROI in select segments        | Scale positive promos to good segments        | Preserve ROI, grow NS        |

> Do: use ActionCodes_Portfolio; keep triggers KPI-based.

---

## 6. 3–30–300 Page Layout

### 6.1 3-Second Layer (KPI Cards – mandatory)
- Promo ROI %, Incremental Sales %, GM %, Price Realization %, Cannibalization %.

### 6.2 30-Second Layer (Main Visuals – mandatory)
| Visual Name          | Type      | X-Axis / Category | Y-Axis / Value                           | Segment / Legend | Filters            |
|----------------------|-----------|-------------------|------------------------------------------|------------------|--------------------|
| Promo ROI & GM Trend | Line      | dim_date[Month]   | [Promo ROI %], [Promo GM %], [Uplift %]  | Channel/Region   | Last 12–24M        |
| ROI by Promo/Ch/Prod | Bar       | dim_promo[PromoName] / dim_org[Channel] / dim_product[Category] | [Promo ROI %], [Uplift %] | Region | Top/Bottom N |
| Promo Variance Bridge| Waterfall | Drivers (Price, Volume, Mix, Spend)  | Δ Promo GM vs Baseline                    | n/a              | Period selector    |
| Detail Matrix        | Matrix    | Promo → Product/Channel              | ROI %, Uplift %, GM %, Cannibalization %  | Channel/Region   | Export enabled     |

### 6.3 300-Second Layer (Diagnostics & Detail)
- Drill: Promo → Product/Channel; basket and halo analysis.
- Export: best/worst promo list with mechanics, ROI, leakage.

---

## 7. Dependencies, Assumptions & Constraints
- Data: Promo ID/flag, mechanics, spend, baseline sales/qty, list/net price, discounts, COGS; cannibalization measurement rules.
- Assumptions: Baseline method agreed (pre/post or modeled); spend captured; price/discount fields reliable.
- Constraints: Missing baseline or spend reduces ROI quality; ensure COGS/price alignment with product hierarchy.

---

## 8. Success Criteria
- Leading: >80 % usage in trade/marketing reviews; action list maintained.
- Lagging: Increase share of ROI >120 % promos; reduce unprofitable promos by >30 %; GM % during promos improves while uplift stable.
- Cadence/Quality: Monthly review; no KPI-definition conflicts.
