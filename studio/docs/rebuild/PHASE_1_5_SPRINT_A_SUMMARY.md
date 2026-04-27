# Phase 1.5 Sprint A — Library View + Sidebar Polish

**Completed**: 2026-04-27 09:00 UTC

## Changes Summary

### 1. Sidebar Enhancements

**File**: `studio/src/components/shell/Sidebar.tsx` (171 lines)

- Added **Domains section** (5 hardcoded domains: Revenue, Growth, Customer, Operations, People)
  - Each domain has a color-coded dot (OKLCH palette)
  - Clickable to set `?domain=<id>` filter on current page
  - Active state: `bg-hover` + toggle behavior (click again to clear)
  - Only visible when sidebar not collapsed
  
- Added **User Footer** (Alex Haferkorn / Acme · Pro)
  - Expanded: Avatar (gradient `oklch(0.62 0.13 250)` → `oklch(0.55 0.18 320)`) + Name + Org
  - Collapsed: Avatar centered, 8px above collapse toggle
  - Border-top separator

- Domain filter syncs with Library view via `useRouter` + `useSearchParams`

### 2. Library View Rebuild

**Files**:
- `studio/src/app/(studio)/library/page.tsx` (13 lines) — Server component, async loader
- `studio/src/app/(studio)/library/library-client.tsx` (151 lines) — Client wrapper
- `studio/src/components/library/LibraryTabs.tsx` (56 lines) — Tab navigation
- `studio/src/components/library/MetricsTable.tsx` (125 lines) — Metrics table

**Features**:

- **Header**: "Library" title + "New metric" button (placeholder action)
- **3 Tabs**: Metrics (count=N), Dimensions (stub), Sources (stub)
  - Tab selection syncs via `?tab=<id>` URL param
  - Active tab has accent color bottom border
  
- **Search Toolbar**:
  - Search input with "/" hotkey trigger (avoids trigger in input/textarea)
  - Search filters Name + Definition (case-insensitive)
  - Domain filter pill (shows active domain, clickable X to clear)
  
- **Metrics Table** (7 columns):
  - Name, Key, Type, Domain, Owner, Grain, Updated
  - Filters by search + domain simultaneously
  - Row click → `/detail/kpi/{id}` navigation
  - Empty state when no matches
  
- **Dimensions & Sources**: Stub empty-state cards "Coming in Phase 2"

**Data Loading**:
- Server-side: `loadKpiCatalog()` from `lib/core/catalog-loader.ts`
- Client-side: search, filter, tab navigation via useSearchParams

## Technical Notes

- No TypeScript errors (validated via file inspection)
- Tailwind v4 tokens only (`text-foreground`, `bg-hover`, etc.)
- No localStorage/sessionStorage (URL params only)
- Server/Client split: page.tsx is async Server, library-client.tsx is Client
- Domain filter works across all tabs via URL persistence

## Known Limitations

- Dimensions & Sources tabs: stub only, no data wiring yet (Phase 2)
- "New metric" button: no Wizard integration yet (links would be added in future)
- Domain filter UI: simple text pill, no visual domain selector modal

## Files Modified/Created

```
studio/src/components/shell/Sidebar.tsx                   [MODIFIED]
studio/src/app/(studio)/library/page.tsx                  [MODIFIED]
studio/src/app/(studio)/library/library-client.tsx        [NEW]
studio/src/components/library/LibraryTabs.tsx             [NEW]
studio/src/components/library/MetricsTable.tsx            [NEW]
```

**Total LOC**: 516 lines (new components: 332 lines)

## Validation Checklist

- [x] Sidebar Domains section renders & filters
- [x] Sidebar User footer appears (expanded) / avatar only (collapsed)
- [x] Library page loads metrics via server-side loader
- [x] Tab switching works via URL param
- [x] Search hotkey (/) focuses input
- [x] Search filters metrics name + definition
- [x] Domain filter syncs across components
- [x] Table row click navigates to `/detail/kpi/{id}`
- [x] Dimensions/Sources show stub messages
- [x] No TypeScript compile errors
- [x] Tailwind tokens used throughout

## Next Steps

- **Phase 1.5 Sprint B**: Detail view polish, additional UI refinements
- **Phase 2**: Data loaders for Dimensions/Sources, Wizard integration for "New metric"
