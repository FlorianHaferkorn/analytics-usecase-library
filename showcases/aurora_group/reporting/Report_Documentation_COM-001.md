# Report Documentation: COM-001

**Use Case:** COM-001  
**Domain:** Commercial  
**Report Owner:** CCO / Head of Sales  
**Last Updated:** 2026-02-07  
**Version:** 1.0  
**Theme:** CY25SU10  

**Purpose:**  
Explain Net Sales performance vs Plan and vs Last Year by price,

**Target Audience:**  
Management / Tactical (from Business Factsheet)

**Usage Rhythm:**  
Weekly / Monthly (from Business Factsheet)

---

## Report Overview

### Business Questions Answered

- Where do Net Sales deviate most vs Plan and vs LY by region, channel, and product hierarchy?
- What is the contribution of price, volume, and mix to the Net Sales gap?
- Which customer or product segments drive negative gross margin %?
- Which actions (pricing, mix, volume activation) close the largest gaps fastest?
- How persistent are the gaps over the last 3 months and current quarter?

### Strategic Alignment

**Strategic KPIs:**  
- Net Sales Amount (`sales.net_sales.amount`)
- Net Sales % vs Plan (`sales.net_sales.delta_pct.plan`)
- Net Sales % vs LY (`sales.net_sales.delta_pct.ly`)
- Gross Margin % (`margin.gm.pct`)
- Price Effect Amount (`sales.pvm.price_effect.amount`)
- Volume Effect Amount (`sales.pvm.volume_effect.amount`)
- Mix Effect Amount (`sales.pvm.mix_effect.amount`)

**Decision Type:** Tactical / Diagnostic (from use case.)

---

## Page Documentation

### Page: Where do Net Sales deviate most vs Plan and vs LY by region, channel, product? W...

**Page Type:** T2  
**Layer:** 3, 30  

#### Visuals

| Visual | Type | Slot (from template) |
|--------|------|----------------------|
| 1edc1be0a293490c95f7 | cardVisual | 1edc1be0a293490c95f7 |
| 20c78beb5ac84bfb9c2c | tableEx | 20c78beb5ac84bfb9c2c |
| 2875cc4857754e0cbcd4 | cardVisual | 2875cc4857754e0cbcd4 |
| 449f7dea734e48f98e7f | clusteredBarChart | 449f7dea734e48f98e7f |
| 8683c1fbb76e485aa80f | slicer | 8683c1fbb76e485aa80f |
| af5cf15f265f4c1b8ca0 | cardVisual | af5cf15f265f4c1b8ca0 |
| bd60789a3cd246d99d54 | cardVisual | bd60789a3cd246d99d54 |

*(Measures to be bound from semantic model; scaffold only.)*  

### Page: Where do Net Sales deviate most vs Plan and vs LY by region, channel, product? W...

**Page Type:** T2  
**Layer:** 300  

#### Visuals

| Visual | Type | Slot (from template) |
|--------|------|----------------------|
| 3293e5b0188c4fa892d6 | slicer | 3293e5b0188c4fa892d6 |
| 59597f6a0c394db9b672 | cardVisual | 59597f6a0c394db9b672 |
| 62fd770b5122472185f0 | cardVisual | 62fd770b5122472185f0 |
| 7c763c87b3c34bcfb88b | cardVisual | 7c763c87b3c34bcfb88b |
| 9a51e09dd0ac457ab2bd | clusteredBarChart | 9a51e09dd0ac457ab2bd |
| b5ab255ab16c4d91bbca | tableEx | b5ab255ab16c4d91bbca |
| cd09cd0880044891804d | cardVisual | cd09cd0880044891804d |

*(Measures to be bound from semantic model; scaffold only.)*  

### Page: Where do Net Sales deviate most vs Plan and vs LY by region, channel, product? W...

**Page Type:** T2  
**Layer:** 3, 30  

#### Visuals

| Visual | Type | Slot (from template) |
|--------|------|----------------------|
| 1fe72aa773384124a561 | cardVisual | 1fe72aa773384124a561 |
| 3a10c29090564e57b286 | cardVisual | 3a10c29090564e57b286 |
| 3e2c290adeed48e0ae0a | cardVisual | 3e2c290adeed48e0ae0a |
| 42dd448f9d324bae93db | slicer | 42dd448f9d324bae93db |
| 44b4339195a047fb878b | clusteredBarChart | 44b4339195a047fb878b |
| 4f18841e15f249a689f1 | waterfallChart | 4f18841e15f249a689f1 |
| 62edecfe5045488a8ff6 | lineChart | 62edecfe5045488a8ff6 |
| 711246c56f824709b611 | cardVisual | 711246c56f824709b611 |
| f287ed83559d499fb794 | textbox | f287ed83559d499fb794 |

*(Measures to be bound from semantic model; scaffold only.)*  

### Page: Where do Net Sales deviate most vs Plan and vs LY by region, channel, product? W...

**Page Type:** T2  
**Layer:** 3, 30  

#### Visuals

| Visual | Type | Slot (from template) |
|--------|------|----------------------|
| ActionPanel | textbox | ActionPanel |
| KPI_1 | cardVisual | KPI 1 |
| KPI_2 | cardVisual | KPI 2 |
| KPI_3 | cardVisual | KPI 3 |
| KPI_4 | cardVisual | KPI 4 |
| Ranking | clusteredBarChart | Ranking |
| Slicer_Date | slicer | Slicer Date |
| Trend | lineChart | Trend |
| Variance | waterfallChart | Variance |

*(Measures to be bound from semantic model; scaffold only.)*  

### Page: Where do Net Sales deviate most vs Plan and vs LY by region, channel, product? W...

**Page Type:** T2  
**Layer:** 300  

#### Visuals

| Visual | Type | Slot (from template) |
|--------|------|----------------------|
| DetailMatrix | tableEx | DetailMatrix |
| KPI_1 | cardVisual | KPI 1 |
| KPI_2 | cardVisual | KPI 2 |
| KPI_3 | cardVisual | KPI 3 |
| KPI_4 | cardVisual | KPI 4 |
| Ranking | clusteredBarChart | Ranking |
| Slicer_Date | slicer | Slicer Date |

*(Measures to be bound from semantic model; scaffold only.)*  

---

## Traceability

- **Use case:** `core/usecases/core/` (Business + Technical Factsheet)
- **KPI catalog:** `core/kpi_catalog/`
- **Action codes:** `core/action_codes/`
- **Page templates:** `core/templates/page_templates/`

**Action codes referenced:** C-M2.1, C-S1.1, C-S1.2, X-A, X-A, X-A, X-A
