#!/usr/bin/env python3
"""
business_objects.py — derive and check the business-object layer of the library (D-608, I-21 W4.6).

The layer (``core/business_objects/business_objects.yaml``) follows
``tooling/generator/schemas/business_object.schema.json`` — one schema for ALUCA and Meridian
(peer pair, byte-identical; Meridian's ``scripts/check_aluca_mirror.py`` compares the two files,
``tooling/tests/test_business_objects.py`` pins the hash here).

**Derived, never invented.** One business object per governed table (the one definition per
table of the Bus-Matrix, ``tooling/utils/data_contracts.py``); what the sources do not carry
stays ``null`` (a gap, counted by :func:`gaps`). Per field:

* ``kind``: ``dimension`` → ``master_data``, ``fact`` → ``transaction``.
* ``name`` de/en: no source carries a business name → gap.
* ``description``, ``grain``: the contract's table ``description`` / ``grain``.
* ``domain``: the owning domain (the one definition); ``used_by_domains``: every domain that
  defines or refers to the table (``users``).
* ``keys``: columns with ``role: key``; an ``int`` column named ``*Key`` is technical, any other
  key natural. No declared key → both ``null``.
* ``attributes``: the contract columns; type mapped to the Fabric IQ property types of the schema;
  ``column`` is ``source_column`` when set (the physical column). No source classifies personal
  data per column → ``personal_data: null``.
* ``relationships``: every column with ``ref``: target = the referenced table's object,
  ``to_column`` = its ``role: key`` column (README: "``ref`` — FK to the dimension's ``role: key``
  column"), ``cardinality`` as declared (else gap), ``role`` → gap.
* ``binding``: the table; ``schema``/``layer`` → gap (the contracts README calls the contracts
  Silver, ``source_column`` "the physical Gold column" — the sources disagree, so no layer is set).
* ``kpi_ids``: KPIs whose ``technical.lineage`` reads the table (``export_governed_catalog``).

Ids stay stable: ``--write`` keeps the id of a table already in the file and gives a new table the
next free number; a curated value (the derivation yields ``null``, the file has a value) is kept.
``--check`` exits 1 when writing would change the file or a gate fails (schema, Golden Thread,
referential integrity, physical binding).

Usage:
    python3 tooling/generator/business_objects.py --write
    python3 tooling/generator/business_objects.py --check
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

if __package__ in (None, ""):          # run as a script: make `tooling.` importable
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tooling.generator.export_governed_catalog import _load_measures  # noqa: E402
from tooling.utils.data_contracts import is_reference, load_contracts, users  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SCHEMA = REPO / "tooling" / "generator" / "schemas" / "business_object.schema.json"
DATA = Path("core") / "business_objects" / "business_objects.yaml"
BO_ID_RE = re.compile(r"^BO-(\d{3})$")

#: contract column type → Fabric IQ property type (schema enum)
TYPE_MAP = {"int": "int64", "text": "string", "currency": "decimal", "decimal": "decimal",
            "boolean": "boolean", "bool": "boolean", "date": "dateTime", "datetime": "dateTime"}

GAP_FIELDS = ("name.de", "name.en", "description", "grain", "domain", "keys.technical",
              "keys.natural", "binding.schema", "binding.layer", "attribute.description",
              "attribute.personal_data", "relationship.cardinality", "relationship.role",
              "relationship.to_column")


def _tables(repo: Path) -> list[tuple[str, str, dict, list[str]]]:
    """``(domain, section, table, users)`` per definition, sorted by table name."""
    contracts = load_contracts(repo / "core" / "data_contracts" / "domains")
    used = users(contracts)
    out = []
    for path, doc in contracts:
        dom = str(doc.get("domain") or path.stem)
        for section in ("dimension", "fact"):
            for t in doc.get(section) or []:
                if isinstance(t, dict) and t.get("name") and not is_reference(t):
                    out.append((dom, section, t, used.get(t["name"], [dom])))
    return sorted(out, key=lambda x: x[2]["name"])


def _columns(table: dict) -> list[dict]:
    seen: set[str] = set()
    out = []
    for c in table.get("columns") or []:
        if isinstance(c, dict) and c.get("name") and c["name"] not in seen:
            seen.add(c["name"])
            out.append(c)
    return out


def _key_columns(table: dict) -> list[dict]:
    return [c for c in _columns(table) if c.get("role") == "key"]


def derive(repo: Path = REPO) -> dict[str, Any]:
    """Contracts + KPI catalog → business-object document (ids BO-001… in table-name order)."""
    tables = _tables(repo)
    ids = {t["name"]: f"BO-{i:03d}" for i, (_d, _s, t, _u) in enumerate(tables, 1)}
    by_name = {t["name"]: t for _d, _s, t, _u in tables}
    kpis: dict[str, set[str]] = {}
    for m in _load_measures(repo / "core" / "kpi_catalog" / "kpis"):
        for lin in m["lineage"]:
            kpis.setdefault(lin.split(".", 1)[0], set()).add(m["kpi_id"])

    objects = []
    for dom, section, t, used in tables:
        keys = _key_columns(t)
        tech = [c["name"] for c in keys if c.get("type") == "int" and c["name"].endswith("Key")]
        nat = [c["name"] for c in keys if c["name"] not in tech]
        attributes = [{
            "name": c["name"],
            "type": TYPE_MAP[str(c.get("type"))],
            "description": c.get("description") or None,
            "column": c.get("source_column") or c["name"],
            "target_state": c.get("target_state") is True,
            "personal_data": None,
            "personal_data_category": None,
        } for c in _columns(t)]
        relationships = []
        for c in _columns(t):
            if not c.get("ref"):
                continue
            target_keys = _key_columns(by_name.get(c["ref"], {}))
            relationships.append({
                "target": ids.get(c["ref"], f"unresolved:{c['ref']}"),
                "cardinality": c.get("cardinality"),
                "role": None,
                "from_column": c.get("source_column") or c["name"],
                "to_column": target_keys[0]["name"] if len(target_keys) == 1 else None,
            })
        objects.append({
            "id": ids[t["name"]],
            "name": {"de": None, "en": None},
            "description": t.get("description") or None,
            "kind": "master_data" if section == "dimension" else "transaction",
            "grain": t.get("grain") if section == "fact" else None,
            "domain": dom,
            "used_by_domains": used,
            "keys": {"technical": tech or None, "natural": nat or None},
            "attributes": attributes,
            "relationships": relationships,
            "binding": {"table": t["name"], "schema": None, "layer": None},
            "kpi_ids": sorted(kpis.get(t["name"], ())),
        })
    return {
        "_schema": "tooling/generator/schemas/business_object.schema.json",
        "_description": "Business-object layer of the ALUCA library (D-608). Derived; null = gap.",
        "_derived_from": ["core/data_contracts/domains/*.yaml", "core/kpi_catalog/kpis/*.yaml"],
        "_generated_by": "python3 tooling/generator/business_objects.py --write",
        "catalog": "aluca-library",
        "business_objects": objects,
    }


# ─── merge with the file (stable ids, curated values) ─────────────────────────

def _fill(new: Any, old: Any) -> Any:
    """The derived value; only where the derivation yields ``None`` the curated one counts."""
    if new is None:
        return old
    if isinstance(new, dict) and isinstance(old, dict):
        return {k: _fill(v, old.get(k)) for k, v in new.items()}
    return new


def merge(derived: dict[str, Any], existing: dict[str, Any] | None) -> dict[str, Any]:
    doc = copy.deepcopy(derived)
    if not existing:
        return doc
    old = {o["binding"]["table"]: o for o in existing.get("business_objects") or []}
    taken = [int(m.group(1)) for o in old.values() if (m := BO_ID_RE.match(str(o.get("id", ""))))]
    nxt = max(taken, default=0) + 1
    remap: dict[str, str] = {}
    for o in doc["business_objects"]:
        prev = old.get(o["binding"]["table"])
        if prev:
            remap[o["id"]] = prev["id"]
        else:
            remap[o["id"]] = f"BO-{nxt:03d}"
            nxt += 1
    for o in doc["business_objects"]:
        prev = old.get(o["binding"]["table"]) or {}
        o["id"] = remap[o["id"]]
        for r in o["relationships"]:
            r["target"] = remap.get(r["target"], r["target"])
        for f in ("name", "description", "grain", "domain", "keys", "binding"):
            o[f] = _fill(o[f], prev.get(f))
        old_attr = {a.get("name"): a for a in prev.get("attributes") or []}
        o["attributes"] = [_fill(a, old_attr.get(a["name"])) for a in o["attributes"]]
        old_rel = {(r.get("target"), r.get("from_column")): r for r in prev.get("relationships") or []}
        o["relationships"] = [_fill(r, old_rel.get((r["target"], r["from_column"])))
                              for r in o["relationships"]]
    doc["business_objects"].sort(key=lambda o: o["id"])
    return doc


# ─── gates ────────────────────────────────────────────────────────────────────

def catalog_kpi_ids(repo: Path = REPO) -> set[str]:
    out = set()
    for p in (repo / "core" / "kpi_catalog" / "kpis").glob("*.yaml"):
        doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if isinstance(doc, dict) and doc.get("kpi_id"):       # skips _index.yaml
            out.add(str(doc["kpi_id"]))
    return out


def physical_columns(repo: Path = REPO) -> dict[str, set[str]]:
    """Table → physical columns (``source_column`` or ``name``), straight from the contracts."""
    return {t["name"]: {c.get("source_column") or c["name"] for c in _columns(t)}
            for _d, _s, t, _u in _tables(repo)}


def check(doc: dict[str, Any], kpi_catalog: set[str], columns: dict[str, set[str]]) -> list[str]:
    """Schema, unique ids/bindings, relationship targets, Golden Thread, physical columns."""
    from jsonschema import Draft202012Validator

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    out = [f"schema: {'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
           for e in Draft202012Validator(schema).iter_errors(doc)]
    objs = doc.get("business_objects") or []
    ids = [o.get("id") for o in objs]
    out += [f"duplicate id: {i}" for i in sorted({i for i in ids if ids.count(i) > 1})]
    tabs = [(o.get("binding") or {}).get("table") for o in objs]
    out += [f"table bound twice: {t}" for t in sorted({t for t in tabs if tabs.count(t) > 1})]
    by_id = {o.get("id"): o for o in objs}
    for o in objs:
        t = (o.get("binding") or {}).get("table")
        if t not in columns:
            out.append(f"{o.get('id')}: table {t!r} not in the data contracts")
            continue
        out += [f"{o['id']}: column {a.get('column')!r} missing in {t}"
                for a in o.get("attributes") or [] if a.get("column") not in columns[t]]
        out += [f"{o['id']}: KPI {k} not in the catalog (Golden Thread)"
                for k in o.get("kpi_ids") or [] if k not in kpi_catalog]
        for r in o.get("relationships") or []:
            target = by_id.get(r.get("target"))
            if not target:
                out.append(f"{o['id']}: relationship target {r.get('target')} does not exist")
                continue
            if r.get("from_column") not in columns[t]:
                out.append(f"{o['id']}: join column {r.get('from_column')!r} missing in {t}")
            tt = target["binding"]["table"]
            if r.get("to_column") is not None and r["to_column"] not in columns.get(tt, set()):
                out.append(f"{o['id']}: join column {r['to_column']!r} missing in {tt}")
    return out


def gaps(doc: dict[str, Any]) -> dict[str, int]:
    """Counter per field: how often it is ``null`` (unknown). ``grain`` counts transactions only."""
    z = dict.fromkeys(GAP_FIELDS, 0)
    for o in doc.get("business_objects") or []:
        for f in ("name.de", "name.en", "keys.technical", "keys.natural", "binding.schema", "binding.layer"):
            a, b = f.split(".")
            z[f] += (o.get(a) or {}).get(b) is None
        z["description"] += o.get("description") is None
        z["domain"] += o.get("domain") is None
        z["grain"] += o.get("kind") == "transaction" and o.get("grain") is None
        for a in o.get("attributes") or []:
            z["attribute.description"] += a.get("description") is None
            z["attribute.personal_data"] += a.get("personal_data") is None
        for r in o.get("relationships") or []:
            for f in ("cardinality", "role", "to_column"):
                z[f"relationship.{f}"] += r.get(f) is None
    return z


def dump(doc: dict[str, Any]) -> str:
    return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100)


def load(repo: Path = REPO) -> dict[str, Any] | None:
    p = repo / DATA
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.is_file() else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Derive/check the business-object layer (D-608)")
    ap.add_argument("--repo-root", type=Path, default=REPO)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    existing = load(a.repo_root)
    doc = merge(derive(a.repo_root), existing)
    kpis, cols = catalog_kpi_ids(a.repo_root), physical_columns(a.repo_root)
    problems = check(doc, kpis, cols)
    if a.check:
        if existing is None:
            problems.append(f"{DATA} missing (create with --write)")
        else:
            problems += check(existing, kpis, cols)
            if dump(doc) != dump(existing):
                problems.append(f"{DATA} differs from the derivation (rewrite with --write)")
    if problems:
        print("ERROR:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    if a.write:
        p = a.repo_root / DATA
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(dump(doc), encoding="utf-8", newline="\n")
    g = gaps(doc)
    print(f"[OK] {len(doc['business_objects'])} business objects, {sum(g.values())} gaps: "
          + ", ".join(f"{k}={v}" for k, v in g.items() if v))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
