"""arch_targets.databricks — ArchitectureBlueprint → Databricks Unity Catalog scaffolding (T7).

Plan-only. Same IR, different native mapping: OneLake shortcut → UC external location /
Lakehouse Federation; mirror → managed table; medallion → UC `bronze`/`silver`/`gold`
schemas; grounding → Genie metric views over gold. Deterministic.
"""
from __future__ import annotations

import json

from tooling.superversion.arch_targets.base import ArchAdapter, register

_ACCESS = {
    "shortcut": "Unity Catalog external location / Lakehouse Federation (zero-copy)",
    "mirror": "managed table (replicated into UC)",
    "copy": "physical copy (requires rationale)",
}


def _json(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


# The mirrored Meridian emitters that carry a Databricks dialect (SHARED_SUBSTANCE.md
# class A). Meridian reaches these through CLI flags on its `run()` layer; ALUCA has no
# such layer — the adapter *is* the emission layer here, so the same substance is wired
# in one place instead. Fabric-only emitters (`emit_apply`, `emit_ingestion`) return
# nothing for this stack by their own design and are therefore not listed: a Fabric
# artifact in a Databricks rendering would be worse than a missing one.
_MIRRORED: tuple[tuple[str, dict], ...] = (
    ("emit_databricks_cicd", {}),
    ("emit_transforms", {"stack": "databricks"}),
    ("emit_notebooks", {"stack": "databricks"}),
    ("emit_lineage", {"stack": "databricks"}),
    # dbt Semantic Layer — stack-neutral by construction, so it carries no stack argument.
    ("emit_metricflow", {}),
)


def _mirrored_artifacts(blueprint: dict) -> dict[str, str]:
    """Artifacts from the mirrored emitters, or ``{}`` when the mirror is unavailable.

    A broken mirror degrades to the topology layer rather than to half-correct
    scaffolding — same promise the Fabric adapter makes.
    """
    try:
        from tooling.superversion._dataarch_vendor import VendorUnavailable, load_emitters
        api = load_emitters()
    except (ImportError, VendorUnavailable):
        return {}

    out: dict[str, str] = {}
    for name, kwargs in _MIRRORED:
        for path, content in api[name](blueprint, **kwargs).items():
            # `emit_databricks_cicd` already names its own stack; the rest are relative.
            key = path if path.startswith("databricks/") else f"databricks/{path}"
            out[key] = content
    return out


def emit(blueprint: dict) -> dict[str, str]:
    med = blueprint.get("medallion", {})
    domains = sorted(blueprint.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", ""))
    ingestion = sorted(blueprint.get("ingestion", []), key=lambda e: e.get("source", ""))
    gold = sorted(p["name"] for p in med.get("gold", {}).get("data_products", []))

    unity = {
        "catalog": "analytics",
        "schemas": ["bronze", "silver", "gold"],
        "gold_tables": gold,
        "domains": [
            {"name": d["name"], "group": f"grp_{d['name'].lower()}", "products": sorted(d.get("data_products", []))}
            for d in domains
        ],
    }
    ingestion_plan = [
        {"source": e["source"], "access_mode": e["access_mode"], "action": _ACCESS.get(e["access_mode"], e["access_mode"])}
        for e in ingestion
    ]
    grounding = {"engine": "Genie metric views over gold", "surface": blueprint.get("ai_grounding", {}).get("grounding_surface", [])}

    runbook = (
        "# Databricks Unity Catalog Provisioning Plan (generated — plan-only)\n\n"
        f"Catalog `analytics` with schemas bronze/silver/gold. Gold tables: "
        f"{', '.join(gold) or '(none)'}.\n"
    )
    out = {
        "databricks/PROVISIONING_PLAN.md": runbook,
        "databricks/unity_catalog.json": _json(unity),
        "databricks/ingestion_plan.json": _json(ingestion_plan),
        "databricks/grounding.json": _json(grounding),
    }
    out.update(_mirrored_artifacts(blueprint))
    return out


register(ArchAdapter(id="databricks", label="Databricks (Unity Catalog)", emit=emit))
