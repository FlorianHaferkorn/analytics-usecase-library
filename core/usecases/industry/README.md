# Industry Use Cases

## Purpose

Industry use cases address analytics scenarios that are specific to one or a
small number of verticals. They follow the same framework standards as core and
extended use cases, but their applicability is bounded by industry context.

The industry layer allows the framework to speak the language of specific
sectors — using domain terminology, sector-specific KPIs, and regulatory or
operational realities that are not meaningful cross-industry.

---

## What Makes a Use Case "Industry-Specific"

An industry use case must satisfy all of the following:

| Criterion | Requirement |
|-----------|-------------|
| **Vertical-specific** | Applicable to ≤2 industries without major adaptation |
| **Not an extended use case** | Cannot be generalized to ≥50% of industries as-is |
| **Framework-compliant** | Must follow the same Bracket schema and DoD as core |
| **Named vertical** | Must be filed under a named industry sub-folder (see below) |

If a use case previously filed as industry-specific proves broadly applicable,
it should be promoted to `extended/` rather than `core/` unless it passes the
full Core DoD and is universally relevant.

---

## Naming Convention

Industry use cases are organized by vertical and follow this structure:

```
<VERTICAL>/<DOMAIN>-IND-<NNN>_<ShortTitle>/
  Business_Factsheet.md
  UseCase_Bracket.yaml      ← required when build-ready
```

Examples:
- `retail/COM-IND-001_Basket_Analysis/`
- `manufacturing/OPS-IND-001_Shift_OEE_Benchmarking/`
- `pharma/OPS-IND-001_Batch_Release_Performance/`
- `logistics/SCM-IND-001_Last_Mile_Delivery_Performance/`

---

## Planned Verticals

The following verticals are on the roadmap. Entries move from `planned` to
`active` once the first use case under that vertical reaches `build_ready`.

| Vertical | Focus | Status | Core Prerequisites |
|----------|-------|--------|--------------------|
| **Retail & CPG** | Category management, basket analysis, promotional uplift | planned | COM-001, COM-004, SCM-001 |
| **Manufacturing** | Shift benchmarking, batch performance, yield by product family | planned | OPS-001, OPS-003 |
| **Logistics & 3PL** | Last-mile performance, carrier scorecard, dock utilization | planned | SCM-002, OPS-001 |
| **Pharma & MedTech** | Batch release, deviation tracking, serialization compliance | planned | OPS-003, XD-001 |
| **Financial Services** | Loan portfolio quality, liquidity stress, operational loss | planned | FIN-001, FIN-002 |
| **Professional Services** | Utilization vs. realization, project margin, bench management | planned | XD-002, FIN-002 |

---

## Planned Use Cases by Vertical

### Retail & CPG

| ID | Title | Prerequisite Core UC | Status |
|----|-------|---------------------|--------|
| COM-IND-R001 | Basket & Category Cross-Sell Analysis | COM-001, COM-003 | planned |
| COM-IND-R002 | Promotional Lift vs. Cannibalization | COM-004 | planned |
| SCM-IND-R001 | Shelf Availability & OSA Monitoring | SCM-001, SCM-002 | planned |

### Manufacturing

| ID | Title | Prerequisite Core UC | Status |
|----|-------|---------------------|--------|
| OPS-IND-M001 | Shift OEE Benchmarking across Plants | OPS-001 | planned |
| OPS-IND-M002 | Batch Yield Variability & Root Cause | OPS-003 | planned |
| SCM-IND-M001 | Make-to-Order vs. Make-to-Stock Mix | SCM-001, SCM-003 | planned |

### Logistics & 3PL

| ID | Title | Prerequisite Core UC | Status |
|----|-------|---------------------|--------|
| SCM-IND-L001 | Last-Mile Delivery Performance | SCM-002 | planned |
| SCM-IND-L002 | Carrier Scorecard & Rate Compliance | SCM-002 | planned |
| OPS-IND-L001 | Dock & Yard Utilization | OPS-001 | planned |

---

## Promotion Paths

```
industry/  →  extended/  →  core/
```

- **Industry → Extended**: Use case proven applicable across ≥3 industries
- **Extended → Core**: Universal applicability confirmed across ≥3 deployments + Core DoD met

---

## Relations

- **Core layer:** `core/usecases/core/` — canonical cross-industry blueprint set
- **Extended layer:** `core/usecases/extended/` — advanced cross-industry use cases
- **Templates:** `core/usecases/templates/` — shared Factsheet and Bracket templates
- **Inventory:** `core/usecases/UseCase_Inventory.md` — master list including industry status
