"""
data_contracts.py — conformed tables across the domain data contracts (Bus-Matrix).

Rule (Florian, 29.09.2026, Kimball conformed dimensions): every physical table has **exactly one**
definition — in the contract of its owning domain. Every other domain that uses the table
refers to it instead of redefining it:

.. code-block:: yaml

    dimension:
      - name: dim_date
        conformed_from: commercial_sales              # owning domain (its `domain:` value)
        uses_columns: [DateKey, Date, Year, Quarter]  # optional: the columns this domain uses

A reference carries no ``columns`` and no table fields of its own (description, grain, …): the
owner's definition is the only one. ``uses_columns`` names the subset of the owner's columns the
domain's model uses (the per-domain semantic model, linguistic schema and AI descriptions stay
on that subset); without it the domain uses every column.

Two views, one source:

* **canonical** — the raw YAML: one definition per table. ``export_governed_catalog.py``, the
  validator and the showcase proof read this.
* **domain view** — :func:`resolve_contract`: every reference replaced by a copy of the owner's
  table, columns narrowed to ``uses_columns`` (in that order) and ``conformed_from`` kept, so a
  per-domain consumer (``ai_description``, ``linguistic_schema``, ``enrich_measure_docs``)
  sees the same table list as before, with the owner's column specs.

Validation of the references (owner exists, owner defines the table, columns exist, no second
definition) lives in ``tooling/validation/check_validate_data_contracts.py`` — here only the
resolution, which skips what it cannot resolve rather than inventing it.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Iterable

import yaml

#: Table fields of a reference (everything else belongs to the owner's definition).
CONFORMED_FROM = "conformed_from"
USES_COLUMNS = "uses_columns"
REFERENCE_KEYS = frozenset({"name", CONFORMED_FROM, USES_COLUMNS})
SECTIONS = ("dimension", "fact")


def is_reference(table: Any) -> bool:
    """True for a table entry that refers to the owner's definition."""
    return isinstance(table, dict) and CONFORMED_FROM in table


def _tables(doc: dict, section: str) -> list:
    tables = doc.get(section) or []
    return tables if isinstance(tables, list) else [tables]


def load_contracts(contracts_dir: Path | str) -> list[tuple[Path, dict]]:
    """``(path, doc)`` of every ``*.yaml`` under ``contracts_dir`` (sorted; unparsable → skipped)."""
    out: list[tuple[Path, dict]] = []
    for path in sorted(Path(contracts_dir).glob("*.yaml")):
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if isinstance(doc, dict):
            out.append((path, doc))
    return out


def domain_of(path: Path, doc: dict) -> str:
    return str(doc.get("domain") or path.stem)


def owners(contracts: Iterable[tuple[Path, dict]]) -> dict[str, tuple[str, str, dict]]:
    """``{table: (owning domain, section, table)}`` — the first definition (non-reference) per name."""
    out: dict[str, tuple[str, str, dict]] = {}
    for path, doc in contracts:
        dom = domain_of(path, doc)
        for section in SECTIONS:
            for t in _tables(doc, section):
                if isinstance(t, dict) and t.get("name") and not is_reference(t):
                    out.setdefault(t["name"], (dom, section, t))
    return out


def users(contracts: Iterable[tuple[Path, dict]]) -> dict[str, list[str]]:
    """``{table: sorted domains that define or reference it}`` (Bus-Matrix row per table)."""
    out: dict[str, set[str]] = {}
    for path, doc in contracts:
        dom = domain_of(path, doc)
        for section in SECTIONS:
            for t in _tables(doc, section):
                if isinstance(t, dict) and t.get("name"):
                    out.setdefault(t["name"], set()).add(dom)
    return {k: sorted(v) for k, v in out.items()}


def _narrow(table: dict, uses: Any) -> dict:
    """``table`` with its columns narrowed to ``uses`` (in that order), when ``uses`` is a list."""
    if isinstance(uses, list):
        by_name = {c.get("name"): c for c in table.get("columns") or [] if isinstance(c, dict)}
        table["columns"] = [by_name[n] for n in uses if n in by_name]
    return table


def resolve_table(ref: dict, owner_index: dict[str, tuple[str, str, dict]]) -> dict | None:
    """The domain view of one reference, or ``None`` when the owner does not define the table."""
    hit = owner_index.get(ref.get("name"))
    if hit is None or hit[0] != ref.get(CONFORMED_FROM):
        return None
    table = copy.deepcopy(hit[2])
    table.pop(USES_COLUMNS, None)          # the owner's own use is not the referencing domain's
    table = _narrow(table, ref.get(USES_COLUMNS))
    table[CONFORMED_FROM] = ref[CONFORMED_FROM]
    return table


def resolve_contract(doc: dict, owner_index: dict[str, tuple[str, str, dict]]) -> dict:
    """A copy of ``doc`` in its domain view: every resolvable reference replaced by the owner's
    table, and every table (definition or reference) narrowed to its ``uses_columns``."""
    out = copy.deepcopy(doc)
    for section in SECTIONS:
        tables = out.get(section)
        if not isinstance(tables, list):
            continue
        resolved = []
        for t in tables:
            if is_reference(t):
                view = resolve_table(t, owner_index)
                resolved.append(view if view is not None else t)
            elif isinstance(t, dict):
                resolved.append(_narrow(t, t.get(USES_COLUMNS)))
            else:
                resolved.append(t)
        out[section] = resolved
    return out


def load_resolved_contract(contract_path: Path | str) -> dict:
    """The domain view of one contract file; owners are looked up among its sibling files."""
    path = Path(contract_path)
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        return {}
    if not any(isinstance(t, dict) and (CONFORMED_FROM in t or USES_COLUMNS in t)
               for s in SECTIONS for t in _tables(doc, s)):
        return doc
    return resolve_contract(doc, owners(load_contracts(path.parent)))
