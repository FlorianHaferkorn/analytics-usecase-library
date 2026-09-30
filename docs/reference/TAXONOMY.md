# Taxonomy Reference

This document defines the naming conventions, ID schemes, and domain structure
used across ALUCA (Analytics Library of Use Cases).

## Domain Prefixes

| Prefix | Domain | Example use case |
|--------|--------|-----------------|
| `COM` | Commercial (Sales, Marketing, CRM) | COM-001 Sales Performance |
| `FIN` | Finance (Cash, P&L, Controlling) | FIN-001 Cash & Liquidity |
| `OPS` | Operations (Production, Efficiency) | OPS-001 Operations Performance |
| `SCM` | Supply Chain (Inventory, Logistics) | SCM-001 Inventory Performance |
| `HR` | People & HR | (planned) |
| `MFG` | Manufacturing | (planned) |
| `XD` | Cross-Domain / Executive | XD-001 Service Level Performance |

## ID Schemes

### KPI IDs

Format: `KPI-<KUERZEL>-<NNN>` (Meridian D-594, 30.09.2026) — one numbering space for ALUCA,
industry packs and Meridian tenants. The ID carries no meaning; name, unit and formula live in the
catalog entry (`kpi_key`, `business.unit_format`, `technical.calculation`).

| Segment | Rules | Example |
|---------|-------|---------|
| `KPI` | fixed prefix | `KPI` |
| Kürzel | business ownership of the KPI (lever: owner role of the action codes pointing at it, else `governance.business_owner`); list in `tooling/validation/_index.yaml` `kpi_domains` | `COM`, `FIN`, `OPS`, `SCM`, `SVC`, `CUS`, `GOV`, `PPL`, `QUA`, `ESG` |
| Nummer | three digits, running per Kürzel from 001 | `005` |

Examples: `KPI-COM-005`, `KPI-CUS-001`, `KPI-FIN-006`

### Use Case IDs

Three tiers, ratified in [ADR-0004](../architecture/adr/0004-industry-variant-use-case-tier-taxonomy.md):

| Tier | Format | Folder | Example |
|------|--------|--------|---------|
| Core (governed-16) | `<DOMAIN>-<NNN>` | `core/usecases/core/` | `COM-001` |
| Cross-industry extension | `<DOMAIN>-EXT-<NNN>` | `core/usecases/extended/` | `COM-EXT-001` |
| Industry / sector-specific | `<DOMAIN>-IND-<S><NNN>` | `core/usecases/industry/<sector>/` | `COM-IND-R001` |

Uppercase domain prefix; `EXT` marks a sector-agnostic extension; `IND-<S>` marks a sector-specific variant where `<S>` is a sector letter (**R**=Retail, **L**=Logistics, **M**=Manufacturing). The `<NNN>` sequence restarts per `(domain, tier[, sector])` namespace.

- Folder name: `<ID>_<Descriptive_Name>` (e.g. `COM-001_Sales_Performance`, `COM-IND-R001_Basket_Category_CrossSell`)
- Each folder contains `Business_Factsheet.md` and `UseCase_Bracket.yaml` (schema version declared inside the file as `schema_version: '2.0'`)
- Extension-tier use cases pass the **same** Golden Thread gates as core.

### Action Code IDs

Format: `<Prefix>-<Type><Sequence>.<Sub>`

| Segment | Meaning | Values |
|---------|---------|--------|
| Prefix | Domain letter | `C` (Commercial), `F` (Finance), `O` (Operations), `S` (Supply Chain), `E` (Enterprise), `P` (People), `X` (Cross-Domain) |
| Type | Action category | `M` (Margin/Revenue), `P` (Process), `S` (Service), `C` (Cost), `R` (Risk) |
| Sequence | Numbered within type | `1`, `2`, `3`, ... |
| Sub | Variant/sub-action | `.1`, `.2`, ... |

Examples: `C-M1.1` (Commercial, Margin action 1.1), `F-C2.1` (Finance, Cost action 2.1)

### Data Contract IDs

Domain contracts: `<domain_name>.yaml` (snake_case)
Source contracts: `<domain>_<source>.yaml`

Located in `core/data_contracts/domains/` and `core/data_contracts/sources/`.

## KPI Catalog Tiers (Lean Core v1.0)

The KPI catalog is organized in two tiers:

| Tier | File | Count | Description |
|------|------|-------|-------------|
| **Lean Core (Golden 20)** | `core/kpi_catalog/golden_20.yaml` | 20 | Strategic spine; every Aurora report references at least one |
| **Extended Playbook** | `core/kpi_catalog/extended_playbook.md` | 93 | Supporting and narrow KPIs; used as `influencing_kpi_ids` |

Registry builder reads both files. KPIs marked `deprecated: true` in the catalog are excluded from Aurora generation.

## KPI Roles

Each KPI in the catalog has a `kpi_role`:

| Role | Meaning | Usage |
|------|---------|-------|
| `strategic` | Top-level KPI tracked by leadership | Drives Golden Thread (H1 metric) |
| `influencing` | Mid-level KPI that influences strategic KPIs | Referenced in use case brackets |
| `operational` | Day-to-day metric | Used in measure dictionaries |
| `supporting` | Supporting/derived measure backing other KPIs | Used in formulas and aggregations |

## Action Code Structure

Each action code YAML contains:

```yaml
id: C-M1.1
name: Revenue Recovery Action
trigger:
  type: threshold          # threshold, trend, anomaly
  evaluation:
    levels: [...]          # warning, critical, etc.
impact:
  category: revenue        # revenue, cost, risk, process
  expected_range: "1-5%"
kpis:
  trigger_kpis: [...]      # KPIs that fire this action
  guardrail_kpis: [...]    # KPIs to watch during execution
  outcome_kpis: [...]      # KPIs measuring action success
operational_execution:
  steps: [...]             # Concrete execution steps
```

## Measure Dictionary Entries

Each measure in `Measure_Dictionary_<Domain>.md`:

```yaml
- measure_name: Net Sales Amount
  kpi_id_ref: KPI-COM-005    # Links to KPI catalog
  is_kpi_measure: true
  governance:
    status: active                       # active | draft
  aggregation_method: sum                # sum, avg, count, min, max (optional)
```

## Golden Thread Traceability

The framework's core principle is end-to-end traceability:

```
Strategy → KPIs → Use Cases → Semantic Models → Reports → Actions
```

The health scorecard (H1 metric) validates that each strategic KPI can be
traced through all five layers:

1. **KPI Catalog** — KPI is defined with role=strategic
2. **Use Case Bracket** — KPI is referenced in a bracket
3. **Measure Dictionary** — KPI has a corresponding measure (kpi_id_ref)
4. **Data Contract** — Measure source has a domain contract
5. **Action Code** — At least one action references the KPI

Run `python tooling/health_scorecard.py` to check coverage.
