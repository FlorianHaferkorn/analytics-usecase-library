"""naming — the single, documented Fabric naming convention (ADR-0015 follow-up).

"Pick the pattern, document it, enforce it." One `NamingConvention` that every emitter
consults, so names are consistent and best-practice-aligned across the whole system.

Grounded in Microsoft + community guidance (research 2026-07-15 §naming):
- **Type prefixes** for Fabric *items* (not data tables): lh_ lakehouse, dw_ warehouse,
  pl_ pipeline, nb_ notebook, df_ dataflow, sm_ semantic model, rpt_ report, cj_ copy job,
  eh_ eventhouse. Applied to the base name, base casing preserved (house style).
- **Workspace stage suffix**: non-prod gets ` [Dev]` / ` [Test]`; prod (or unset) gets none.
- **Medallion index** (optional, default off): 100/200/300 bands for bronze/silver/gold,
  3-digit spacing so intermediate stages can be inserted later.
- Data *table* names keep their layer/semantic prefixes (fact_/dim_/agg_, silver_/bronze_) —
  those are not Fabric items and are already conventioned.

Applied at the emit boundary (CLI) so the shared IR contract is untouched.
"""
from __future__ import annotations

from dataclasses import dataclass

# Fabric item type → prefix (community-standard).
_PREFIX = {
    "lakehouse": "lh_", "warehouse": "dw_", "pipeline": "pl_", "notebook": "nb_",
    "dataflow": "df_", "semantic_model": "sm_", "report": "rpt_", "copy_job": "cj_",
    "eventhouse": "eh_",
}
_STAGE_SUFFIX = {"dev": " [Dev]", "test": " [Test]", "prod": "", None: ""}
_LAYER_BAND = {"bronze": "100", "silver": "200", "gold": "300"}


@dataclass(frozen=True)
class NamingConvention:
    """Configurable naming rules. Defaults follow the agreed house convention."""
    apply_type_prefixes: bool = True
    stage: str | None = None          # dev | test | prod | None
    medallion_index: bool = False

    # --- items -----------------------------------------------------------------
    def _item(self, kind: str, base: str) -> str:
        if not base:
            return base
        pre = _PREFIX.get(kind, "") if self.apply_type_prefixes else ""
        return base if base.startswith(pre) and pre else f"{pre}{base}"

    def lakehouse(self, base: str, layer: str = "gold") -> str:
        name = self._item("lakehouse", base)
        if self.medallion_index and layer in _LAYER_BAND and self.apply_type_prefixes:
            # lh_300_gold — band sits after the prefix
            return name.replace("lh_", f"lh_{_LAYER_BAND[layer]}_", 1)
        return name

    def warehouse(self, base: str) -> str:
        return self._item("warehouse", base)

    def pipeline(self, base: str) -> str:
        return self._item("pipeline", base)

    def notebook(self, base: str) -> str:
        return self._item("notebook", base)

    def copy_job(self, base: str) -> str:
        return self._item("copy_job", base)

    def semantic_model(self, base: str) -> str:
        return self._item("semantic_model", base)

    def report(self, base: str) -> str:
        return self._item("report", base)

    # --- workspaces ------------------------------------------------------------
    def stage_suffix(self) -> str:
        return _STAGE_SUFFIX.get(self.stage, "")

    def workspace(self, base: str) -> str:
        """Append the non-prod stage suffix; prod/unset unchanged. Idempotent."""
        suffix = self.stage_suffix()
        if not base or not suffix or base.endswith(suffix):
            return base
        return f"{base}{suffix}"

    # --- tables (unchanged: keep semantic/layer prefixes) ----------------------
    def layer_band(self, layer: str) -> str:
        """Medallion band for a layer, '' when the index is off."""
        return _LAYER_BAND.get(layer, "") if self.medallion_index else ""


DEFAULT = NamingConvention()


def layer_ref(layer: str, name: str, schemas: bool = False) -> str:
    """Reference a layer table: ``gold.fact_x`` in a schema-enabled lakehouse, else ``gold_fact_x``.

    Schema-enabled lakehouses (creationPayload.enableSchemas) put the medallion layer in a real
    SQL schema (gold/silver/bronze) instead of the default ``dbo`` namespace + a name prefix.
    """
    return f"{layer}.{name}" if schemas else f"{layer}_{name}"
