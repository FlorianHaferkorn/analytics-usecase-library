"""targets.tmdl — TMDL semantic-model emitter (concrete target adapter, task I-3.2).

First concrete adapter on the I-3.1 contract (ADR-0006): emits a Power BI **TMDL**
semantic model FROM the canonical model — one `<table>.tmdl` per table under
`<Model>.SemanticModel/definition/tables/`, plus (since 07.10.2026) the item frame that
makes the folder a semantic model Power BI Desktop can open, in the Microsoft layout
(Learn, "Power BI Desktop project semantic model folder" / "TMDL folder structure"):
`definition.pbism` (required), `.platform`, `definition/database.tmdl`,
`definition/model.tmdl`, `definition/relationships.tmdl` (when the model has any), and a
partition per table. `database`/`model`/`pbism` are rendered from the governed base
templates in `core/strategy_operating_model/operating_model/reference/tmdl_base_templates/`
(the same source `table_ops.ps1 -Operation WriteModelFiles` uses — reused, not copied).

Partitions: a table whose canonical model carries an `m_expression` gets it verbatim;
every other table gets an **empty typed table** (`#table(type table [...], {})`) — the
model opens and refreshes with 0 rows, no data source is invented. Binding the real
source (Import vs Direct Lake, Gold path, `source_column` renames) is the delivery
connector's decision and is listed by `datasource_gaps()`. A table without columns
(the `_Measures` home) gets the hidden `Column1` the legacy models use.

This is the **stack step where dialect/DAX is materialized** (Invariant I1: the
source adapter `from_aluca` stays dialect-neutral; DAX is filled HERE). ALUCA defines
*meaning*, not DAX (Golden Thread). Three dialect sources are tried, in order:

  1. `measure.expressions['dax']` / `measure.expression` — a real dialect override,
     used verbatim (unchanged from before I-10.0).
  2. `measure.expressions['dsl']` — the governed, stack-neutral formula resolved by
     `from_aluca` from the KPI catalog's `technical.calculation` (I-10.0 / Cut S-1);
     synthesized into real DAX HERE, deterministically, via `dax_synth.synthesize_dax`
     (never on the source-adapter side — I1).
  3. Neither present → a deterministic HITL placeholder (`BLANK()` + a `/// HITL:`
     comment carrying the SPECIFIC reason from `expressions['hitl_reason']` when one
     was recorded, else the generic "no catalog entry / no dialect" comment) —
     mirroring ALUCA's BracketCompiler (missing → BLANK()/warning). This placeholder
     is never silent: every occurrence carries a diagnosable `/// HITL:` reason, and
     `hitl_gaps()` below counts them for the ledger (Review Befund A1: "gezählt,
     nicht still BLANK()").

TMDL hard-rules (AGENTS.md, enforced by `.claude/hooks/validate_tmdl_style.sh`):
  - TABS only (never leading spaces)
  - DAX assignment `=` (never `:=`)
  - measure docs as `/// Purpose:` comment (never a `description:` property)
  - numeric columns carry `summarizeBy`; measures carry `formatString` when known
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.targets import dax_synth
from tooling.superversion.targets.base import TargetAdapter, register

TAB = "\t"

_TEMPLATES = (Path(__file__).resolve().parents[3] / "core" / "strategy_operating_model"
              / "operating_model" / "reference" / "tmdl_base_templates")
#: Culture of the governed WriteModelFiles path (`table_ops.ps1 -Culture`, default de-DE).
#: The canonical model carries no culture; this is the repo's documented default, not a guess.
DEFAULT_CULTURE = "de-DE"
_PLATFORM_SCHEMA = ("https://developer.microsoft.com/json-schemas/fabric/gitIntegration/"
                    "platformProperties/2.0.0/schema.json")
_BARE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
#: TOM data type → Power Query type used in the placeholder partition's table type.
_M_TYPE = {
    "int64": "Int64.Type",
    "double": "number",
    "decimal": "Currency.Type",
    "boolean": "logical",
    "string": "text",
    "datetime": "datetime",
}
_PLACEHOLDER_COLUMN = "Column1"

_GENERIC_HITL_REASON = "define DAX dialect (ALUCA carries meaning, not DAX)"


def _dax_for(measure) -> tuple[str, bool]:
    """(dax_expression, is_placeholder). Uses a real dialect when present, else
    synthesizes DAX from the governed DSL formula (I-10.0), else a deterministic
    HITL placeholder. Never emits ':=' (TMDL hard-rule)."""
    exprs = getattr(measure, "expressions", None) or {}
    dialect = exprs.get("dax", "")
    if dialect:
        return dialect.strip(), False
    if measure.expression:
        return measure.expression.strip(), False
    dsl = exprs.get("dsl", "")
    if dsl:
        try:
            resolved = json.loads(dsl)
            return dax_synth.synthesize_dax(resolved), False
        except (ValueError, dax_synth.SynthesisError):
            pass  # malformed DSL payload — fall through to the HITL placeholder
    return "BLANK()", True


def _hitl_reason(measure) -> str:
    return (getattr(measure, "expressions", None) or {}).get("hitl_reason") or _GENERIC_HITL_REASON


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
        lines.append(f"{TAB}/// HITL: {_one_line(_hitl_reason(measure))}")
    lines.append(f"{TAB}measure {_measure_name_literal(measure.name)} = {dax}")
    if measure.display_folder:
        lines.append(f"{TAB}{TAB}displayFolder: '{measure.display_folder}'")
    if measure.format_string:
        lines.append(f'{TAB}{TAB}formatString: "{measure.format_string}"')
    if getattr(measure, "is_hidden", False):
        lines.append(f"{TAB}{TAB}isHidden")
    return lines


def quote_name(name: str) -> str:
    """TMDL object name: bare when it is a plain identifier, else single-quoted with
    embedded quotes doubled (`'OTIF Flag'`, `'SCM-002_x'`)."""
    if _BARE_NAME.fullmatch(name):
        return name
    return "'" + name.replace("'", "''") + "'"


def _render_column(column) -> list[str]:
    lines: list[str] = []
    doc = _one_line(getattr(column, "description", ""))
    if doc:
        lines.append(f"{TAB}/// {doc}")
    lines.append(f"{TAB}column {quote_name(column.name)}")
    if column.data_type:
        lines.append(f"{TAB}{TAB}dataType: {column.data_type}")
    if getattr(column, "is_hidden", False):
        lines.append(f"{TAB}{TAB}isHidden")
    if not getattr(column, "expression", ""):
        lines.append(f"{TAB}{TAB}sourceColumn: {column.name}")
    # numeric columns must carry summarizeBy (hard-rule); default to none if unset
    lines.append(f"{TAB}{TAB}summarizeBy: {column.summarize_by or 'none'}")
    return lines


def _m_field(name: str) -> str:
    return '#"' + name.replace('"', '""') + '"'


def _partition_source(table, columns) -> str:
    if getattr(table, "m_expression", ""):
        return table.m_expression.strip()
    fields = ", ".join(
        f"{_m_field(c.name)} = {_M_TYPE.get((c.data_type or '').lower(), 'text')}"
        for c in columns if not getattr(c, "expression", "")
    )
    return f"let\n\tSource = #table(type table [{fields}], {{}})\nin\n\tSource"


def _render_partition(table, columns) -> list[str]:
    lines: list[str] = []
    if not getattr(table, "m_expression", ""):
        lines.append(f"{TAB}/// HITL: placeholder partition (empty typed table, 0 rows) — "
                     "bind the data source in delivery")
    lines += [f"{TAB}partition {quote_name(table.name)} = m", f"{TAB}{TAB}mode: import",
              f"{TAB}{TAB}source ="]
    lines += [f"{TAB}{TAB}{TAB}{line}" for line in _partition_source(table, columns).splitlines()]
    return lines


def _emitted_columns(table) -> list:
    """The table's columns; a column-less table (measure home) gets the hidden `Column1`
    the legacy `_Measures` tables carry — TOM needs a column for an import partition."""
    if table.columns:
        return list(table.columns)
    from tooling.superversion.canonical_contract import Column
    return [Column(name=_PLACEHOLDER_COLUMN, data_type="string", is_hidden=True)]


def render_table(table) -> str:
    """Render one table to TMDL text (tabs, hard-rule compliant)."""
    blocks: list[str] = []
    doc = _one_line(getattr(table, "description", ""))
    if doc:
        blocks.append(f"/// {doc}")
    blocks.append(f"table {quote_name(table.name)}")
    columns = _emitted_columns(table)
    for col in columns:
        blocks.append("")
        blocks.extend(_render_column(col))
    for measure in table.measures:
        blocks.append("")
        blocks.extend(_render_measure(measure))
    blocks.append("")
    blocks.extend(_render_partition(table, columns))
    return "\n".join(blocks) + "\n"


def _template(name: str) -> str:
    return (_TEMPLATES / name).read_text(encoding="utf-8")


def _column_ref(table: str, column: str) -> str:
    return f"{quote_name(table)}.{quote_name(column)}"


def render_relationships(relationships) -> str:
    blocks: list[str] = []
    for rel in relationships:
        name = f"{rel.from_table}_{rel.from_column}_{rel.to_table}"
        if blocks:
            blocks.append("")
        blocks.append(f"relationship {quote_name(name)}")
        if not rel.is_active:
            blocks.append(f"{TAB}isActive: false")
        if rel.cross_filter:
            blocks.append(f"{TAB}crossFilteringBehavior: {rel.cross_filter}")
        blocks.append(f"{TAB}fromColumn: {_column_ref(rel.from_table, rel.from_column)}")
        blocks.append(f"{TAB}toColumn: {_column_ref(rel.to_table, rel.to_column)}")
    return "\n".join(blocks) + "\n"


def emit(canonical: CanonicalModel) -> dict[str, str]:
    """Canonical model → {path: TMDL content}. Deterministic (Invariant I2)."""
    model = canonical.semantic
    item = f"{model.name}.SemanticModel"
    base = f"{item}/definition/tables"
    out: dict[str, str] = {}
    out[f"{item}/.platform"] = json.dumps({
        "$schema": _PLATFORM_SCHEMA,
        "metadata": {"type": "SemanticModel", "displayName": model.name},
        # Nullkennung wie im PBIR-Target: vergeben wird beim Import, eine erfundene GUID
        # kollidiert beim naechsten.
        "config": {"version": "2.0", "logicalId": "00000000-0000-0000-0000-000000000000"},
    }, indent=2, ensure_ascii=False) + "\n"
    out[f"{item}/definition.pbism"] = _template("definition.pbism.template").rstrip() + "\n"
    database = _template("database.tmdl.template").replace("{{MODEL_NAME}}", quote_name(model.name))
    if model.compatibility_level:
        database = re.sub(r"compatibilityLevel: \d+",
                          f"compatibilityLevel: {model.compatibility_level}", database)
    out[f"{item}/definition/database.tmdl"] = database.rstrip() + "\n"
    model_tmdl = _template("model.tmdl.template").replace("{{CULTURE}}", DEFAULT_CULTURE).rstrip()
    refs = "\n".join(f"ref table {quote_name(t.name)}" for t in model.tables)
    out[f"{item}/definition/model.tmdl"] = model_tmdl + "\n" + (f"\n{refs}\n" if refs else "")
    if model.relationships:
        out[f"{item}/definition/relationships.tmdl"] = render_relationships(model.relationships)
    for table in model.tables:
        out[f"{base}/{table.name}.tmdl"] = render_table(table)
    return out


def table_files(emitted: dict[str, str]) -> dict[str, str]:
    """Only the `definition/tables/*.tmdl` entries of an `emit()` result."""
    return {k: v for k, v in emitted.items() if "/definition/tables/" in k}


def datasource_gaps(canonical: CanonicalModel) -> list[str]:
    """Tables whose partition is the empty placeholder (no `m_expression`): the data
    source is a delivery decision, not something ALUCA carries."""
    return [f"{t.name}: placeholder partition (0 rows) — bind the data source in delivery"
            for t in canonical.semantic.tables if not getattr(t, "m_expression", "")]


def hitl_gaps(canonical: CanonicalModel) -> list[str]:
    """Human-in-the-loop gaps in the emitted TMDL (measures with no derivable DAX —
    either no `technical.calculation` was authored, or it is an explicit `op: hitl`
    marker) — for the E2E run / ledger (mirrors `targets/pbir.py::hitl_gaps`).

    Every entry here is an explicit, diagnosable gap (Review Befund A1: "gezählt,
    nicht still BLANK()"), never a silent one — each corresponds 1:1 to a
    `/// HITL: <reason>` comment in the emitted TMDL."""
    gaps: list[str] = []
    for table in canonical.semantic.tables:
        for measure in table.measures:
            _, is_placeholder = _dax_for(measure)
            if is_placeholder:
                gaps.append(f"{table.name}.{measure.name}: {_hitl_reason(measure)}")
    return gaps


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
