# ActionReady Studio

Next.js app that serves as the **Interaction Layer** for the Analytics Strategy-to-Action Framework. Visual editor over the tool-agnostic artifacts in `core/`.

## Quick start

```bash
cd studio
npm ci
# .env.local: ALUCA_REPO_ROOT=/absolute/path/to/analytics-usecase-library
npm run dev      # http://localhost:3000
```

## Useful scripts

| Command | What it does |
|---|---|
| `npm run dev` | Dev server (Turbopack) |
| `npm run build` | Production build |
| `npm run lint` | ESLint |
| `npm run lint:tokens` | Verify design tokens against the system |
| `npm run generate:types` | Regenerate TS types from JSON schemas in `tooling/generator/schemas/` (generated set, or name schemas: `npm run generate:types -- data_contract.schema.json`) |
| `npm test` | Vitest unit tests |
| `npm run test:e2e` | Playwright end-to-end tests |
| `npm run mcp` | Run the MCP server locally |

## Architecture (one paragraph)

Studio is the **middle of three layers**:

- **Logic Layer** — `/core/` (YAML, JSON schemas, KPI catalog, action codes). Source of truth.
- **Interaction Layer** — `/studio/` (this app). Reads `core/`, validates, edits, exports.
- **Execution Layer** — `/products/fabric/`, `/products/open_source_stack/`. Renders to a target platform.

Studio never writes to the Execution Layer directly — it calls adapters.

## Conventions

- TypeScript strict; no `any`.
- Types in `src/lib/schemas/` are **auto-generated** — never hand-edit. Run `npm run generate:types` after changing any schema.
- Server Components by default; `'use client'` only when needed.
- Single Zustand store: `src/lib/store/project-store.ts`.
- Design tokens via CSS custom properties in `src/styles/globals.css`; JS access via `src/lib/theme/tokens.ts`.

Full conventions and architecture: [`CLAUDE.md`](CLAUDE.md).

## Where things live

```
studio/src/
├── app/              # Next.js App Router (pages, route handlers)
├── components/       # React components by feature (ui, flow, editor, registry, …)
├── lib/
│   ├── schemas/      # AUTO-GENERATED TS types
│   ├── core/         # Server-side loaders for /core artifacts
│   ├── store/        # Zustand state
│   ├── validation/   # Ajv schema validation
│   └── theme/        # Design tokens
└── styles/           # Global CSS
```

## Before you push

1. `npm run build` — must succeed with zero TS errors.
2. `npm test` — Vitest must pass.
3. If you changed a JSON schema: `npm run generate:types`.

For the broader repo, see [`../ONBOARDING.md`](../ONBOARDING.md).
