"""contract_binding — bind the canonical model to its data contract (I-3 delivery step).

``from_aluca`` builds the canonical model from the bracket and the KPI catalog. Both
carry *meaning*: which KPIs, which visuals, which fields. Neither carries the physical
star schema — the plan says so explicitly (UMSETZUNGSPLAN_SUPERVERSION §I-1, "bewusst
nicht: Relationships aus Brackets ableiten — gehören in Stack/data_contracts, → I-3").
Until 07.10.2026 nothing took that step, so the Power BI output was four measure-only
TMDL files: no columns, no dimensions, no relationships — not openable in Desktop.

This module is that step. It reads the bracket's ``overrides.data_contract_ref`` in its
domain view (``tooling.utils.data_contracts.load_resolved_contract`` — the Bus-Matrix
resolver, reused, not rebuilt) and adds to a *copy* of the canonical model:

* the contract columns of every fact table the KPIs already route to,
* every dimension a fact column references (``ref``) with its domain-view columns,
* one relationship per foreign key (fact ``ref`` column → the dimension's ``role: key``),
* qualified visual fields where the contract answers the question unambiguously.

Derived, never invented. Every decision is returned as a :class:`BindingFinding`:

* ``resolved``  — an unqualified bracket field matched exactly one dimension column
  (case-insensitive name), or a date axis the governed idiom demands
  (``visual_idioms.category_axis_type == "date"``) matched exactly one ``date`` column.
* ``widened``   — the bracket binds a column of a conformed dimension that the domain
  view (``uses_columns``) leaves out, but the one owning definition carries; the column is
  added and the deviation reported so the contract can be corrected.
* ``moved``     — a measure shares its name with a column of its host table (TOM rejects
  that); it moves to ``_Measures``, as the legacy SupplyChain model does.
* ``gap``       — the contract does not answer: the field stays unresolved and the PBIR
  emitter shows a HITL placeholder with this reason.

Columns marked ``target_state: true`` are skipped: the contract README defines them as
"not (yet) delivered … or read by a model". A relationship over such a key would bind a
column no data source fills.
"""
from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from tooling.superversion.canonical_contract import (
    CanonicalModel,
    Column,
    Relationship,
    Table,
)
from tooling.utils.data_contracts import (
    CONFORMED_FROM,
    load_contracts,
    load_resolved_contract,
    owners,
)

_REPO = Path(__file__).resolve().parents[2]
_MEASURES = "_Measures"

#: Contract column type → TOM data type (the vocabulary the canonical ``Column.data_type``
#: carries, as parsed from TMDL by the vendored Meridian parser).
_TYPE_MAP = {
    "int": "int64",
    "decimal": "double",
    "currency": "decimal",
    "boolean": "boolean",
    "bool": "boolean",
    "text": "string",
    "date": "dateTime",
    "datetime": "dateTime",
}
#: Contract ``agg`` → TOM ``summarizeBy``. Anything else (keys, flags, labels) is ``none``.
_AGG_MAP = {"sum": "sum", "avg": "average", "min": "min", "max": "max", "count": "count"}

_DAX_COLUMN_REF = re.compile(r"(?:'([^']+)'|\b([A-Za-z_][A-Za-z0-9_]*))\[([^\]]+)\]")


@dataclass(frozen=True)
class BindingFinding:
    kind: str     # resolved | widened | moved | gap
    detail: str

    def __str__(self) -> str:
        return f"{self.kind}: {self.detail}"


def contract_ref(bracket: dict) -> Optional[str]:
    """The bracket's declared data contract (``overrides.data_contract_ref``), or None."""
    ref = ((bracket or {}).get("overrides") or {}).get("data_contract_ref")
    return ref if isinstance(ref, str) and ref.strip() else None


def resolve_contract_path(ref: str, bracket_path: Optional[Path] = None) -> Path:
    """Repo-relative first (the convention of all 22 brackets), else bracket-relative."""
    candidate = _REPO / ref
    if candidate.is_file() or bracket_path is None:
        return candidate
    return Path(bracket_path).parent / ref


def _columns_of(table: dict) -> list[dict]:
    return [c for c in table.get("columns") or [] if isinstance(c, dict) and c.get("name")]


def _key_of(table: dict) -> Optional[str]:
    return next((c["name"] for c in _columns_of(table) if c.get("role") == "key"), None)


def _column(spec: dict, findings: list[BindingFinding], table: str) -> Optional[Column]:
    data_type = _TYPE_MAP.get(str(spec.get("type") or "").lower())
    if data_type is None:
        findings.append(BindingFinding(
            "gap", f"{table}.{spec['name']}: contract type '{spec.get('type')}' has no "
                   "TOM data type mapping — column left out"))
        return None
    is_key = spec.get("role") == "key" or bool(spec.get("ref"))
    return Column(
        name=spec["name"],
        data_type=data_type,
        is_hidden=is_key,
        description=str(spec.get("description") or ""),
        summarize_by=_AGG_MAP.get(str(spec.get("agg") or "").lower(), "none"),
    )


