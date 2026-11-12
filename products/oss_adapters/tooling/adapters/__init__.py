"""
OSS generator adapters.

Concrete implementations of GeneratorAdapter for open-source BI tools.
Each adapter translates a tool-agnostic DashboardSpec (IR) into the
output format required by that tool.

Adapter status:
    MetabaseAdapter  — renders dashboard.json
    GrafanaAdapter   — renders dashboard.json
    SupersetAdapter  — renders dashboard_export.zip
    (Import into the live tools is not tested; 12.11.2026.)

Import pattern:
    from products.oss_adapters.tooling.adapters.metabase import MetabaseAdapter
    from products.oss_adapters.tooling.adapters.grafana import GrafanaAdapter
    from products.oss_adapters.tooling.adapters.superset import SupersetAdapter
"""
