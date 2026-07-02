#!/usr/bin/env python3
"""
linguistic_schema.py — Epic A2: linguistic-schema projection (Copilot/Q&A readiness)
====================================================================================

The *third* projection of the governed catalog. PR #283 projects the catalog into
two AI surfaces — the TMDL ``///`` doc block and the viz tooltip (see
``core/semantic_models/AI_Description_Standard.md``). Both are **description text**.
Native Power BI Q&A and Copilot do not read description prose; they read the model's
**linguistic schema** (``cultures`` / ``linguisticMetadata``). So curated synonyms
that only reach ``///`` are invisible to in-product natural language.

This module closes that gap: it projects the curated, governed ``synonyms`` on data
contract columns into a TMDL ``culture`` object's ``linguisticMetadata`` (Power BI
Q&A linguistic schema, LSDL v1.0.0), written to
``<Domain>.SemanticModel/definition/cultures/<culture>.tmdl`` and referenced from
``model.tmdl`` via ``ref culture <culture>``.

Source of truth: data-contract column ``synonyms`` (one governed source, many
projections — never hand-authored here, never LLM-generated at build time).

Properties (Epic A2 acceptance):
  * Deterministic + idempotent — same contract yields byte-identical output.
  * TMDL-style clean — tab indentation only, no ``:=``, no ``description:`` property.

TMDL culture serialization reference:
  https://learn.microsoft.com/analysis-services/tmdl/tmdl-reference-tabular-object
LSDL (linguistic schema) binding reference:
  products/fabric/powerbi/docs/references/pbir-rename-cascade.md (Culture Files)

Keyword note: the object is declared ``culture <name>`` (with ``ref culture <name>``
in model.tmdl) per the MS Learn TMDL reference above and the SpaceParts sample.
Current TMDL rejects ``cultureInfo`` as an "Unsupported object type" — so ``culture``
is the correct (and only accepted) keyword; a Desktop round-trip is confirmatory only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from tooling.generator_core.ai_description import (
    TableDescription,
    build_table_descriptions,
)

# ─────────────────────────────────────────────────────────────────────────────
# Constants & paths
# ─────────────────────────────────────────────────────────────────────────────

LSDL_VERSION = "1.0.0"
DEFAULT_CULTURE = "en-US"

_SCRIPT_DIR = Path(__file__).resolve().parent                 # products/fabric/powerbi/tooling/
_PBIP_ROOT = _SCRIPT_DIR.parent                               # products/fabric/powerbi/
_PROJECT_ROOT = _PBIP_ROOT.parent.parent.parent               # analytics-usecase-library/
DIST = _PBIP_ROOT / "dist"
DATA_CONTRACTS = _PROJECT_ROOT / "core" / "data_contracts" / "domains"

# Domain → data contract filename — mirrors generate_semantic_model.DOMAIN_CONTRACT.
DOMAIN_CONTRACT: Dict[str, str] = {
    "Commercial": "commercial_sales.yaml",
    "Finance": "finance.yaml",
    "Operations": "operations.yaml",
    "SupplyChain": "supply_chain.yaml",
    "Experience": "experience.yaml",
}


# ─────────────────────────────────────────────────────────────────────────────
# Linguistic schema (LSDL) builder — deterministic
# ─────────────────────────────────────────────────────────────────────────────

def _slug(name: str) -> str:
    """Stable lookup-key fragment from an object name (key is arbitrary; the
    ``ConceptualEntity``/``ConceptualProperty`` carry the real binding)."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _entity(table: str, column: str, synonyms: List[str]) -> dict:
    """One LSDL entity: bind a model column and list its terms.

    The first term is the object's own name (Generated); each curated synonym is an
    Authored noun sourced from the governed catalog.
    """
    terms: List[dict] = [{column: {"State": "Generated"}}]
    for syn in synonyms:
        terms.append({syn: {"Type": "Noun", "State": "Authored", "Source": "User"}})
    return {
        "Definition": {
            "Binding": {"ConceptualEntity": table, "ConceptualProperty": column}
        },
        "State": "Generated",
        "Terms": terms,
    }


