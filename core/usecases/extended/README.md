# Extended Use Cases

## Purpose

Extended use cases go beyond the 15 core use cases to address more specific
business problems, deeper analytical techniques, or domain-specific variants
that are broadly applicable but not universal.

Core use cases provide the baseline blueprint set that every implementation
should have. Extended use cases add depth: they answer "what comes next" once
the core layer is operational and teams are ready for more advanced analytics.

---

## What Makes a Use Case "Extended"

An extended use case must satisfy all of the following:

| Criterion | Requirement |
|-----------|-------------|
| **Not a duplicate** | Does not replicate a core use case; clearly additive |
| **Cross-industry applicability** | Applicable to ≥50% of target industries (vs. industry-specific → see `industry/`) |
| **Requires core as a prerequisite** | Builds on ≥1 core use case; not standalone |
| **Prescriptive output** | Must produce action-code-ready decisions, not just descriptive charts |
| **Bracket-ready** | Must have or be on a roadmap to have a `UseCase_Bracket.yaml` |

Extended use cases that become universally adopted across all implementations
should be promoted to `core/usecases/core/` via a structured review.

---

## Naming Convention

Extended use cases follow the same naming scheme as core:

```
<DOMAIN>-EXT-<NNN>_<ShortTitle>/
  Business_Factsheet.md
  UseCase_Bracket.yaml      ← required when build-ready
```

Examples:
- `COM-EXT-001_Advanced_Customer_Segmentation/`
- `FIN-EXT-001_Budget_Variance_Waterfall/`
- `SCM-EXT-001_Supplier_Risk_Monitoring/`
- `OPS-EXT-001_Predictive_Maintenance_Readiness/`

---

## Roadmap

The following extended use cases are planned or under consideration.
Status: `planned` = defined in backlog | `draft` = in development | `build_ready` = ready for implementation

| ID | Title | Domain | Prerequisite Core UC | Status |
|----|-------|--------|---------------------|--------|
| COM-EXT-001 | Advanced Customer Segmentation (RFM + CLV) | Commercial | COM-001, COM-003 | planned |
| COM-EXT-002 | Price Elasticity Analysis | Commercial | COM-002 | planned |
| COM-EXT-003 | Channel Mix Optimization | Commercial | COM-001, COM-002 | planned |
| FIN-EXT-001 | Budget Variance Waterfall (P&L Bridge) | Finance | FIN-002 | planned |
| FIN-EXT-002 | Rolling Forecast vs Actuals | Finance | FIN-001, FIN-002 | planned |
| SCM-EXT-001 | Supplier Risk & Dual-Sourcing Monitor | Supply Chain | SCM-002 | planned |
| SCM-EXT-002 | Network Inventory Optimization | Supply Chain | SCM-001, SCM-003 | planned |
| OPS-EXT-001 | Predictive Maintenance Readiness | Operations | OPS-002 | planned |
| OPS-EXT-002 | Energy & Sustainability per Unit | Operations | OPS-001 | planned |
| XD-EXT-001 | Cross-Domain P&L Attribution | Cross-Domain | XD-003, FIN-002 | planned |

To propose a new extended use case, follow the intake process in
`core/usecases/templates/UseCase_Bracket_TEMPLATE.yaml` and reference this
README in the PR description.

---

## Promotion to Core

An extended use case is promoted to `core/usecases/core/` when:

1. It is implemented in ≥3 independent showcases or client deployments
2. It passes the full Core Use Case DoD (`core/usecases/usecase_DoD_Core.md`)
3. It is reviewed and approved by the Framework Owner

After promotion, the extended entry becomes a redirect or stub pointing to the
new core location.

---

## Relations

- **Core layer:** `core/usecases/core/` — canonical blueprint set
- **Industry layer:** `core/usecases/industry/` — industry-vertical use cases
- **Templates:** `core/usecases/templates/` — shared Factsheet and Bracket templates
- **Inventory:** `core/usecases/UseCase_Inventory.md` — master list including extended status
