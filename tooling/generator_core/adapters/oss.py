"""
OSS Stack Adapter — stub for open-source BI tool targets.

Supported targets (Phase 2+):
    metabase   — Metabase dashboard/card definitions via API
    grafana    — Grafana dashboard provisioning YAML
    superset   — Apache Superset chart + dashboard JSON
    redash     — Redash query + visualization JSON

The OSS adapter is a routing layer that delegates to the appropriate
sub-adapter based on the ``target`` parameter.  Sub-adapters are registered
via the ``register()`` class method so third parties can extend without
modifying this file.

Current state: stub.  All sub-adapters return a single README explaining
what would be generated.  Implement a sub-adapter by:

    1. Subclass OSSSubAdapter
    2. Implement visual_type_map(), _render_page(), _render_measures()
    3. Register: OSSAdapter.register("mytool", MySubAdapter)

Example
-------
    adapter = OSSAdapter(target="metabase")
    result = adapter.render(spec)
    result.write_to(Path("dist/"))
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from ..adapters.base import GeneratorAdapter, RenderResult
from ..ir.specs import AdapterTarget, DashboardSpec, VisualType


# ---------------------------------------------------------------------------
# Sub-adapter base
# ---------------------------------------------------------------------------

class OSSSubAdapter:
    """Base for concrete OSS sub-adapters."""

    name: str = "oss"

    def visual_type_map(self) -> Dict[VisualType, List[str]]:
        raise NotImplementedError

    def render(self, spec: DashboardSpec) -> RenderResult:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Stub sub-adapters
# ---------------------------------------------------------------------------

_STUB_README = """\
# {tool} adapter — stub

This adapter has not been implemented yet.

DashboardSpec received:
  use_case_id : {use_case_id}
  domain      : {domain}
  pages       : {pages}
  measures    : {measures}

To implement, subclass OSSSubAdapter and register it:

    from tooling.generator_core.adapters.oss import OSSAdapter, OSSSubAdapter

    class {tool_class}Adapter(OSSSubAdapter):
        name = "{tool_lower}"

        def visual_type_map(self):
            return {{ ... }}

        def render(self, spec):
            # ... return RenderResult(files={{...}})

    OSSAdapter.register("{tool_lower}", {tool_class}Adapter)
"""


class _MetabaseStub(OSSSubAdapter):
    name = "metabase"

    def visual_type_map(self) -> Dict[VisualType, List[str]]:
        return {
            VisualType.KPI_CARD:    ["scalar"],
            VisualType.TREND_LINE:  ["line"],
            VisualType.BAR_CHART:   ["bar"],
            VisualType.MATRIX:      ["pivot"],
            VisualType.TABLE:       ["table"],
            VisualType.WATERFALL:   ["waterfall"],
            VisualType.SCATTER:     ["scatter"],
        }

    def render(self, spec: DashboardSpec) -> RenderResult:
        readme = _STUB_README.format(
            tool="Metabase",
            tool_class="Metabase",
            tool_lower="metabase",
            use_case_id=spec.use_case_id,
            domain=spec.domain,
            pages=len(spec.pages),
            measures=len(spec.measures),
        )
        return RenderResult(
            files={"README_metabase_stub.md": readme.encode()},
            adapter="metabase",
            warnings=["Metabase adapter is a stub — output not renderable"],
        )


class _GrafanaStub(OSSSubAdapter):
    name = "grafana"

    def visual_type_map(self) -> Dict[VisualType, List[str]]:
        return {
            VisualType.KPI_CARD:    ["stat"],
            VisualType.TREND_LINE:  ["timeseries"],
            VisualType.BAR_CHART:   ["barchart"],
            VisualType.MATRIX:      ["table"],
            VisualType.TABLE:       ["table"],
            VisualType.SCATTER:     ["scatter"],
        }

    def render(self, spec: DashboardSpec) -> RenderResult:
        readme = _STUB_README.format(
            tool="Grafana",
            tool_class="Grafana",
            tool_lower="grafana",
            use_case_id=spec.use_case_id,
            domain=spec.domain,
            pages=len(spec.pages),
            measures=len(spec.measures),
        )
        return RenderResult(
            files={"README_grafana_stub.md": readme.encode()},
            adapter="grafana",
            warnings=["Grafana adapter is a stub — output not renderable"],
        )


class _SupersetStub(OSSSubAdapter):
    name = "superset"

    def visual_type_map(self) -> Dict[VisualType, List[str]]:
        return {
            VisualType.KPI_CARD:    ["big_number_total"],
            VisualType.TREND_LINE:  ["echarts_timeseries_line"],
            VisualType.BAR_CHART:   ["echarts_bar"],
            VisualType.MATRIX:      ["pivot_table_v2"],
            VisualType.TABLE:       ["table"],
            VisualType.SCATTER:     ["echarts_scatter"],
            VisualType.WATERFALL:   ["waterfall"],
        }

    def render(self, spec: DashboardSpec) -> RenderResult:
        readme = _STUB_README.format(
            tool="Superset",
            tool_class="Superset",
            tool_lower="superset",
            use_case_id=spec.use_case_id,
            domain=spec.domain,
            pages=len(spec.pages),
            measures=len(spec.measures),
        )
        return RenderResult(
            files={"README_superset_stub.md": readme.encode()},
            adapter="superset",
            warnings=["Superset adapter is a stub — output not renderable"],
        )


# ---------------------------------------------------------------------------
# Router / OSS Adapter
# ---------------------------------------------------------------------------

_REGISTRY: Dict[str, Type[OSSSubAdapter]] = {
    "metabase": _MetabaseStub,
    "grafana":  _GrafanaStub,
    "superset": _SupersetStub,
}


class OSSAdapter(GeneratorAdapter):
    """
    Routes to the appropriate OSS sub-adapter based on the target name.

    Parameters
    ----------
    target
        One of: "metabase", "grafana", "superset", or any registered name.
    """

    def __init__(self, target: str = "metabase") -> None:
        cls = _REGISTRY.get(target)
        if not cls:
            available = ", ".join(_REGISTRY)
            raise ValueError(
                f"Unknown OSS adapter target '{target}'. "
                f"Available: {available}"
            )
        self._delegate: OSSSubAdapter = cls()
        self._target_name = target

    @classmethod
    def register(cls, target_name: str, sub_adapter_cls: Type[OSSSubAdapter]) -> None:
        """Register a custom sub-adapter so it is available by target name."""
        _REGISTRY[target_name] = sub_adapter_cls

    @classmethod
    def available_targets(cls) -> List[str]:
        return list(_REGISTRY.keys())

    @property
    def name(self) -> str:
        return f"oss/{self._target_name}"

    @property
    def target(self) -> AdapterTarget:
        # All OSS targets share a single enum value for now
        return AdapterTarget.METABASE

    def visual_type_map(self) -> Dict[VisualType, List[str]]:
        return self._delegate.visual_type_map()

    def validate_ir(self, spec: DashboardSpec) -> List[str]:
        errors: List[str] = []
        if not spec.pages:
            errors.append("DashboardSpec has no pages")
        if not spec.measures and self._target_name not in ("grafana",):
            # Grafana is metric-based, not measure-based
            errors.append("DashboardSpec has no measures")
        return errors

    def render(self, spec: DashboardSpec) -> RenderResult:
        return self._delegate.render(spec)
