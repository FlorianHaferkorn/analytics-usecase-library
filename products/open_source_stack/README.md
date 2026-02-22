# Open-Source Stack (Evidence.dev)

Platform-agnostic frontend implementation using [Evidence.dev](https://evidence.dev). Logic is driven by Core (KPI catalog, use cases, semantic model); this stack is a **connector** that renders dashboards from that logic.

## Structure

```
open_source_stack/
  evidence_app/       # Evidence app (pages, components, static)
  themes/             # Corporate design (Tailwind config, CSS variables)
  deploy/             # Docker / proxy for auth and deployment (e.g. Authentik, Traefik)
```

## Agent workflow

- **Input:** Core artifacts (e.g. `core/kpi_catalog/`, use case bracket, semantic model).
- **Template:** `core/templates/evidence_page_template.md` (design tokens: `fill-primary`, `text-brand-header`, `bg-surface`).
- **Output:** Pages under `evidence_app/pages/` (e.g. `sales_performance.md`) with SQL and Evidence components.

When adding a new dashboard for a KPI or use case, use the Evidence template and the SQL/logic from the semantic model; do not define new metrics in the page.

## Data

- Local/dev: DuckDB or other file-based source in `evidence.config.yaml`.
- Production: Postgres or warehouse; credentials and connection outside repo (env or secrets).

## Security and DSGVO

- Protect the app behind an identity proxy (Authentik, Keycloak, or Traefik auth) so that only authenticated users see data.
- No tracking; no telemetry to third parties. All changes are Git-versioned for audit.
