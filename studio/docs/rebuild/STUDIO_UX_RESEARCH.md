# Studio UX Research — Comparable Tools & Authoring Patterns

**Status:** LOCKED for agent program (2026-05).  
**Audience:** PM, implementers, `quality-verifier`.  
**Prerequisite:** Read after `REBUILD_DECISIONS.md`; use with `DETAIL_IA.md` and `design-reference/`.

**Purpose:** Deep research on how comparable products structure authoring UIs, governance UX, and content-editing patterns — so Studio rebuild decisions are evidence-based, not mockup-only.

---

## 1. Studio positioning (one sentence)

ALUCA Studio is a **Golden-Thread authoring portal**: governed KPIs, action codes, use cases (Factsheet prose + Bracket YAML), lineage, and export — not a consumption BI tool and not a generic data catalog.

No single vendor ships this combination. The target IA is a **deliberate composite** (see §3).

---

## 2. Comparable tools — architecture & UI

### 2.1 Summary matrix

| Tool | Shell / navigation | Browse vs detail | Definitions / lineage / governance | AI assist |
|------|-------------------|------------------|--------------------------------------|-----------|
| **dbt Catalog** | Top nav → Catalog; search + left sidebar | Search → resource page; graph + summary panel | YAML in project; Catalog = discovery + applied lineage | Semantic layer API-first |
| **Looker IDE** | Develop → IDE panels | File browser **and** object browser by type | LookML in editor; health/metadata side panels | Secondary in IDE |
| **Power BI TMDL Web** | Workspace → model → TMDL View | Graphical + code view; View vs Edit | TMDL/PBIP = SSOT; version history | Copilot + diff preview (roadmap) |
| **Metabase Data Studio** | Grid icon → Data Studio | Tables → detail; Library for published assets | Measures/segments; dependency graph | Glossary for people + agents |
| **Atlan / Collibra / Alation** | Search → **asset profile** | Profile tabs + sidebar “at a glance” | Metadata on asset; lineage tab; certification/workflows | Enrichment / docs (Atlan) |
| **ThoughtSpot / Sigma** | Search/workbook-first | Metrics at dataset level | Governed metrics, workbook reuse | Agentic semantic layer; human-validated metrics |
| **Evidence.dev** | File-based IDE | Pages = markdown, not entity CRUD | SQL/markdown; git = governance | AI for schema/docs |
| **Grafana** | Folder → dashboard; **content outline** | Outline tree for panels/rows | Dashboard JSON; not semantic definitions | Panel title/description assist |
| **Backstage** | `/catalog` → `/catalog/:ns/:kind/:name` | Index → **kind-specific entity tabs** | `catalog-info.yaml`; graph = lineage | Scaffolder for create |

### 2.2 dbt Cloud / MetricFlow / Catalog