def _delivered(spec: dict) -> bool:
    return spec.get("target_state") is not True


def _add_columns(table: Table, specs: list[dict], findings: list[BindingFinding]) -> None:
    present = {c.name for c in table.columns}
    for spec in specs:
        if spec["name"] in present or not _delivered(spec):
            continue
        col = _column(spec, findings, table.name)
        if col is not None:
            table.columns.append(col)
            present.add(col.name)


def _dimension_columns(model: CanonicalModel, dim_names: set[str]) -> list[tuple[str, Column]]:
    return [(t.name, c) for t in model.semantic.tables if t.name in dim_names for c in t.columns]


def _resolve_unqualified(field: str, model: CanonicalModel, dim_names: set[str]) -> list[str]:
    wanted = field.strip().lower()
    return [f"{t}.{c.name}" for t, c in _dimension_columns(model, dim_names)
            if c.name.lower() == wanted and not c.is_hidden]


def _owner_columns(contract_path: Path) -> dict[str, list[dict]]:
    """Full column list of every owning (non-reference) table among the contract's siblings."""
    return {name: _columns_of(table)
            for name, (_dom, _sec, table) in owners(load_contracts(contract_path.parent)).items()}


def bind(model: CanonicalModel, contract_path: Path) -> tuple[CanonicalModel, list[BindingFinding]]:
    """Return a copy of ``model`` bound to the contract, plus every decision taken."""
    bound = copy.deepcopy(model)
    findings: list[BindingFinding] = []
    contract = load_resolved_contract(contract_path)
    facts = {t["name"]: t for t in contract.get("fact") or [] if isinstance(t, dict) and t.get("name")}
    dims = {t["name"]: t for t in contract.get("dimension") or []
            if isinstance(t, dict) and t.get("name")}
    sm = bound.semantic
    by_name = {t.name: t for t in sm.tables}

    # 1 — facts the KPIs already route to get their delivered contract columns.
    for table in list(sm.tables):
        spec = facts.get(table.name) or dims.get(table.name)
        if spec is None:
            if table.name != _MEASURES:
                findings.append(BindingFinding(
                    "gap", f"table '{table.name}' is not a table of {contract_path.name} — "
                           "no columns, no relationships"))
            continue
        if not table.description:
            table.description = str(spec.get("description") or "")
        _add_columns(table, _columns_of(spec), findings)

    # 2 — every delivered foreign key pulls in its dimension and one relationship.
    dim_names: set[str] = set()
    for table in list(sm.tables):
        spec = facts.get(table.name)
        if spec is None:
            continue
        for col in _columns_of(spec):
            target = col.get("ref")
            if not target:
                continue
            if not _delivered(col):
                findings.append(BindingFinding(
                    "gap", f"{table.name}.{col['name']} → {target}: key is target_state "
                           "(not delivered) — dimension and relationship left out"))
                continue
            dim_spec = dims.get(target)
            key = _key_of(dim_spec) if dim_spec else None
            if dim_spec is None or key is None:
                findings.append(BindingFinding(
                    "gap", f"{table.name}.{col['name']} → {target}: dimension or its "
                           "role: key column not in the contract"))
                continue
            dim = by_name.get(target)
            if dim is None:
                dim = Table(name=target, description=str(dim_spec.get("description") or ""))
                _add_columns(dim, _columns_of(dim_spec), findings)
                sm.tables.append(dim)
                by_name[target] = dim
            dim_names.add(target)
            sm.relationships.append(Relationship(
                from_table=table.name, from_column=col["name"],
                to_table=target, to_column=key,
            ))

    # 3 — measure names must not collide with a column of their host table (TOM).
    for table in list(sm.tables):
        col_names = {c.name for c in table.columns}
        clashing = [m for m in table.measures if m.name in col_names]
        if not clashing:
            continue
        host = by_name.get(_MEASURES)
        if host is None:
            host = Table(name=_MEASURES)
            sm.tables.append(host)
            by_name[_MEASURES] = host
        for m in clashing:
            table.measures.remove(m)
            host.measures.append(m)
            findings.append(BindingFinding(
                "moved", f"measure '{m.name}' {table.name} → {_MEASURES} "
                         f"(column '{table.name}[{m.name}]' has the same name)"))

    # 4 — visual fields.
    owner_cols: Optional[dict[str, list[dict]]] = None
    from tooling.superversion.layer_tools.visual_idioms import category_axis_type

    for page in bound.report.pages:
        for visual in page.visuals:
            vid = f"{page.name}/{visual.visual_id}"
            for attr in ("rows", "columns"):
                fields = getattr(visual, attr)
                for i, field in enumerate(list(fields)):
                    if "." in field:
                        t_name, c_name = field.rsplit(".", 1)
                        table = by_name.get(t_name)
                        if table is not None and any(c.name == c_name for c in table.columns):
                            continue
                        if owner_cols is None:
                            owner_cols = _owner_columns(contract_path)
                        spec = next((c for c in owner_cols.get(t_name, [])
                                     if c["name"] == c_name and _delivered(c)), None)
                        if table is not None and spec is not None and t_name in dims \
                                and dims[t_name].get(CONFORMED_FROM):
                            col = _column(spec, findings, t_name)
                            if col is not None:
                                table.columns.append(col)
                                findings.append(BindingFinding(
                                    "widened", f"{vid}: '{field}' is not in the "
                                               f"{contract_path.stem} view of {t_name} "
                                               f"(uses_columns) but in its owning definition "
                                               f"({dims[t_name][CONFORMED_FROM]}) — added; "
                                               "add it to uses_columns or change the bracket"))
                            continue
                        findings.append(BindingFinding(
                            "gap", f"{vid}: '{field}' has no column in the bound model"))
                        continue
                    hits = _resolve_unqualified(field, bound, dim_names)
                    if len(hits) == 1:
                        fields[i] = hits[0]
                        findings.append(BindingFinding(
                            "resolved", f"{vid}: '{field}' → {hits[0]} (only dimension "
                                        "column of that name)"))
                    else:
                        why = (f"ambiguous: {', '.join(sorted(hits))}" if hits else
                               "no dimension column of that name reachable from the facts")
                        findings.append(BindingFinding("gap", f"{vid}: '{field}' — {why}"))

            if visual.rows or visual.columns or visual.slicer_field:
                continue
            if category_axis_type(visual.visual_type) != "date":
                continue
            date_cols = [
                f"{t.name}.{c.name}" for t in sm.tables if t.name in dim_names
                for c in t.columns if c.data_type == "dateTime" and not c.is_hidden
            ]
            if len(date_cols) == 1:
                visual.columns.append(date_cols[0])
                findings.append(BindingFinding(
                    "resolved", f"{vid}: {visual.visual_type} time axis → {date_cols[0]} "
                                "(idiom category type 'date', only date column in the model)"))
            else:
                why = (f"ambiguous: {', '.join(date_cols)}" if date_cols else "no date column")
                findings.append(BindingFinding(
                    "gap", f"{vid}: {visual.visual_type} needs a date axis — {why}"))
    return bound, findings


