# Studio Data Wiring — UI ↔ Core Loader Map

**Status:** Authoritative mapping. Every piece of data shown in the new shell must come from one of the loaders listed here. **No new "mock" data.**

**How to read this file:** each view from the uploaded mockup is a row. The columns explain which loader produces the data and which API route mutates it. If a row has no loader, that's a **gap** — flagged at the end.

---

## 1. Loader inventory (`src/lib/core/*-loader.ts`)

| Loader | Source of truth | Returns | Key exports |
|---|---|---|---|
| `catalog-loader.ts` | `core/kpi_catalog/*.yaml` | KPI definitions | `loadKpiCatalog()`, `loadKpi(id)`, `loadKpiMap()`, `loadDomainTags()` |
| `action-loader.ts` | `core/action_codes/*.yaml` | Action code playbooks | `loadAllActionCodes()`, `loadActionCode(id)` |
| `bracket-loader.ts` | `core/usecases/**/UseCase_Bracket.yaml` | Machine-readable use case spec | `loadBracket(id)`, `loadAllBrackets()` |
| `factsheet-loader.ts` | `core/usecases/**/Business_Factsheet.md` | Prose factsheet + frontmatter | `loadFactsheet(id)`, `loadAllFactsheets()`, `getFactsheetForKpi(kpiId)` |
| `contract-loader.ts` | `core/data_contracts/**/*.yaml` | Data contracts / sources | `loadAllContracts()`, `loadContract(id)`, `loadContractMap()` |
| `spine-loader.ts` | `core/strategy_operating_model/**` | Org spines, value driver model | — |
| `lineage-builder.ts` | derived | Graph of KPIs ↔ Action Codes ↔ Contracts | `buildLineageGraph()` |
| `org-role-loader.ts` | `core/strategy_operating_model/roles/*.yaml` | RACI roles, owners | — |
| `golden20.ts` | constant | Top-20 strategic KPI whitelist | `GOLDEN_20_IDS`, `GOLDEN_20_IDS_SET` |
| `yaml-loader.ts` | internal utility | Generic YAML I/O | — |

**Rule for Sonnet 4.6:** if data is needed in a view, check this table first. If the loader exists, use it. If it doesn't, add a row to the "Gaps" section at the bottom and surface it in the rebuild plan — do **not** silently add a new loader.

---

## 2. View-by-view mapping

### 2.1 Dashboard view (maps to mockup `detail.jsx` → `Dashboard` export)

Shows a Core health snapshot: KPI coverage, action readiness, sparklines.

| UI element | Data source | Loader call | Notes |
|---|---|---|---|
| KPI count card | `loadKpiCatalog()` | `catalog-loader` | `.length` |
| Golden-20 completion | `loadKpiCatalog()` + `GOLDEN_20_IDS_SET` | `catalog-loader`, `golden20` | Intersection of catalog with whitelist |
| Use case count | `loadAllBrackets()` | `bracket-loader` | `.length` |
| Action codes coverage | `loadAllActionCodes()` | `action-loader` | Total + orphans (no referencing use case) |
| Composition stripes | `loadDomainTags()` + grouped counts | `catalog-loader` | One stripe per domain |
| Sparklines (activity) | `/api/audit` events | `src/app/api/audit/route.ts` | Last 14 days aggregated |
| "Recent changes" list | same audit endpoint | — | Include `actor`, `entity_type`, `entity_id` |

### 2.2 Canvas view (maps to mockup `data.jsx` → `Canvas` export)

Full Golden Thread lineage graph. Pan/zoom, node types = KPI / Contract / Action Code / Use Case.

| UI element | Data source | Loader call |
|---|---|---|
| Graph nodes + edges | `buildLineageGraph()` | `lineage-builder` |
| Node detail popover | `loadKpi(id)` / `loadActionCode(id)` / `loadContract(id)` / `loadBracket(id)` | resolved by node type |
| Domain filter | `loadDomainTags()` | `catalog-loader` |
| Certification filter | derived from each node's `status` field | — |

**Implementation note:** keep the existing `@xyflow/react` + `@dagrejs/dagre` setup. Port the layout heuristics from the mockup but plug them into React Flow nodes, not raw SVG.

### 2.3 Library view (maps to mockup `tweaks.jsx` → `Library` export)

Tabbed registry: KPIs / Dimensions / Sources / Action Codes / Use Cases.

| Tab | Data source | Loader call | Row shape |
|---|---|---|---|
| KPIs | `loadKpiCatalog()` | `catalog-loader` | `{ id, label, domain, polarity, status }` |
| Dimensions | derived from contracts | `loadAllContracts()` | Distinct dimension refs |
| Sources | `loadAllContracts()` | `contract-loader` | `{ id, label, system, owner }` |
| Action Codes | `loadAllActionCodes()` | `action-loader` | `{ id, label, kpi_id, severity }` |
| Use Cases | `loadAllBrackets()` + `loadAllFactsheets()` (joined on `id`) | both | `{ id, title, domain, strategic_kpi_id, factsheet_status }` |

Row click → navigates to **Detail view** with the corresponding entity.

### 2.4 Detail view (maps to mockup `library.jsx` → `Detail` export)

The tabbed editor (see REBUILD_DECISIONS.md §D5). Shape depends on entity type.

#### 2.4.1 Use Case detail

| Tab | Data source | Mutation route |
|---|---|---|
| **Overview** | `loadBracket(id)` + `loadFactsheet(id)` | read-only derived summary |
| **Factsheet** (prose, MDX) | `loadFactsheet(id)` | `PUT /api/factsheets/[bracketId]` |
| **Bracket** (YAML, Monaco) | `loadBracket(id)` | `PUT /api/core/brackets/[id]` |
| **Data Contracts** | `loadAllContracts()` filtered by refs in bracket | read-only list; clicking a row navigates to its Detail |
| **History** | `/api/audit?entity=usecase&id=[id]` | read-only |

