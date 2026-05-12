# Taxonomy Reference

This document defines the naming conventions, ID schemes, and domain structure
used across the Analytics Strategy-to-Action Framework.

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

Format: `<domain>.<entity>.<metric>[.<qualifier>]`

All lowercase, dot-separated (2-5 segments). The domain segment maps to a KPI catalog file.

| Segment | Rules | Example |
|---------|-------|---------|
| domain | Lowercase domain name | `sales`, `crm`, `finance`, `ops` |
| entity | Business entity or concept | `net_sales`, `clv`, `inventory_turn` |
| metric | Measurement type | `amount`, `pct`, `count`, `ratio`, `days` |
| qualifier | Optional: comparison, period, variant | `ly`, `plan`, `vs_plan` |

Examples: `sales.net_sales.amount`, `crm.clv.amount`, `sales.net_sales.delta_pct.ly`

### Use Case IDs

Format: `<DOMAIN>-<NNN>`

Uppercase domain prefix, dash, three-digit sequence number.

- Folder name: `<ID>_<Descriptive_Name>` (e.g. `COM-001_Sales_Performance`)
- Each folder contains `Business_Factsheet.md` and `UseCase_Bracket_v2.0.yaml`

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
  kpi_id_ref: sales.net_sales.amount    # Links to KPI catalog
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