def bind_bracket_file(model: CanonicalModel,
                      bracket_path: Path) -> tuple[CanonicalModel, list[BindingFinding]]:
    """Bind via the bracket's ``overrides.data_contract_ref``; unchanged model + one gap
    finding when the bracket declares none or the file is missing."""
    bracket = yaml.safe_load(Path(bracket_path).read_text(encoding="utf-8")) or {}
    ref = contract_ref(bracket)
    if ref is None:
        return model, [BindingFinding("gap", "bracket declares no overrides.data_contract_ref")]
    path = resolve_contract_path(ref, bracket_path)
    if not path.is_file():
        return model, [BindingFinding("gap", f"data contract not found: {ref}")]
    return bind(model, path)


def dangling_references(model: CanonicalModel) -> list[str]:
    """References the bound model cannot satisfy: relationship ends and DAX ``T[C]`` column
    references (measure names in brackets are left alone — ``[M]`` has no table prefix).

    A dangling relationship end makes the model fail to load; a dangling DAX column makes
    the measure error. Both are reported, never patched."""
    cols = {t.name: {c.name for c in t.columns} for t in model.semantic.tables}
    measures = {m.name for t in model.semantic.tables for m in t.measures}
    out: list[str] = []
    for r in model.semantic.relationships:
        for t, c in ((r.from_table, r.from_column), (r.to_table, r.to_column)):
            if c not in cols.get(t, set()):
                out.append(f"relationship {r.from_table}.{r.from_column}→{r.to_table}."
                           f"{r.to_column}: {t}.{c} missing")
    for t in model.semantic.tables:
        for m in t.measures:
            from tooling.superversion.targets.tmdl import _dax_for  # dialect lives there
            dax, _ = _dax_for(m)
            for quoted, bare, col in _DAX_COLUMN_REF.findall(dax):
                table = quoted or bare
                if table not in cols:
                    out.append(f"measure '{m.name}': table '{table}' not in model")
                elif col not in cols[table] and col not in measures:
                    out.append(f"measure '{m.name}': {table}[{col}] not in model")
    return out
