# Golden Semantic Model – Commercial

## Purpose

The Commercial Golden Semantic Model defines the **canonical meaning of commercial performance** across the enterprise.

It serves as the **single semantic foundation** for all commercial use cases, KPIs, and Action Codes related to:

- Revenue growth
- Pricing and margin
- Promotions
- Customer commercial behavior

All Commercial Use Cases consume this model.
None redefine it.

---

## Scope

This semantic core defines:

- Canonical commercial KPIs
- Stable grains and aggregation rules
- Explicit economic assumptions
- Shared commercial dimensions

It does NOT:

- Encode use-case-specific logic
- Implement reporting layouts
- Define operational execution steps

---

## Canonical Dimensions

The Commercial domain relies on the following shared dimensions:

- Date (Day / Week / Month)
- Product (SKU, Category, Brand)
- Customer (Account, Segment)
- Organization (Sales Org, Region, Channel)
- Promotion (Campaign, Mechanic – if applicable)

These dimensions are shared across domains but interpreted **commercially** here.

---

## Canonical KPI Families

The Commercial semantic core covers the following KPI families:

### Growth

- Net Sales Amount
- Net Sales Amount LY
- Δ Net Sales Amount
- Δ% Net Sales
- Volume Sold
- Price Realization %

### Profitability

- Gross Margin Amount
- Gross Margin %
- Discount %
- Price Effect Amount
- Volume Effect Amount
- Mix Effect Amount

### Promotion

- Promo Uplift %
- Incremental Sales Amount
- Cannibalization %

Each KPI is defined **once** in the KPI Catalog and referenced here.

---

## Economic Assumptions (Explicit)

The Commercial semantic model enforces the following assumptions:

- Revenue and margin KPIs are **managerial**, not statutory.
- Price effects and volume effects are **mutually exclusive decompositions**.
- Promotions are evaluated on **incrementality**, not gross uplift.
- Margin optimization takes precedence over pure volume growth unless explicitly overridden.

These assumptions apply to all consuming use cases and Action Codes.

---

## Relation to Action Codes

All Commercial Action Codes:

- Reference KPIs defined in this semantic model
- Assume the grains and aggregations defined here
- Do NOT redefine calculations or interpretations

Action Codes operate **on top of** the semantic model, never inside it.

---

## Cross-Domain Usage

Commercial KPIs may be used in:

- Executive overviews
- Customer experience analyses
- Financial liquidity assessments

Rules:

- Commercial KPIs remain owned by the Commercial domain
- Cross-domain views consume, but do not reinterpret
- No KPI logic is duplicated across domains

---

## Definition of Done

The Commercial Golden Semantic Model is considered complete when:

- All Core Commercial Use Cases are fully covered
- No use case requires custom commercial measures
- All Action Codes map cleanly to KPIs in this model

Once complete, the model is **stable and read-only**.

---

## Why This Matters

This model ensures that:

- Commercial decisions are based on one truth
- New use cases do not increase complexity
- Prescriptive actions scale consistently
- Automation and AI operate safely

This is the foundation for scalable, enterprise-grade commercial analytics.

