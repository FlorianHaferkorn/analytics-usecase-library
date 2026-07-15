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
    return {
        "databricks/PROVISIONING_PLAN.md": runbook,
        "databricks/unity_catalog.json": _json(unity),
        "databricks/ingestion_plan.json": _json(ingestion_plan),
        "databricks/grounding.json": _json(grounding),
    }


register(ArchAdapter(id="databricks", label="Databricks (Unity Catalog)", emit=emit))
