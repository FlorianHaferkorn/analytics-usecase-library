#!/usr/bin/env python3
"""
ontology_ttl.py — the library's business-object layer as a Fabric IQ ontology (Turtle).

I-21 W4.3, Meridian D-593 (delivery path (a): import from RDF/OWL into an empty ontology item)
and D-617 (one emitter: the catalog-agnostic ``ontologie_kern`` is mirrored from Meridian into
``tooling/superversion/vendor/meridian_dataarch/``). This adapter only supplies the ALUCA inputs:

* ``core/business_objects/business_objects.yaml`` (D-608) — one entity type per business object,
  IRI = bound table (the same names "Generate from semantic model" produces), attributes as data
  properties, business-object relationships as object properties;
* the KPI catalog (``core/kpi_catalog/kpis/*.yaml``) — ``kpi_key`` as the readable name next to each
  KPI id bound to an object.

Nothing is invented: a missing name or description stays missing (the gaps are curated via
``business_objects.py --template/--apply``). Action codes are not emitted as rules — the import
does not document a rule construct.

Deadline (I-21 W5.9): the old ontology experience (JSON item definition) retires on 2027-01-31
(Learn fabric/iq/ontology/overview, read 2026-10-01). This path does not depend on it: the RDF/OWL
import into an empty item is documented for the new experience (Learn
fabric/iq/ontology/how-to-import-export, read 2026-10-01). Never target an old-experience item.
Ledger: docs/architecture/_INDEX.md A-22.

Usage:
    python3 tooling/generator/ontology_ttl.py --check            # import profile, exit 1 on findings
    python3 tooling/generator/ontology_ttl.py --out build/ontology.ttl
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

if __package__ in (None, ""):          # run as a script: make `tooling.` importable
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tooling.generator import business_objects as bo  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
ORG = "aluca-library"
ORG_NAME = "ALUCA Analytics Library"
BASE_IRI = "urn:aluca:library:ontology#"
HERKUNFT = "ALUCA"
LANGUAGE = "en"


def kpi_names(repo: Path = REPO) -> dict[str, str]:
    """KPI id → ``kpi_key`` (the catalog's readable name)."""
    out: dict[str, str] = {}
    for f in sorted((repo / "core" / "kpi_catalog" / "kpis").glob("*.yaml")):
        doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if doc.get("kpi_id") and doc.get("kpi_key"):
            out[str(doc["kpi_id"])] = str(doc["kpi_key"])
    return out


def build(repo: Path = REPO) -> tuple[Any, Any]:
    """(kern module, ontology model) from the library layer."""
    from tooling.superversion._dataarch_vendor import load_module

    kern = load_module("ontologie_kern")
    doc = bo.load(repo)
    if doc is None:
        raise SystemExit(f"ERROR: {bo.DATA} missing (run business_objects.py --write first)")
    model = kern.modell_aus_geschaeftsobjekten(doc, ORG, ORG_NAME, BASE_IRI, sprache=LANGUAGE,
                                               kpi_namen=kpi_names(repo))
    return kern, model


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Business-object layer → Fabric IQ ontology (Turtle)")
    ap.add_argument("--repo-root", type=Path, default=REPO)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="import profile only; exit 1 on findings")
    mode.add_argument("--out", type=Path, metavar="TTL", help="write the Turtle file")
    a = ap.parse_args(argv)
    kern, model = build(a.repo_root)
    findings = kern.profil_befunde(model)
    if findings:
        print("ERROR (import profile):\n  " + "\n  ".join(findings), file=sys.stderr)
        return 1
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(kern.emit_ttl(model, herkunft=HERKUNFT), encoding="utf-8", newline="\n")
    print(f"[OK] {len(model.klassen)} entity types, {len(model.eigenschaften)} properties, "
          f"{len(model.beziehungen)} relationships" + (f" → {a.out}" if a.out else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
