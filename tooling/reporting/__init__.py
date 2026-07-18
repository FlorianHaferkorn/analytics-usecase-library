"""tooling/reporting — tool-agnostic reporting decisions (format, semantic, target, title).

The governed, viz-tool-NEUTRAL base every renderer consumes: Power BI (via the CLI adapters in
products/fabric/powerbi), Databricks AI/BI, React, etc. This layer never imports a product/target;
targets import from here (ADR-0006 adapter direction).
"""
