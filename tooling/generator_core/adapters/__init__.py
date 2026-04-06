"""
generator_core adapters — only the abstract base lives here.

Concrete implementations belong to their respective product directories:
  products/fabric/powerbi/tooling/adapters/pbip.py  → PBIPAdapter
  products/oss/tooling/adapters/metabase.py          → MetabaseAdapter
  products/oss/tooling/adapters/grafana.py            → GrafanaAdapter
  products/oss/tooling/adapters/superset.py           → SupersetAdapter
"""
from .base import GeneratorAdapter, RenderResult
