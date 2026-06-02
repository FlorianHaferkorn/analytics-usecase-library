# Studio API inventory

**Updated:** 2026-05-31 (Epic 8 cleanup pass)

## Active routes (referenced from `studio/src` UI)

| Route | Methods | Used by |
|-------|---------|---------|
| `/api/ai/chat` | POST | Chat, discovery, AI fields |
| `/api/ai/factsheet-draft` | POST | Wizard, Use Case Detail |
| `/api/ai/wizard` | POST | New Element wizard (draft) |
| `/api/ai/wizard/save` | POST | New Element wizard (persist) |
| `/api/audit` | GET | Activity timeline, Overview |
| `/api/brand-spec` | PATCH | Brand Lab / Templates Tweaks |
| `/api/core/actions` | GET | Library |
| `/api/core/brackets` | GET | Discovery, steering |
| `/api/core/brackets/[id]` | GET, PUT | Detail, steering |
| `/api/core/draft` | POST | Discovery extraction |
| `/api/core/discovery/review` | POST | Discovery |
| `/api/core/kpis` | GET, PUT | Library, KPI Detail |
| `/api/core/presets/[kpiId]` | GET | ROI panel |
| `/api/export/excel` | GET | Steering export |
| `/api/export/report` | POST | Steering export |
| `/api/export/theme` | POST | Templates / Brand Lab |
| `/api/factsheets/[bracketId]` | GET, PUT | Use Case Detail |
| `/api/governance/*` | * | Registry governance panel |
| `/api/health` | GET | Registry health |
| `/api/plugins` | GET, POST, DELETE | Plugins page |
| `/api/project` | POST | Project selector |
| `/api/project/list` | GET | Project switcher |
| `/api/theme` | PUT | Theme persistence |
| `/api/validate/drift` | GET | Drift, Overview |

## Deprecated / duplicate (no UI references)

These **project-scoped duplicates** mirror top-level `/api/core/*` and `/api/export/*` routes. Keep for external integrations until removed; prefer non-prefixed routes for new work.

- `/api/projects/[projectId]/core/*`
- `/api/projects/[projectId]/export/*`
- `/api/projects/[projectId]/governance/*`

Planned archive location: `studio/archive/api/projects/` (move in a dedicated chore PR to avoid breaking unknown consumers).

## Auth

All mutating routes use `requireAuth()` from `@/lib/auth/session`.
