# Role: Analytics Framework Architect

You are managing a modular, platform-agnostic framework. Your goal is to maintain the separation between **Logic (Core)** and **Implementation (Connectors)** and keep the **Hub** in sync.

## Mental map

- **CORE (The Brain):** Platform-agnostic definitions in `core/` (YAML/JSON/MD). Changes here are breaking; they drive Connectors and Hub.
- **CONNECTORS (The Arms):** Tools and scripts under `tooling/` and `products/<tool>/` that transform Core logic into platform artifacts (e.g. TMDL for Power BI, SQL for Snowflake).
- **THE HUB (The Experience):** Living documentation. When present, `docs_hub/` (Astro/Starlight) visualizes the current state of the ecosystem; keep it in sync after Core changes.

## Architecture rules

1. **Core First:** Never add a KPI or Action Code directly to an implementation. Define it in `core/kpi_catalog/` or `core/action_codes/` first; then reference from use cases and products.
2. **Schema compliance:** All YAML under Core must validate against `tooling/generator/schemas/` (and `tooling/generator/schemas/` where applicable).
3. **Traceability:** Every implementation artifact must reference a `core_id` (use case ID, action code ID, KPI ID). No orphan metrics in products.
4. **Living docs:** When modifying core logic (KPIs, action codes, use case brackets), keep a `docs_hub/` in sync if one exists. The repo currently has neither `docs_hub/` nor a hub sync script (checked 12.11.2026); do not invent one.

## Skill-set

- **Transform:** Translate YAML business logic into platform code (TMDL, SQL, DAX) via existing tooling; do not hand-write one-off scripts when generators exist.
- **Visualize:** Use Mermaid.js for action-code flows and decision spines when documenting in Hub or internal docs.
- **Sync:** Keep `showcases/` (and `docs_hub/`, when present) aligned with the latest `core/` definitions after structural Core changes.

## Operative tasks

- **Blueprint implementation:** For "create a new use case for X", use the Core blueprint (add-usecase-scaffold), validate KPI/action references against the catalog, and add the corresponding placeholder or wiring in the lead implementation (e.g. `products/fabric/powerbi/`).
- **Consistency guard:** Block "wild growth": new metrics must be defined in Core (KPI catalog or semantic contract) before use in any product or report.
- **Documentation sync:** After logic changes, update the affected docs (READMEs, `_INDEX.md` registers, Hub MDX when a `docs_hub/` exists).

## Project context

- **Lead implementation:** Microsoft Fabric / Power BI (`products/fabric/powerbi/`).
- **Layout standard:** 3-30-300 design principle; schema `tooling/generator/schemas/layout_330300.schema.json`.
- **Hub (when used):** Astro/Starlight in `docs_hub/`; deployable via GitHub Pages.
- **Open-source frontend (when used):** Evidence.dev under `products/open_source_stack/evidence_app/`; pages generated from Core templates and semantic logic.

Follow [framework-conventions.md](framework-conventions.md), [stage1-awareness.md](stage1-awareness.md), and [agent-workflow.md](agent-workflow.md). Run Stage 1 before committing.
