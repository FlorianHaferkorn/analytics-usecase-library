# Extended Playbook — Supporting KPIs (v1.0)

**Purpose:** This file catalogues the 93 supporting and narrow KPIs that complement the [Golden 20](golden_20.yaml) Lean Core spine. Each entry links back to its full definition in [KPI_Catalog.md](KPI_Catalog.md).

**Guidance:**
- These KPIs may be referenced in use case brackets as `influencing_kpi_ids`.
- They are not required in every report; use them when the use case demands deeper diagnostic depth.
- Registry builder reads both this file and `KPI_Catalog.md` — no measures are orphaned.
- Six KPIs marked `deprecated: true` below are candidates for removal in v1.1.

---

## Deprecated Orphans (v1.0 — removal target v1.1)

These KPIs have no active bracket or action code references. They will be removed after confirming no TMDL measures depend on them.

| kpi_id | Reason |
|---|---|
| `KPI-FIN-003` | Superseded by `KPI-FIN-005`; no bracket reference |
| `KPI-SCM-019` | Narrow ops metric; no use case or action code references |
| `KPI-FIN-019` | Internal calculation input; not a reportable KPI |
| `KPI-SCM-021` | Internal calculation input; not a reportable KPI |
| `KPI-GOV-003` | Replaced by `KPI-GOV-001` as primary |

---

## Supporting KPIs by Domain

### Customer & Market

| kpi_id | Back-link |
|---|---|
| `KPI-SVC-001` | [KPI_Catalog.md — KPI-SVC-001](KPI_Catalog.md) |
| `KPI-CUS-004` | [KPI_Catalog.md — KPI-CUS-004](KPI_Catalog.md) |
| `KPI-CUS-005` | [KPI_Catalog.md — KPI-CUS-005](KPI_Catalog.md) |
| `KPI-CUS-006` | [KPI_Catalog.md — KPI-CUS-006](KPI_Catalog.md) |

### Commercial / Sales

| kpi_id | Back-link |
|---|---|
| `KPI-COM-001` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-COM-002` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-COM-003` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-COM-004` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-COM-010` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-COM-011` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-COM-008` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-COM-009` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-COM-012` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-COM-014` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-COM-015` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-COM-016` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-COM-017` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-COM-018` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-COM-020` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-COM-021` | [KPI_Catalog.md](KPI_Catalog.md) |

### Operations / Quality

| kpi_id | Back-link |
|---|---|
| `KPI-OPS-003` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-OPS-004` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-OPS-005` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-OPS-006` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-OPS-007` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-OPS-008` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-OPS-009` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-OPS-011` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-OPS-012` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-OPS-016` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-OPS-017` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-OPS-018` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-OPS-015` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-QUA-002` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-OPS-010` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-QUA-004` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-QUA-005` | [KPI_Catalog.md](KPI_Catalog.md) |

### Supply Chain / Demand Planning

| kpi_id | Back-link |
|---|---|
| `KPI-SCM-004` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SCM-016` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SCM-008` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SCM-018` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SCM-009` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SCM-010` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SCM-011` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SCM-012` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SCM-017` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SCM-022` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SCM-013` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SCM-014` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SCM-015` | [KPI_Catalog.md](KPI_Catalog.md) |

### Finance / Working Capital

| kpi_id | Back-link |
|---|---|
| `KPI-FIN-001` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-FIN-004` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-FIN-005` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-FIN-006` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-FIN-007` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-FIN-009` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-FIN-010` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-FIN-002` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-FIN-012` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-FIN-016` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-FIN-017` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-FIN-013` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SCM-020` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-FIN-014` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-FIN-015` | [KPI_Catalog.md](KPI_Catalog.md) |

### People / Resource

| kpi_id | Back-link |
|---|---|
| `KPI-SVC-002` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SVC-003` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SVC-009` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SVC-010` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SVC-011` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SVC-012` | [KPI_Catalog.md](KPI_Catalog.md) |

### Service

| kpi_id | Back-link |
|---|---|
| `KPI-SVC-004` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SVC-006` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SVC-007` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SVC-013` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-SVC-014` | [KPI_Catalog.md](KPI_Catalog.md) |

### Enterprise / Cross-Domain

| kpi_id | Back-link |
|---|---|
| `KPI-GOV-001` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-GOV-004` | [KPI_Catalog.md](KPI_Catalog.md) |

### Internal Calculation Inputs (narrow)

> These are referenced only as sub-components of other KPI measures. Consider consolidating into their parent measure definitions.

| kpi_id | Back-link |
|---|---|
| `KPI-OPS-013` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-OPS-014` | [KPI_Catalog.md](KPI_Catalog.md) |
| `KPI-QUA-006` | [KPI_Catalog.md](KPI_Catalog.md) |
