"""targets.tmdl — TMDL semantic-model emitter (concrete target adapter, task I-3.2).

First concrete adapter on the I-3.1 contract (ADR-0006): emits a Power BI **TMDL**
semantic model FROM the canonical model — one `<table>.tmdl` per table under
`<Model>.SemanticModel/definition/tables/`.

This is the **stack step where dialect/DAX is materialized** (Invariant I1: the
source adapter `from_aluca` stays dialect-neutral; DAX is filled HERE). ALUCA defines
*meaning*, not DAX (Golden Thread), so when a measure carries no dialect we emit a
deterministic HITL placeholder (`BLANK()` + a `/// HITL:` marker) rather than invent
business logic — mirroring ALUCA's BracketCompiler (missing → BLANK()/warning). A real
DAX dialect, when present in `measure.expressions['dax']` (or `measure.expression`), is
used verbatim.

TMDL hard-rules (AGENTS.md, enforced by `.claude/hooks/validate_tmdl_style.sh`):
  - TABS only (never leading spaces)
  - DAX assignment `=` (never `:=`)
  - measure docs as `/// Purpose:` comment (never a `description:` property)
  - numeric columns carry `summarizeBy`; measures carry `formatString` when known
"""
from __future__ import annotations

from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.targets.base import TargetAdapter, register

TAB = "\t"


def _dax_for(measure) -> tuple[str, bool]:
    """(dax_expression, is_placeholder). Uses a real dialect when present; else a
    deterministic HITL placeholder. Never emits ':=' (TMDL hard-rule)."""
    dialect = (getattr(measure, "expressions", None) or {}).get("dax", "")
    if dialect:
        return dialect.strip(), False
    if measure.expression:
        return measure.expression.strip(), False
    return "BLANK()", True


def _one_line(text: str) -> str:
    """Collapse to a single line for a `///` doc comment (no embedded newlines)."""
    return " ".join((text or "").split())


def _measure_name_literal(name: str) -> str:
    # TMDL measure names are quoted; our KPI measure names contain no single quotes.
    return f"'{name}'"


def _render_measure(measure) -> list[str]:
    lines: list[str] = []
    purpose = _one_line(measure.description)
    if purpose:
        lines.append(f"{TAB}/// Purpose: {purpose}")
    dax, is_placeholder = _dax_for(measure)
    if is_placeholder:
        lines.append(f"{TAB}/// HITL: define DAX dialect (ALUCA carries meaning, not DAX)")
    lines.append(f"{TAB}measure {_measure_name_literal(measure.name)} = {dax}")
    if measure.display_folder:
        lines.append(f"{TAB}{TAB}displayFolder: '{measure.display_folder}'")
    if measure.format_string:
        lines.append(f'{TAB}{TAB}formatString: "{measure.format_string}"')
    if getattr(measure, "is_hidden", False):
        lines.append(f"{TAB}{TAB}isHidden")
    return lines


def _render_column(column) -> list[str]:
    lines = [f"{TAB}column {column.name}"]
    if column.data_type:
        lines.append(f"{TAB}{TAB}dataType: {column.data_type}")
    if getattr(column, "is_hidden", False):
        lines.append(f"{TAB}{TAB}isHidden")
    # numeric columns must carry summarizeBy (hard-rule); default to none if unset
    lines.append(f"{TAB}{TAB}summarizeBy: {column.summarize_by or 'none'}")
    return lines


def render_table(table) -> str:
    """Render one table to TMDL text (tabs, hard-rule compliant)."""
    blocks: list[str] = [f"table {table.name}"]
    for col in table.columns:
        blocks.append("")
        blocks.extend(_render_column(col))
    for measure in table.measures:
        blocks.append("")
        blocks.extend(_render_measure(measure))
    return "\n".join(blocks) + "\n"


def emit(canonical: CanonicalModel) -> dict[str, str]:
    """Canonical model → {path: TMDL content}. Deterministic (Invariant I2)."""
    model = canonical.semantic
    base = f"{model.name}.SemanticModel/definition/tables"
    out: dict[str, str] = {}
    for table in model.tables:
        out[f"{base}/{table.name}.tmdl"] = render_table(table)
    return out


# Register the adapter. Marked `live` only once it passes the official validator
# (premium floor F1); the TMDL hook + parse round-trip are the gates today.
register(TargetAdapter(
    id="tmdl",
    label="Power BI semantic model (TMDL)",
    fmt="tmdl",
    emit=emit,
    data_platform="Fabric/Power BI",
    visualization="Power BI",
    status="geplant",
))
