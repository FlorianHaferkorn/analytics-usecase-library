# Studio Detail IA — Entity Kinds, Routes & Tabs

**Status:** LOCKED for implementation slices (2026-05).  
**Authority:** Extends `REBUILD_DECISIONS.md` §D5–D7 and `DATA_WIRING.md` §2.4.  
**Research basis:** `STUDIO_UX_RESEARCH.md` (Backstage + Looker + governance catalogs).

---

## 1. URL contract

| Pattern | Example | Notes |
|---------|---------|-------|
| Library index | `/library` | Query: `?tab=`, `?domain=`, `?q=` |
| Detail page | `/detail/[kind]/[id]` | `kind` = slug below; `id` = catalog/bracket/action/contract id |
| Canvas deep link | `/canvas?focus=[kind]:[id]` | Optional; highlights node |
| Compare mode | `/detail/usecase/[id]?compare=1` | Factsheet \| Bracket split (Use Case only) |

**Invalid:** `/detail` without segments (sidebar “Detail” nav → `/library` or last entity).  
**Redirects (Epic 1.3):**

| Legacy | Target |
|--------|--------|
| `/catalog` | `/library?tab=kpis` |
| `/catalog/[kpiId]` | `/detail/kpi/[kpiId]` |
| `/registry/brackets/[id]` | `/detail/usecase/[id]` |
| `/discover`, `/blueprint`, … | Contextual; prefer ⌘K + redirect doc in PROGRESS |

---

## 2. Entity kinds (`kind` slug)

| `kind` | Source (SSOT) | Library tab | `id` format |
|--------|---------------|-------------|-------------|
| `kpi` | `core/kpi_catalog/*.yaml` | KPIs (label: Metrics in mockup v3) | `kpi_id` e.g. `NRR` |
| `action` | `core/action_codes/*.yaml` | Action Codes | action `id` |
| `usecase` | `core/usecases/**/UseCase_Bracket.yaml` | Use Cases | bracket `id` e.g. `COM-001` |
| `contract` | `core/data_contracts/**/*.yaml` | Sources | contract `id` |

**Dimensions tab (Library):** Derived view over contracts — not a separate `kind`; rows link to `contract` or filter KPIs by dimension refs (`DATA_WIRING.md` §2.3).

---

## 3. Governance header (all kinds)

Rendered at top of every Detail view (Atlan/Collibra pattern):

| Field | KPI | Action | Use Case | Contract |
|-------|-----|--------|----------|----------|
| Title | `kpi_key` / business name | `name` | `title` | `label` / id |
| Status pill | certified / review / draft (from `metadata_quality`) | lifecycle if present | factsheet + bracket sync status | published / draft |
| Domain | `domain_tag[0]` | — | from bracket/strategic KPI | domain tag |
| Owner | `governance.business_owner` | owner field | RACI from bracket | steward |
| Ref mono | `technical.dax_name` | `id` | `id` | contract id |

**No mock personas** in production UI — use loader fields or “Unassigned”.

---

## 4. Tab matrix by kind

### 4.1 KPI (`/detail/kpi/[id]`)

| Tab | ID | Content | Editable | Loader / API |
|-----|-----|---------|----------|--------------|
| Overview | `overview` | Definition summary, refs, governance | Partial inline (name/desc) | `loadKpi` |
| Definition | `definition` | Full YAML or structured fields | Yes | `PUT /api/core/kpis` |
| Lineage | `lineage` | Upstream contracts, downstream use cases | No | `lineage-builder`, filters |
| Comments | `comments` | Thread (optional v1: stub) | Yes (later) | audit / defer PD-3 |
| History | `history` | Audit events | No | `/api/audit` |

Mockup v3 KPI Detail maps to Overview + Definition; Comments/History per mockup — implement stub → audit in Epic 3+.

### 4.2 Action Code (`/detail/action/[id]`)

| Tab | ID | Content | Editable |
|-----|-----|---------|----------|
| Overview | `overview` | Trigger KPI, severity, summary | No |
| Playbook | `definition` | YAML playbook | Yes — `PUT /api/core/actions` |
| Lineage | `lineage` | Use cases referencing this action | No |
| History | `history` | Audit | No |

### 4.3 Use Case (`/detail/usecase/[id]`) — primary Golden Thread surface

| Tab | ID | Content | Editable | Notes |
|-----|-----|---------|----------|-------|
| Overview | `overview` | Rolled-up factsheet + bracket summary | No | Diátaxis: orientation |
| Factsheet | `factsheet` | Business_Factsheet.md | Yes (MDX) | Diátaxis: explanation |
| Bracket | `bracket` | UseCase_Bracket.yaml (Monaco) | Yes | Diátaxis: reference |
| Data Contracts | `contracts` | Referenced contracts list | No | Links to `contract` detail |
| History | `history` | Audit | No | |

**Compare toggle (Topbar):** splits Factsheet | Bracket 50/50; state `?compare=1` (REBUILD_DECISIONS §D5).

**Cascading AI (Epic 3):** on save of Factsheet or Bracket → diff on other tab; never auto-apply.

### 4.4 Data Contract (`/detail/contract/[id]`)

| Tab | ID | Content | Editable |
|-----|-----|---------|----------|
| Overview | `overview` | System, owner, tables | No |
| Contract | `definition` | YAML contract | Yes — `PUT /api/core/contracts` |
| Lineage | `lineage` | KPIs referencing fields | No |
| History | `history` | Audit | No |

---

## 5. Library ↔ Detail navigation

| Event | Behavior |
|-------|----------|
| Row click | `router.push(/detail/${kind}/${id})` |
| Back link | “Back to library” → `/library?tab=${tab}` preserve domain filter |
| ⌘K result | Same URL pattern; palette items use `kind` + `id` |
| Canvas node | Popover → “Open detail” → same URL |

---

## 6. Command palette entity shape

```typescript
// Serializable for server → client (extends existing SerializablePaletteItem)
type PaletteEntity = {
  kind: 'kpi' | 'action' | 'usecase' | 'contract';
  id: string;
  label: string;
  sub?: string; // domain or path hint
  href: `/detail/${kind}/${id}`;
};
```

**Deprecate** palette links to `/catalog?kpi=`, `/steering?bracket=` after Epic 1.3.

---

## 7. TypeScript stub (optional reference)

Implementers may add `studio/src/lib/studio/entity-ia.ts`:

```typescript
export const STUDIO_ENTITY_KINDS = ['kpi', 'action', 'usecase', 'contract'] as const;
export type StudioEntityKind = (typeof STUDIO_ENTITY_KINDS)[number];

export function detailPath(kind: StudioEntityKind, id: string): string {
  return `/detail/${kind}/${encodeURIComponent(id)}`;
}
```

Not required for R0/E0 — documentation is authoritative until Epic 1.1.

---

## 8. Verifier acceptance (DETAIL_IA)

- [ ] All new Detail links use `/detail/[kind]/[id]` with kind from §2.
- [ ] Use Case has Factsheet + Bracket tabs (not permanent split without compare toggle).
- [ ] Lineage tabs are read-only (no drag-edit graph in Detail).
- [ ] Governance header uses loader data (no hardcoded “Alex Haferkorn”).
- [ ] Library row click matches kind slug.

---

## Change log

| Date | Change |
|------|--------|
| 2026-05-29 | Initial E0 contract for agent program |