def build_linguistic_schema(
    tables: List[TableDescription], culture: str = DEFAULT_CULTURE
) -> dict:
    """Build the LSDL document from table/column descriptions.

    Only columns that carry curated ``synonyms`` produce an entity. Tables are
    iterated in name order and columns in contract order, so the output is a pure
    function of the contract (deterministic, idempotent).
    """
    entities: Dict[str, dict] = {}
    for table in sorted(tables, key=lambda t: t.name):
        for col in table.columns:
            if not col.synonyms:
                continue
            key = f"{table.name}.{_slug(col.name)}"
            entities[key] = _entity(table.name, col.name, list(col.synonyms))
    return {"Version": LSDL_VERSION, "Language": culture, "Entities": entities}


# ─────────────────────────────────────────────────────────────────────────────
# TMDL rendering — tab-indented, hook-clean
# ─────────────────────────────────────────────────────────────────────────────

def render_culture_tmdl(schema: dict, culture: str = DEFAULT_CULTURE) -> str:
    """Render the ``cultures/<culture>.tmdl`` file content.

    Layout (TMDL): ``linguisticMetadata`` is a nested object with two properties —
    ``contentType: Json`` and ``content = <expression>``. Without an explicit
    ``contentType``, Analysis Services' TMDL deserializer defaults to XML and
    throws ``does not comply with the Xml content-type`` on this JSON body
    (confirmed against ``Microsoft.AnalysisServices.Tabular.TmdlSerializer`` —
    real Power BI Desktop crash, model never loads). The JSON body is serialized
    with **tab** indentation and prefixed to TMDL expression level (3 tabs), so
    every line begins with tabs — never spaces — satisfying the TMDL-style hook.
    """
    body = json.dumps(schema, indent="\t", ensure_ascii=False)
    indented = "\n".join((f"\t\t\t{line}" if line else line) for line in body.split("\n"))
    return f"culture {culture}\n\tlinguisticMetadata\n\t\tcontentType: Json\n\t\tcontent =\n{indented}\n"


def parse_culture_tmdl(text: str) -> dict:
    """Inverse of :func:`render_culture_tmdl` — extract the LSDL JSON back out.

    Used by the round-trip test (Epic A2 risk mitigation). Skips the ``culture``/
    ``linguisticMetadata``/``contentType``/``content =`` header lines by finding
    the first ``{``, dedents the body and parses it as JSON.
    """
    lines = text.split("\n")
    try:
        start = next(i for i, l in enumerate(lines) if l.lstrip().startswith("{"))
    except StopIteration as exc:  # pragma: no cover - defensive
        raise ValueError("no JSON body found in culture TMDL") from exc
    body = "\n".join(l[3:] if l.startswith("\t\t\t") else l for l in lines[start:])
    return json.loads(body)


# ─────────────────────────────────────────────────────────────────────────────
# model.tmdl wiring
# ─────────────────────────────────────────────────────────────────────────────

def ensure_model_ref(model_tmdl_path: Path, culture: str = DEFAULT_CULTURE) -> bool:
    """Ensure ``model.tmdl`` declares ``ref culture <culture>`` (idempotent).

    Inserted directly after the last ``ref table`` line to keep ref groups ordered.
    Returns ``True`` if the file was modified.
    """
    text = model_tmdl_path.read_text(encoding="utf-8")
    ref_line = f"ref culture {culture}"
    lines = text.splitlines()
    if any(l.strip() == ref_line for l in lines):
        return False
    insert_at = len(lines)
    for i, l in enumerate(lines):
        if l.startswith("ref table "):
            insert_at = i + 1
    lines.insert(insert_at, ref_line)
    new_text = "\n".join(lines)
    if text.endswith("\n"):
        new_text += "\n"
    model_tmdl_path.write_text(new_text, encoding="utf-8")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Emitter
# ─────────────────────────────────────────────────────────────────────────────

