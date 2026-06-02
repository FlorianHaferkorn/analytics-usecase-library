"""
schema_registry.py — Central registry for Power BI PBIP/PBIR JSON schema URLs.

Single source of truth: change version constants here first, then update
schema_manifest.json, regenerate reports, and run Fabric checks. Never
hardcode schema URLs inside generators, writers, validators, or adapters.

Upgrade procedure (one PR per version bump):
  1. Update the constant below.
  2. Run: python products/fabric/powerbi/tooling/update_schema_manifest.py
  3. Run: python products/fabric/powerbi/tooling/page_scaffold_generator/generate_full_report.py --use-case <ID> --force-full
  4. Run: .\\products\\fabric\\powerbi\\tooling\\run_fabric_checks.ps1
  5. Verify Desktop opens the report without errors.
  6. Commit registry + manifest + generated reports together.

Schema source references:
  PBIR definitions:  https://github.com/microsoft/json-schemas/tree/main/fabric/item/report/definition
  PBIP root file:    https://github.com/microsoft/json-schemas/tree/main/fabric/pbip/pbipProperties
  Semantic model:    https://github.com/microsoft/json-schemas/tree/main/fabric/item/semanticModel/definitionProperties
  Report theme:      https://github.com/microsoft/powerbi-desktop-samples/tree/main/Report%%20Theme%%20JSON%%20Schema
"""

from __future__ import annotations

_BASE = "https://developer.microsoft.com/json-schemas/fabric"


# ── Report JSON (definition/report.json) ───────────────────────────────────────
# Pinned: 3.3.0  |  Latest known: 3.3.0  |  Updated: 2026-06 (schema discovery)
REPORT_SCHEMA = f"{_BASE}/item/report/definition/report/3.3.0/schema.json"

# ── Page JSON (definition/pages/<name>/page.json) ──────────────────────────────
# Pinned: 2.1.0  |  Latest known: 2.1.0 (March 2026, Custom Totals)
PAGE_SCHEMA = f"{_BASE}/item/report/definition/page/2.1.0/schema.json"

# ── Visual container JSON (definition/pages/<p>/visuals/<v>/visual.json) ────────
# Pinned: 2.9.0  |  Latest known: 2.9.0 (June 2026, schema discovery)
VISUAL_SCHEMA = f"{_BASE}/item/report/definition/visualContainer/2.9.0/schema.json"

# ── Pages metadata JSON (definition/pages/pages.json) ──────────────────────────
# Pinned: 1.1.0  |  Latest known: 1.1.0  |  Updated: 2026-06 (schema discovery)
PAGES_METADATA_SCHEMA = f"{_BASE}/item/report/definition/pagesMetadata/1.1.0/schema.json"

# ── Version metadata JSON (definition/version.json) ────────────────────────────
# Pinned: 1.0.0  |  Latest known: 1.0.0  |  Updated: 2026-05
VERSION_METADATA_SCHEMA = f"{_BASE}/item/report/definition/versionMetadata/1.0.0/schema.json"

# ── PBIP root file (<Name>.pbip) ───────────────────────────────────────────────
# Pinned: 1.0.0  |  Latest known: 1.0.0  |  Updated: 2026-05
PBIP_SCHEMA = f"{_BASE}/pbip/pbipProperties/1.0.0/schema.json"

# ── definition.pbir (report-to-model binding) ──────────────────────────────────
# Path: <Name>.Report/definition.pbir
# Canonical URL does NOT include /definition/ segment — see Microsoft docs.
# Pinned: 2.0.0  |  Latest known: 2.0.0  |  Updated: 2026-05
DEFINITION_PBIR_SCHEMA = f"{_BASE}/item/report/definitionProperties/2.0.0/schema.json"

# version string written into definition.pbir — 4.0 supports both PBIR-Legacy
# (report.json) and PBIR (\definition folder).
DEFINITION_PBIR_VERSION = "4.0"

# ── Semantic model definition pointer (definition.pbism) ───────────────────────
# Pinned: 1.0.0  |  Latest known: 1.0.0  |  Updated: 2026-05
SEMANTIC_MODEL_SCHEMA = f"{_BASE}/item/semanticModel/definitionProperties/1.0.0/schema.json"

# ── Fabric Git integration .platform file ──────────────────────────────────────
# Used by create_direct_lake_model.py for .platform metadata files.
# Pinned: 2.1.0  |  Latest known: 2.1.0  |  Updated: 2026-06 (schema discovery)
PLATFORM_PROPERTIES_SCHEMA = f"{_BASE}/gitIntegration/platformProperties/2.1.0/schema.json"

# ── Report theme schema ─────────────────────────────────────────────────────────
# Source: github.com/microsoft/powerbi-desktop-samples / Report Theme JSON Schema
# Pinned: 2.154  |  Latest known: 2.154 (Power BI Desktop 2.154.x, June 2026)
# Update THEME_SCHEMA_PINNED_VERSION when a new monthly Desktop release ships.
THEME_SCHEMA_PINNED_VERSION = "2.154"
THEME_SCHEMA_URL = (
    "https://raw.githubusercontent.com/microsoft/powerbi-desktop-samples/main"
    f"/Report%20Theme%20JSON%20Schema/reportThemeSchema-{THEME_SCHEMA_PINNED_VERSION}.json"
)


# ── Convenience helpers ────────────────────────────────────────────────────────

def visual_schema_version() -> str:
    """Return only the version segment from VISUAL_SCHEMA (e.g. '2.3.0')."""
    return VISUAL_SCHEMA.rstrip("/").rsplit("/", 2)[-2]


def page_schema_version() -> str:
    """Return only the version segment from PAGE_SCHEMA (e.g. '2.0.0')."""
    return PAGE_SCHEMA.rstrip("/").rsplit("/", 2)[-2]


def report_schema_version() -> str:
    """Return only the version segment from REPORT_SCHEMA (e.g. '3.0.0')."""
    return REPORT_SCHEMA.rstrip("/").rsplit("/", 2)[-2]


def all_schemas() -> dict[str, str]:
    """Return all registered schema URLs keyed by logical name."""
    return {
        "report": REPORT_SCHEMA,
        "page": PAGE_SCHEMA,
        "visual": VISUAL_SCHEMA,
        "pages_metadata": PAGES_METADATA_SCHEMA,
        "version_metadata": VERSION_METADATA_SCHEMA,
        "pbip": PBIP_SCHEMA,
        "definition_pbir": DEFINITION_PBIR_SCHEMA,
        "semantic_model": SEMANTIC_MODEL_SCHEMA,
        "platform_properties": PLATFORM_PROPERTIES_SCHEMA,
        "theme_pinned_version": THEME_SCHEMA_PINNED_VERSION,
        "theme_url": THEME_SCHEMA_URL,
    }