- **Catalog:** Global search, lineage graph, ERD, health signals, model query history ([Explore projects](https://docs.getdbt.com/docs/explore/explore-projects)).
- **Global navigation** (2025): unified search across projects ([2025 release notes](https://docs.getdbt.com/docs/dbt-versions/2025-release-notes)).
- **Pattern:** Graph + right summary panel; “open in IDE” keeps editing in code context.
- **Studio adopt:** Canvas lineage + summary drawer; selector-style filters for large graphs.
- **Studio avoid:** Plan-gated feature parity; Catalog is read-heavy, not Factsheet authoring.

### 2.3 Looker / LookML IDE

- **Dual browse:** File browser + object browser (model → explore → view) ([Looker IDE](https://cloud.google.com/looker/docs/looker-ide), [Object browser](https://cloud.google.com/looker/docs/object-browser)).
- **Jump:** Ctrl+J to object or file ([Accessing project files](https://cloud.google.com/looker/docs/accessing-project-files)).
- **Governance UX:** Labels, `hidden`, `group_label`, descriptions ([Explore menu](https://cloud.google.com/looker/docs/changing-explore-menu-and-field-picker), [Positive experience](https://cloud.google.com/looker/docs/best-practices/how-to-create-a-positive-experience-for-looker-users)).
- **Studio adopt:** Command palette (⌘K) as primary cross-entity jump; object-kind mental model.
- **Studio avoid:** Explore-menu sprawl (too many top-level explores).

### 2.4 Power BI / Fabric / TMDL

- **TMDL View on Web:** View vs Edit; diff preview; Copilot with preview ([TMDL on web](https://powerbi.microsoft.com/en-us/blog/tmdl-view-on-the-web-preview/)).
- **Studio adopt:** View/Edit + **diff-before-apply** for Bracket YAML and AI patches (execution = Fabric layer).
- **Studio avoid:** Treating Studio as a full semantic model IDE (TMDL stays in `products/fabric/`).

### 2.5 Metabase Data Studio

- **Data Studio:** Tables, Library (published), measures, dependency graph, glossary ([Overview](https://www.metabase.com/docs/latest/data-studio/overview), [Managing tables](https://www.metabase.com/docs/latest/data-studio/managing-tables)).
- **Metrics explorer:** Ad-hoc compare/breakdown ([Metrics explorer](https://www.metabase.com/docs/latest/questions/metrics-explorer)).
- **Studio adopt:** Library tab = curated KPIs; dependency/impact before save; official measure definitions.
- **Studio avoid:** SQL Lab as primary surface.

### 2.6 Governance catalogs (Atlan, Collibra, Alation)

- Certification, owners, domains on asset profile; lineage as **separate tab** ([Atlan asset profiles](https://docs.atlan.com/product/capabilities/discovery/concepts/what-are-asset-profiles)).
- **Studio adopt:** Governance header on every Detail view (owner, status, domain).
- **Studio avoid:** Heavy workflow engines in v1; manual lineage editing (derive from bracket refs).

### 2.7 Backstage (strongest structural analog)

- Catalog index → entity page with kind-specific tabs ([Catalog plugin](https://github.com/backstage/backstage/tree/master/plugins/catalog)).
- **Studio adopt:** `/library` + `/detail/[kind]/[id]` with kinds: `kpi`, `action`, `usecase`, `contract`.

### 2.8 ThoughtSpot / Sigma / Evidence / Grafana

- **ThoughtSpot:** Search-first consumption — **avoid** as Studio shell model ([Agentic semantic layer](https://www.thoughtspot.com/data-trends/agentic-semantic-layer)).
- **Sigma:** Define metrics once at dataset — adopt “single definition, many consumers” ([About metrics](https://help.sigmacomputing.com/docs/about-metrics)).
- **Evidence:** Docs-as-code — adopt for Factsheet + git workflow ([evidence.dev](https://evidence.dev/)).
- **Grafana:** **Content outline** on Canvas — adopt for graph navigation ([Create dashboard](https://grafana.com/docs/grafana/latest/visualizations/dashboards/build-dashboards/create-dashboard/)).

---

## 3. Target information architecture (approved for agent program)

Aligned with [Analytics Studio.html](file:///c:/Users/florianhaferkorn/Downloads/Analytics%20Studio.html) (Studio v3), `REBUILD_DECISIONS.md`, and this research:

```
Shell: Sidebar (4 core routes) + Topbar + Command Palette (⌘K)
├── /overview     — 3s pulse (health, domains, validation status)
├── /library      — 30s registry (kind tabs)
├── /canvas       — lineage graph (+ optional content outline)
└── /detail/[kind]/[id]
    ├── overview    — governance summary
    ├── definition  — entity-specific (see DETAIL_IA.md)
    ├── lineage     — read-only derived graph
    └── export      — adapter preview (later)

Secondary tools:
├── /templates    — Report Templates (T1–T4); Tweaks panel ONLY here (D3)
└── Legacy routes — redirects only (D8), not permanent sidebar clutter
```

**Command palette** carries Discover, Steering, Delivery, etc. — not 12+ sidebar items.

---

## 4. UX methodologies for content authoring

### 4.1 Time layers — 3-30-300

| Layer | Budget | Studio surface | Source |
|-------|--------|----------------|--------|
| 3s | Glance | Overview KPI band, certification counts | [SQLBI 3-30-300](https://www.sqlbi.com/articles/introducing-the-3-30-300-rule-for-better-reports/) |
| 30s | Scan | Library filters, domain bar, table browse | Same |
| 300s | Deep work | Detail tabs, YAML, compare, export | Same; maps `layout_330300` |

### 4.2 Progressive disclosure

- Core nav visible; advanced in Settings, Compare toggle, Wizard steps 2–3.
- Max ~2 levels of nesting for primary tasks ([NN/g progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/)).

### 4.3 Diátaxis (Factsheet vs Bracket)

| Quadrant | Studio artifact | UI |
|----------|-----------------|-----|
| Explanation | Business Factsheet | Prose / MDX tab |
| Reference | Bracket YAML, KPI YAML | Monaco + schema hints |
| How-to | Wizard, validation fixes | Modal / inline help |
| Tutorial | Onboarding, showcases | First-run only |

Do **not** add empty “Tutorial / How-to / Reference / Explanation” top-level nav ([Diátaxis how-to-use](https://www.diataxis.fr/how-to-use-diataxis/)).

### 4.4 Search & discovery

- **Recognition over recall:** Library table + domain facets before search-only ([NN/g search UX](https://uxdesign.cc/ux-for-search-101%EF%B8%8F-2ab4b2f2384d)).
- Search box: top area, ~27–30 char width; faceted filters ([Search UX practices](https://whatifdesign.co/feeds/blog/best-search-ux-design)).
- Command palette: grouped results, keyboard-only path ([Command palette pattern](https://uxpatterns.dev/patterns/advanced/command-palette)).

### 4.5 Data-dense tables

- Toolbar: search, domain filter, export (max ~5 actions) — [Carbon Data Table](https://carbondesignsystem.com/components/data-table/usage/).
- Virtualize KPI registry at 50+ rows — [Fluent DataGrid](https://react.fluentui.dev/?path=/docs/components-datagrid--docs).

### 4.6 KPI / glossary content design

Per governance practice, every KPI surface should lead with:

- Business definition, owner, domain, certification status
- Link to technical implementation (DAX name, grain, unit)
- Downstream use cases / action codes

Sources: [Data catalog glossary](https://thedatagovernor.com/what-is-a-data-catalog/), [Unity Catalog business semantics](https://community.databricks.com/t5/community-articles/define-kpis-once-with-unity-catalog-business-semantics/m-p/157765).

### 4.7 AI human-in-the-loop (HITL)

- Inline diff per proposed change; user Accept/Reject per hunk.
- Never auto-write to `/core/` without schema validation.
- Reference: [VS Code review code edits](https://code.visualstudio.com/docs/copilot/chat/review-code-edits), ThoughtSpot human-validated metrics.

### 4.8 Accessibility

- Tables: proper `th`/`scope`, captions ([W3C Tables](https://www.w3.org/WAI/tutorials/tables/)).
- Interactive grids: roving tabindex, visible focus ([APG Grid](https://www.w3.org/WAI/ARIA/apg/patterns/grid/)).
- All shell actions reachable via keyboard (REBUILD_DECISIONS D9).

---

## 5. Anti-patterns (verifier checklist)

| Anti-pattern | Why reject |
|--------------|------------|
| ThoughtSpot-style search-only shell | Studio is authoring, not consumption |
| Grafana dashboard grid as main editor | Wrong metaphor; use lineage graph |
| 12+ permanent sidebar routes | Cognitive load; violates progressive disclosure |
| AI auto-apply to `/core/` | Governance risk |
| Manual lineage graph editing | Derive from `lineage-builder` + bracket refs |
| Empty Diátaxis section tabs | Navigation debt |
| YAML-only use case (no Factsheet) | Breaks Business Factsheet layer |
| Form-only bracket (no YAML) | Loses git diff and agent compatibility |
| Mock FRAMEWORK data in production views | Violates DATA_WIRING.md |
| Tweaks panel in Studio shell | Settings modal only (D3); Tweaks in Templates |

---

## 6. What to adopt — prioritized

1. **Backstage** — `/library` + `/detail/[kind]/[id]` + kind tabs (`DETAIL_IA.md`).
2. **Looker** — ⌘K jump + object-kind browser in Command Palette.
3. **dbt Catalog** — Canvas graph + right summary + filters.
4. **Metabase** — Library curation, dependency impact, glossary linkage.
5. **Atlan/Collibra** — Governance header on Detail.
6. **Power BI TMDL** — View/Edit + diff before save.
7. **Diátaxis + 3-30-300** — Overview / Library / Detail time budgets.
8. **Carbon/Fluent** — Library table toolbar + virtualization.
9. **Grafana** — Optional content outline on Canvas.
10. **VS Code HITL** — Cascading AI diff panel (Epic 3).

---

## 7. Open product decisions (PM / Flo)

| ID | Question | Options | Blocks |
|----|----------|---------|--------|
| **PD-1** | Overview content | A) Keep admin `FrameworkOverview` B) Mockup dashboard (sparklines, use-case panels) | Epic 4 / Epic 5 in REBUILD_PLAN |
| **PD-2** | Sidebar brand | “ALUCA Studio” vs “Studio / Analytics Framework” (mockup) | Cosmetic; Epic 1 |
| **PD-3** | Comments on KPI Detail | Real audit thread vs defer | Epic 2.3 / Phase 3 |
| **PD-4** | Ask Studio | Wire chat overlay vs hide until Epic 3 | Epic 1.2 |

Default agent assumption until Flo decides: **PD-1 = A** for Epic 1–2; revisit before Epic 4.

---

## 8. Research phase placement in agent program

| When | Agent | Action |
|------|-------|--------|
| **R0 (done)** | `research-validator` | Produced this document |
| **E0 (done)** | Parent / doc agent | `DETAIL_IA.md` |
| **Before Epic 1.1** | `quality-verifier` | Confirm plan references this file; no anti-pattern regressions |
| **Before Epic 3** | `research-validator` | Refresh HITL / AI governance patterns |
| **Before Epic 6** | `research-validator` | Templates + theme export UX |
| **Before GA** | `quality-verifier` | WCAG pass on Library/Detail grids |

---

## 9. Source index

| Topic | URL |
|-------|-----|
| dbt Catalog | https://docs.getdbt.com/docs/explore/explore-projects |
| dbt Semantic Layer | https://docs.getdbt.com/docs/use-dbt-semantic-layer/sl-architecture |
| Looker IDE | https://cloud.google.com/looker/docs/looker-ide |
| Power BI TMDL Web | https://powerbi.microsoft.com/en-us/blog/tmdl-view-on-the-web-preview/ |
| Metabase Data Studio | https://www.metabase.com/docs/latest/data-studio/overview |
| Atlan asset profiles | https://docs.atlan.com/product/capabilities/discovery/concepts/what-are-asset-profiles |
| Backstage catalog | https://github.com/backstage/backstage/tree/master/plugins/catalog |
| NN/g progressive disclosure | https://www.nngroup.com/articles/progressive-disclosure/ |
| SQLBI 3-30-300 | https://www.sqlbi.com/articles/introducing-the-3-30-300-rule-for-better-reports/ |
| Diátaxis | https://diataxis.fr/ |
| Carbon data table | https://carbondesignsystem.com/components/data-table/usage/ |
| W3C tables a11y | https://www.w3.org/WAI/tutorials/tables/ |
| VS Code AI diff review | https://code.visualstudio.com/docs/copilot/chat/review-code-edits |
| Command palette | https://uxpatterns.dev/patterns/advanced/command-palette |

---

## Change log

| Date | Change |
|------|--------|
| 2026-05-29 | Initial research persist (R0); agent program Epic R0+E0 |
