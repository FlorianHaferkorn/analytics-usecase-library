# KPI Catalog — Master Overview

---

## Purpose
Central index for domain KPI catalogs. All catalogs use a single schema and ID conventions.

Schema: see `/_includes/kpi_catalog/SCHEMA.md`

---

## Catalogs

| File | Impact Dimension |
|------|------------------|
| [KPI_Catalog_Growth.md](./KPI_Catalog_Growth.md) | Growth |
| [KPI_Catalog_Profitability.md](./KPI_Catalog_Profitability.md) | Profitability |
| [KPI_Catalog_Liquidity.md](./KPI_Catalog_Liquidity.md) | Liquidity |
| [KPI_Catalog_Efficiency.md](./KPI_Catalog_Efficiency.md) | Efficiency |
| [KPI_Catalog_CustomerValue.md](./KPI_Catalog_CustomerValue.md) | Customer Value |
| [KPI_Catalog_ESG.md](./KPI_Catalog_ESG.md) | ESG |
| [KPI_Catalog_Governance.md](./KPI_Catalog_Governance.md) | Governance |
| [KPI_Catalog_InnovationPeople.md](./KPI_Catalog_InnovationPeople.md) | Innovation & People |

---

## Authoring Guidelines
- Define each KPI once with a unique `kpi_id` (ASCII, namespaced).
- Use aliases for legacy names/variants as needed.
- Keep catalogs focused; put schema changes only in `SCHEMA.md`.

---

## Tooling
- Coverage (ID-only): `tools/coverage/check_factsheet_vs_kpi.ps1`
- Optional validator (IDs, types, regex) can be added to CI on request.

---

_Last updated: 03.11.2025_