def emit_for_domain(
    domain: str,
    dist_root: Path = DIST,
    contracts_dir: Path = DATA_CONTRACTS,
    culture: str = DEFAULT_CULTURE,
) -> Tuple[Path, int, bool]:
    """Write ``cultures/<culture>.tmdl`` for one domain and wire up ``model.tmdl``.

    Returns ``(culture_file, entity_count, model_ref_added)``.
    """
    if domain not in DOMAIN_CONTRACT:
        raise KeyError(f"unknown domain '{domain}'")
    contract = Path(contracts_dir) / DOMAIN_CONTRACT[domain]
    tables = build_table_descriptions(contract)
    schema = build_linguistic_schema(tables, culture)
    n_entities = len(schema["Entities"])

    def_dir = Path(dist_root) / f"{domain}.SemanticModel" / "definition"
    out = def_dir / "cultures" / f"{culture}.tmdl"

    # Don't emit an empty linguistic schema: a culture with no curated synonyms adds
    # nothing for Q&A/Copilot and only creates noise. Domains gain a culture file once
    # their contracts carry synonyms (A2 ships Commercial; others follow as curated).
    if n_entities == 0:
        return out, 0, False

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_culture_tmdl(schema, culture), encoding="utf-8")

    model_ref_added = False
    model_tmdl = def_dir / "model.tmdl"
    if model_tmdl.exists():
        model_ref_added = ensure_model_ref(model_tmdl, culture)

    return out, n_entities, model_ref_added


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def check_coverage(
    domains: List[str],
    dist_root: Path = DIST,
    contracts_dir: Path = DATA_CONTRACTS,
    culture: str = DEFAULT_CULTURE,
) -> Dict[str, List[str]]:
    """Return ``{"<domain>:<table>.<column>": [dropped synonyms]}`` — empty when the
    committed linguistic schema covers every governed synonym (the gate is green).
    """
    gaps: Dict[str, List[str]] = {}
    for domain in domains:
        contract = Path(contracts_dir) / DOMAIN_CONTRACT[domain]
        if not contract.exists():
            continue
        governed: Dict[Tuple[str, str], List[str]] = {}
        for tbl in build_table_descriptions(contract):
            for col in tbl.columns:
                if col.synonyms:
                    governed[(tbl.name, col.name)] = list(col.synonyms)
        if not governed:
            continue
        culture_terms: Dict[Tuple[str, str], set] = {}
        cfile = Path(dist_root) / f"{domain}.SemanticModel" / "definition" / "cultures" / f"{culture}.tmdl"
        if cfile.exists():
            schema = parse_culture_tmdl(cfile.read_text(encoding="utf-8"))
            for ent in (schema.get("Entities") or {}).values():
                b = (ent.get("Definition") or {}).get("Binding") or {}
                key = (b.get("ConceptualEntity"), b.get("ConceptualProperty"))
                culture_terms.setdefault(key, set()).update(
                    next(iter(term)) for term in (ent.get("Terms") or [])
                )
        for key, syns in governed.items():
            dropped = [s for s in syns if s not in culture_terms.get(key, set())]
            if dropped:
                gaps[f"{domain}:{key[0]}.{key[1]}"] = dropped
    return gaps


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emit the TMDL linguistic schema (cultures/) from data contracts."
    )
    parser.add_argument("--domain", "-d", choices=list(DOMAIN_CONTRACT.keys()))
    parser.add_argument("--all", "-a", action="store_true", help="Emit (or check) all domains")
    parser.add_argument("--check", action="store_true",
                        help="Verify the committed linguistic schema covers every governed "
                             "synonym; exit 1 on any gap (no files written).")
    parser.add_argument("--culture", default=DEFAULT_CULTURE, help="Culture, e.g. en-US")
    parser.add_argument("--dist-root", default=str(DIST))
    parser.add_argument("--contracts-dir", default=str(DATA_CONTRACTS))
    args = parser.parse_args(argv)

    if not args.domain and not args.all:
        parser.print_help()
        return 1

    domains = list(DOMAIN_CONTRACT.keys()) if args.all else [args.domain]

    if args.check:
        gaps = check_coverage(domains, Path(args.dist_root), Path(args.contracts_dir), args.culture)
        if gaps:
            print("  ✗ Linguistic coverage gap — governed synonyms missing from the schema:")
            for loc, dropped in sorted(gaps.items()):
                print(f"      {loc}: {', '.join(dropped)}")
            print("    Regenerate: python3 -m products.fabric.powerbi.tooling.linguistic_schema --all")
            return 1
        print("  ✅  Linguistic coverage: all governed synonyms present.")
        return 0

    for domain in domains:
        contract = Path(args.contracts_dir) / DOMAIN_CONTRACT[domain]
        if not contract.exists():
            print(f"  ⚠️  {domain}: contract not found ({contract}) — skipped")
            continue
        out, n, added = emit_for_domain(
            domain, Path(args.dist_root), Path(args.contracts_dir), args.culture
        )
        if n == 0:
            print(f"  ○   {domain}: no curated synonyms — culture skipped")
            continue
        ref_note = " (+ref culture)" if added else ""
        print(f"  ✅  {domain}: {n} synonym entit{'y' if n == 1 else 'ies'} → {out}{ref_note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