**Cascading AI** on save:
- Factsheet change → `POST /api/ai/factsheet-draft` with `{ mode: 'reconcile', prose: new, bracket: current }` → returns bracket diff for user to accept.
- Bracket change → same endpoint with `{ mode: 'reconcile', bracket: new, prose: current }` → returns prose diff.

#### 2.4.2 KPI detail

| Tab | Data source | Mutation |
|---|---|---|
| Definition | `loadKpi(id)` | `PUT /api/core/kpis` |
| Referencing use cases | `getFactsheetForKpi(id)` + filter `loadAllBrackets()` by `orchestration.strategic_kpi_id` or `influencing_kpi_ids` | — |
| Linked contracts | `loadAllContracts()` filtered by `kpi_id` | — |
| Action codes | `loadAllActionCodes()` filtered by `kpi_id` | — |
| History | audit endpoint | — |

#### 2.4.3 Action Code detail

| Tab | Data source | Mutation |
|---|---|---|
| Playbook | `loadActionCode(id)` | `PUT /api/core/actions` |
| Triggering KPI | `loadKpi(playbook.kpi_id)` | read-only |
| Referencing use cases | filter `loadAllBrackets()` by `orchestration.action_code_ids` | — |

#### 2.4.4 Data Source detail

| Tab | Data source | Mutation |
|---|---|---|
| Contract | `loadContract(id)` | `PUT /api/core/contracts` |
| Referencing KPIs | `loadKpiCatalog()` filtered by `lineage` | — |

### 2.5 Wizard (maps to mockup `primitives.jsx` → `Wizard` export)

3-step modal for creating a new entity.

| Step | Data in | Data out | API |
|---|---|---|---|
| 1. Type + intent | user picks type, describes intent | — | — |
| 2. AI draft | prompt + type | YAML/prose draft | `POST /api/ai/wizard` with `{ type, prompt }` |
| 3. Review + save | edited draft | created entity | `POST /api/core/{kpis\|actions\|brackets\|contracts}` |

For Use Case type, the wizard creates **both** the bracket YAML and a Factsheet skeleton in one pass. Save endpoint: `POST /api/core/draft`.

### 2.6 Settings (new — replaces Studio's Tweaks panel)

Studio-wide preferences persisted per-user in localStorage + `/api/theme`:

| Preference | Stored | API |
|---|---|---|
| Theme (dark/light) | localStorage + user profile | `PUT /api/theme` |
| Density | localStorage | — |
| Font pairing | localStorage | — |
| Accent hue/chroma/lightness | localStorage | — |
| Sidebar default (expanded/collapsed) | localStorage | — |
| AI model preference | user profile | `PUT /api/theme` (or dedicated future route) |

### 2.7 Report Templates tool (separate tool, same shell)

Uses the same token system. The Tweaks panel lives here.

| UI element | Data source |
|---|---|
| T1–T4 template cards | static (page template specs in `core/templates/page_templates/`) |
| Current PBI / Evidence theme preview | `/api/export/theme` GET |
| Theme export | `/api/export/theme` POST with current tweaks state |

---

## 3. Mutation safety

Every mutation route must:

1. Validate the payload against the schema in `tooling/generator/schemas/`.
2. Run the PostToolUse equivalents in-process (`validate_tmdl_style.sh` + `validate_pbir_structure.sh`) for files it touches.
3. Write an audit event via `/api/audit` with `{ actor, action, entity_type, entity_id, diff }`.
4. Return the new entity + list of **cascading patches** the AI engine proposes.

---

## 4. AI endpoints summary

| Endpoint | Purpose |
|---|---|
| `POST /api/ai/wizard` | Draft new entity from type + prompt |
| `POST /api/ai/factsheet-draft` | Reconcile Factsheet ↔ Bracket (cascading AI) |
| `POST /api/ai/chat` | Studio AI sidebar (contextual Q&A) |

All three exist already and don't need new backend work — only UI wiring.

---

## 5. Gaps (things the loader layer does NOT yet give us)

Flagged here so they're explicit. These turn into Phase-2 tasks, **not** inline improvisation.

| Gap | Proposed route / helper | Priority |
|---|---|---|
| "Golden Thread completion score" for Dashboard hero card | `POST /api/core/health` (aggregates catalog + brackets + actions) | P1 |
| Search across all entity types for the Command Palette | `POST /api/core/kpis/search` exists for KPIs — extend to all entities | P1 |
| Entity delete (soft-delete with audit) | `DELETE /api/core/{type}/[id]` | P2 |
| Real-time validation of Bracket YAML in Monaco | JSON schema served at `GET /api/validate/schema/bracket` | P2 |
| Factsheet template for a new Use Case | `GET /api/core/draft?type=factsheet&strategic_kpi_id=…` | P2 |
| Bulk import of KPIs from CSV/Excel | `POST /api/core/import` | P3 |

---

## 6. Do / Don't

- **Do** call loaders in Server Components when possible (they're file-I/O bound and benefit from RSC caching).
- **Do** treat every save as a round-trip: mutate → revalidate → re-read via loader → ask AI for cascading patches.
- **Don't** hold a local copy of the catalog in Zustand "just for speed." The project-store is for **UI** state, not domain data.
- **Don't** paste mock `FRAMEWORK` / `GRAPH` objects from the uploaded JSX into React components. Those are placeholders; this document is the replacement.
