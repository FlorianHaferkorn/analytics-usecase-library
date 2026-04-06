"""
OSS-specific validation helpers.

Mirrors products/fabric/powerbi/tooling/validation/ in structure.

Planned checks:
    - validate_metabase_export()  — verify dashboard.json structure
    - validate_grafana_export()   — verify panel types and data source refs
    - validate_superset_export()  — verify ZIP structure and YAML schema

These are OSS-specific checks that complement the shared PreflightValidator
in tooling/generator_core/preflight/. The shared preflight runs BEFORE
generation (bracket-level checks); these run AFTER generation (output checks).
"""
