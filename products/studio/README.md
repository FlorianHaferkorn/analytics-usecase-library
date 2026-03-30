# ActionReady Studio

Next.js web application for designing and exploring the Golden Thread analytics framework.

## Pages

| Page | URL | Description |
|------|-----|-------------|
| **Explorer** | `/` | Browse KPIs, Use Cases, and Action Codes from the registry |
| **Studio** | `/studio` | Triple-pane use case designer (sources · chat · editor) |
| **Brand** | `/brand` | Brand token designer with BrandSpec YAML export |

## Quick Start

### 1. Prerequisites

- Node.js 20+
- The registry must be built first (from repo root):

```bash
python tooling/ontology/registry_builder.py
```

### 2. Install & Run

```bash
cd products/studio
npm install
cp .env.example .env        # then add your LLM API key
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 3. Configure LLM (optional but recommended)

Add **one** of the following to `products/studio/.env`:

```bash
# Google Gemini (recommended — free tier available)
GEMINI_API_KEY=your-key-here

# OpenAI
OPENAI_API_KEY=your-key-here

# Azure OpenAI
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://YOUR_RESOURCE.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

Without an LLM key, the Explorer and YAML editor still work — only the discovery chat is disabled.

## How the Studio Works

```
Sources pane          Chat pane             Studio pane
──────────────        ──────────────        ──────────────────────
Add URLs or text  →   Ask the LLM    →      Apply suggestions to
as grounding          about use cases,       the Living Tree &
context               KPIs, and actions      YAML Editor
                                            ↓
                                            Export UseCase_Bracket.yaml
                                            to core/usecases/core/
```

### Golden Thread model

```
Use Case (id, title, domain)
└── Strategic KPI (North Star — 3-second signal)
    ├── Influencing KPIs (diagnostic levers — 30-second layer)
    └── Action Codes (prescriptions — 300-second layer)
```

## Architecture

```
products/studio/
├── src/app/
│   ├── page.tsx               # Explorer
│   ├── studio/page.tsx        # Studio (triple-pane)
│   ├── brand/page.tsx         # Brand Designer
│   └── api/
│       ├── registry/          # Reads tooling/ontology/out/master_registry.json
│       ├── chat/              # LLM proxy (Gemini / Azure / OpenAI)
│       ├── export/            # Writes UseCase_Bracket.yaml to repo
│       └── fetch-url/         # Fetches and strips HTML from URLs
├── src/components/
│   ├── layout/Header.tsx
│   ├── studio/                # SourcesPane, ChatPane, LivingTree, YamlEditor
│   └── ui/                    # Badge, Button
├── src/lib/                   # registry.ts, llm.ts, bracket.ts
├── src/store/studio.ts        # Zustand global state
└── src/types/                 # Registry, bracket TypeScript interfaces
```

## Production Build

```bash
npm run build
npm start
```

Or deploy to any Node.js host (Vercel, Railway, etc.). Set `REPO_ROOT` env var to the
absolute path of the analytics-usecase-library root if the file system is accessible.
