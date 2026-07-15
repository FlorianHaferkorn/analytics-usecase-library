"""arch_targets.snowflake — ArchitectureBlueprint → Snowflake scaffolding (T7).

Plan-only. Same IR, Snowflake-native mapping: shortcut → external table / Iceberg;
mirror → managed table; medallion → DB schemas BRONZE/SILVER/GOLD; grounding →
Semantic Views over gold. Deterministic.
"""
from __future__ import annotations

import json

from tooling.superversion.arch_targets.base import ArchAdapter, register

_ACCESS = {
    "shortcut": "external table / Apache Iceberg (no copy)",
    "mirror": "managed table (replicated)",
    "copy": "physical copy (requires rationale)",
}


def _json(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def emit(blueprint: dict) -> dict[str, str]:
    med = blueprint.get("medallion", {})
    domains = sorted(blueprint.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", ""))
    ingestion = sorted(blueprint.get("ingestion", []), key=lambda e: e.get("source", ""))
    gold = sorted(p["name"] for p in med.get("gold", {}).get("data_products", []))

    schemas = {
        "database": "ANALYTICS",
        "schemas": ["BRONZE", "SILVER", "GOLD"],
        "gold_tables": gold,
        "domains": [
            {"name": d["name"], "role": f"R_{d['name'].upper()}", "products": sorted(d.get("data_products", []))}
            for d in domains
        ],
    }
    ingestion_plan = [
        {"source": e["source"], "access_mode": e["access_mode"], "action": _ACCESS.get(e["access_mode"], e["access_mode"])}
        for e in ingestion
    ]
    semantic_views = [{"domain": d["name"], "semantic_view": f"SV_{d['name'].upper()}", "over": "GOLD"} for d in domains]

    runbook = (
        "# Snowflake Provisioning Plan (generated — plan-only)\n\n"
        f"Database `ANALYTICS` with schemas BRONZE/SILVER/GOLD. Gold tables: "
        f"{', '.join(gold) or '(none)'}. Semantic Views over GOLD for grounding.\n"
    )
    return {
        "snowflake/PROVISIONING_PLAN.md": runbook,
        "snowflake/schemas.json": _json(schemas),
        "snowflake/ingestion_plan.json": _json(ingestion_plan),
        "snowflake/semantic_views.json": _json(semantic_views),
    }


register(ArchAdapter(id="snowflake", label="Snowflake (Semantic Views)", emit=emit))
