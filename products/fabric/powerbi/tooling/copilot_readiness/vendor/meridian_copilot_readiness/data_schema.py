"""AI-data-schema-Empfehlung — kuratierte Tabellen-/Feldauswahl für Copilot.

Primärpfad: data_architecture.json (Gold-Tabellen + Spalten inkl. is_hidden).
Fallback:   governance.json (Datendomänen) + kpi.json (data_source-Felder),
            wenn keine data_architecture.json vorliegt.

Empfehlungslogik (deterministisch):
  - Gold-Layer-Faktentabellen  → include (Quelle der governten KPIs)
  - Bronze-/Silver-Tabellen    → exclude (Rohdaten, ais_context.no_raw_data)
  - is_hidden-Spalten          → exclude (technische Schlüssel)
"""
from __future__ import annotations

from products.meridian_copilot_readiness.generator.loader import (
    CopilotCore,
    pick_label,
    sources_meta,
)

_NOTE_DIMENSIONS = (
    "Datums-/Dimensionstabellen des Semantic Models (z.B. dim_date) sind nicht "
    "Teil von data_architecture.json — im Service sichtbar lassen, sie tragen "
    "die Grain-Auflösung der KPI-Fragen."
)


def _kpis_for_domain(core: CopilotCore, domain_id: str) -> list[str]:
    return [
        str(k.get("id"))
        for k in core.kpis
        if (k.get("data_source") or {}).get("domain_id") == domain_id
    ]


def _fields_from_columns(columns: dict) -> list[dict]:
    fields: list[dict] = []
    for col in (columns.get("grain") or []):
        hidden = bool(col.get("is_hidden"))
        fields.append({
            "name": col.get("tmdl_name"),
            "kind": "grain",
            "recommendation": "exclude" if hidden else "include",
            "reason": (
                "technischer Schlüssel (im Modell ausgeblendet)" if hidden
                else "Grain-Spalte — Breakdown-Dimension für Copilot-Fragen"
            ),
        })
    for col in (columns.get("measures") or []):
        fields.append({
            "name": col.get("tmdl_name"),
            "kind": "measure_source",
            "recommendation": "include",
            "reason": "Measure-Basis der governten KPIs",
        })
    return fields


def _tables_from_architecture(core: CopilotCore) -> list[dict]:
    tables: list[dict] = []
    for domain in core.arch_domains:
        domain_id = str(domain.get("id"))
        label = domain.get("label") or domain_id
        layer_tables = domain.get("tables") or {}
        kpi_ids = _kpis_for_domain(core, domain_id)

        gold = layer_tables.get("gold")
        if gold:
            tables.append({
                "name": gold,
                "domain": domain_id,
                "domain_label": label,
                "layer": "gold",
                "recommendation": "include",
                "reason": (
                    "Gold-Layer-Faktentabelle"
                    + (f"; Quelle für {', '.join(kpi_ids)}" if kpi_ids else "")
                ),
                "fields": _fields_from_columns(domain.get("columns") or {}),
            })
        for layer in ("bronze", "silver"):
            name = layer_tables.get(layer)
            if name:
                tables.append({
                    "name": name,
                    "domain": domain_id,
                    "domain_label": label,
                    "layer": layer,
                    "recommendation": "exclude",
                    "reason": (
                        f"{layer.capitalize()}-Layer — Rohdaten/Zwischenstand, "
                        "nicht für Copilot freigeben (ais_context.no_raw_data)"
                    ),
                    "fields": [],
                })
    return tables


def _tables_from_fallback(core: CopilotCore) -> list[dict]:
    """Ohne data_architecture.json: Domänen-Ebene aus governance.json + kpi.json."""
    tables: list[dict] = []
    for domain in core.data_domains:
        domain_id = str(domain.get("id"))
        kpi_ids = _kpis_for_domain(core, domain_id)
        fields = [
            {
                "name": (k.get("data_source") or {}).get("field"),
                "kind": "measure_source",
                "recommendation": "include",
                "reason": f"Quellfeld von {k.get('id')}",
            }
            for k in core.kpis
            if (k.get("data_source") or {}).get("domain_id") == domain_id
        ]
        tables.append({
            "name": f"<Gold-/Faktentabelle der Domäne {domain_id}>",
            "domain": domain_id,
            "domain_label": pick_label(domain.get("label"), "en") or domain_id,
            "layer": "gold",
            "recommendation": "include" if kpi_ids else "review",
            "reason": (
                f"Domäne trägt governte KPIs: {', '.join(kpi_ids)}" if kpi_ids
                else "Keine KPI im Core referenziert diese Domäne — Aufnahme prüfen"
            ),
            "fields": fields,
        })
    return tables


def build_ai_data_schema(core: CopilotCore) -> dict:
    if core.architecture is not None:
        derivation = "data_architecture"
        tables = _tables_from_architecture(core)
    else:
        derivation = "fallback_governance_kpi"
        tables = _tables_from_fallback(core)

    return {
        "_artifact": "ai_data_schema_recommendation",
        "_organisation": core.org_name(),
        "_status": (
            "Empfehlung — im Power-BI-Service unter 'Prep data for AI' → "
            "'AI data schema' manuell an-/abwählen (Preview-Feature, keine "
            "dokumentierte public API). 'exclude' = für Copilot ausblenden."
        ),
        "_derivation": derivation,
        "_generated_by": "products.meridian_copilot_readiness (deterministisch, kein LLM)",
        "_sources": sources_meta(core),
        "_note": _NOTE_DIMENSIONS,
        "tables": tables,
    }
