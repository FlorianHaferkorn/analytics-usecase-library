# Claude Code Instructions — ALUCA Studio

## Project Overview

ALUCA Studio is a Next.js SaaS application that serves as the Interaction Layer for the ALUCA Analytics Platform. It provides a visual interface for building, managing, and exporting analytics steering frameworks.

## Architecture

Three-layer separation (Studio only touches the first two):

- **Logic Layer (Core):** `/core/` — YAML specs, JSON schemas, KPI catalog, action codes. SSOT. Never generated, always hand-authored or AI-assisted.
- **Interaction Layer (Studio):** `/studio/` — This Next.js app. Reads Core artifacts, provides UI for editing, validates against schemas, exports to adapters.
- **Execution Layer (Fabric):** `/products/fabric/` — Python orchestrator for TMDL/Power BI. Studio calls adapters but does not contain Python code.

## Key Conventions

### TypeScript
- Strict mode enabled. No `any` types.
- Types in `src/lib/schemas/` are **auto-generated** from `tooling/generator/schemas/*.schema.json`. Never edit them manually. Run `npm run generate:types` to regenerate.
- Use the `@/` path alias for all imports from `src/`.

### Components
- Server Components by default. Only use `'use client'` when needed (interactivity, hooks, browser APIs).
- Dynamic import for heavy client components (Monaco Editor, React Flow).
- No component file should exceed 300 lines. Split into sub-components.

### Data Loading
- Core artifacts are loaded via server-side loaders in `src/lib/core/`.
- Loaders use `node:fs` — they only work in Server Components and Route Handlers.
- Client components receive data as serializable props from server parents.

### State Management
- `zustand` store in `src/lib/store/project-store.ts` is the single source of truth for client-side state.
- Bi-directional sync: Changes in any UI surface (Flow, Editor, Chat) go through the store.

### Design System
- Mint (#00D4AA) / Gold (#FFB800) / Dark Slate (#1E293B) theme.
- 8px grid spacing via CSS custom properties (`--sp-1` through `--sp-8`).
- Use CSS custom properties from `src/styles/globals.css`, not hardcoded colors.
- Token constants in `src/lib/theme/tokens.ts` for JS usage (Framer Motion, etc.).

### Validation
- All Core artifacts validate against JSON schemas in `tooling/generator/schemas/`.
- Runtime validation via Ajv in `src/lib/validation/schema-validator.ts`.
- Never trust user input — always validate YAML against schema before persisting.

## File Structure

```
studio/src/
├── app/              # Next.js App Router pages
│   ├── (studio)/     # Authenticated module pages
│   └── api/          # Route Handlers (AI, Core CRUD, Export)
├── components/       # React components by feature
│   ├── ui/           # Atomic (Button, Card, Badge)
│   ├── flow/         # React Flow nodes and edges
│   ├── editor/       # Monaco YAML editor
│   ├── registry/     # KPI/Action/Bracket tables
│   ├── dashboard/    # 3-30-300 pulse components
│   ├── discovery/    # Source upload, AI chat
│   └── brand/        # Theme editor, layout preview
├── lib/
│   ├── schemas/      # AUTO-GENERATED TypeScript types
│   ├── core/         # Server-side data loaders
│   ├── store/        # Zustand state management
│   ├── validation/   # Schema validation (Ajv)
│   ├── ai/           # AI orchestration (BYOK)
│   ├── delivery/     # Export adapters (Fabric, OSS)
│   └── theme/        # Design tokens
└── styles/           # Global CSS
```

## Commands

```bash
npm run dev            # Start dev server (Turbopack)
npm run build          # Production build
npm run lint           # ESLint
npm run generate:types # Regenerate TS types from JSON schemas
```

## Testing

Before committing:
1. `npm run build` must succeed with zero errors.
2. TypeScript strict — no implicit `any`.
3. Run `npm run generate:types` if any schema in `tooling/generator/schemas/` changed.

## Schema Authority

The JSON schemas in `tooling/generator/schemas/` are the SSOT:
- `usecase_bracket.schema.json` → UseCaseBracket
- `kpi_definition.schema.json` → KpiDefinition
- `action_code.schema.json` → ActionCode
- `data_contract.schema.json` → DataContract
- `layout_330300.schema.json` → Layout330300

Do not redefine these structures. Import from `@/lib/schemas`.

## Secrets

All secret values (API keys, credentials) must be read via the centralized secrets manager:

```ts
import { getSecret } from '@/lib/secrets';
const key = await getSecret('ANTHROPIC_API_KEY');
```

**Never** read secret values directly from `process.env` in application code.
Detection of which provider is active (e.g. `if (process.env.ANTHROPIC_API_KEY)`) is fine — the check is for presence, not value use.

### Provider selection

Set `SECRETS_PROVIDER` in `.env` to one of:

| Value | Adapter | Config required |
|---|---|---|
| `env` (default) | `src/lib/secrets/dev-env.ts` | None — reads `process.env` |
| `azure` | `src/lib/secrets/azure-key-vault.ts` | `AZURE_KEY_VAULT_URL` + Azure credentials |
| `aws` | `src/lib/secrets/aws-secrets-manager.ts` | `AWS_REGION` + AWS credentials |

### Adding a new secret

1. Add the key to `.env.example` (no real value — just the name + comment).
2. Read it with `await getSecret('YOUR_KEY_NAME')` in the consuming module.
3. For Azure/AWS, provision the secret in the target vault under the same name.

### Cloud adapters

The Azure and AWS adapters use dynamic imports so their SDKs are only loaded
when that provider is active.  At build time, `turbopack.resolveAlias` in
`next.config.ts` redirects the missing optional packages to build stubs in
`src/lib/secrets/_stubs/`.  At runtime, `serverExternalPackages` ensures the
real packages are loaded from `node_modules` if installed.

Install optional cloud SDK packages when deploying to cloud:
- Azure: `npm install @azure/keyvault-secrets @azure/identity`
- AWS: `npm install @aws-sdk/client-secrets-manager`
