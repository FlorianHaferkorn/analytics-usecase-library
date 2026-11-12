"""
generator_core adapters — only the abstract base lives here.

Concrete implementations belong to their respective product directories:
  products/fabric/powerbi/tooling/adapters/pbip.py  → PBIPAdapter
  products/oss_adapters/tooling/adapters/metabase.py          → MetabaseAdapter
  products/oss_adapters/tooling/adapters/grafana.py            → GrafanaAdapter
  products/oss_adapters/tooling/adapters/superset.py           → SupersetAdapter
"""
from .base import GeneratorAdapter, RenderResult
