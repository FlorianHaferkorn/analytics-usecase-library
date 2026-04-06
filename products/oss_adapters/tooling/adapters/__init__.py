"""
OSS generator adapters.

Concrete implementations of GeneratorAdapter for open-source BI tools.
Each adapter translates a tool-agnostic DashboardSpec (IR) into the
output format required by that tool.

Adapter status:
    MetabaseAdapter  — stub (not yet implemented)
    GrafanaAdapter   — stub (not yet implemented)
    SupersetAdapter  — stub (not yet implemented)

Import pattern (once implemented):
    from products.oss.tooling.adapters.metabase import MetabaseAdapter
    from products.oss.tooling.adapters.grafana import GrafanaAdapter
    from products.oss.tooling.adapters.superset import SupersetAdapter
"""
