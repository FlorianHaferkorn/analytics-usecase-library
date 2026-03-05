# Golden Thread Discovery Studio

Inception UI for the Golden Thread: sources, discovery chat, Living Tree, and export into SSOTs. Optional tool; not part of Stage 1 CI.

## Purpose

- **Greenfield:** Start from documents/URLs; AI suggests strategy and KPIs; user confirms and extends.
- **Brownfield:** Import existing structures (KPI lists, report inventory, semantic model metadata); map to framework IDs; transform into SSOTs.

Single global state (`DiscoverySession`) drives Tree and YAML editor; Golden Thread (Strategic KPI → Influencing KPIs → Action Codes) stays consistent.

## Key Paths

- Repo root: configurable (default: parent of `tooling/`).
- Registry: `tooling/ontology/out/master_registry.json` (KPI IDs, action code IDs, use cases).
- Bracket schema: `tooling/ai/schemas/usecase_bracket.schema.json`.
- Export target: `core/usecases/core/<id>_*/UseCase_Bracket.yaml` (configurable).

## Run (MVP)

From repo root:

```bash
streamlit run tooling/golden_thread_discovery_studio/app.py
```

## Sessions

Optional: save/load session to `sessions/<session_id>.json`. Add `sessions/*.json` to `.gitignore` in this folder to avoid committing session dumps.

## Phases

1. State + triple-pane layout + manually fillable Tree + YAML display (State → YAML).
2. YAML edit → parse → State → Tree (bidirectional).
3. Chat integration (messages + Apply suggestion → State).
4. Document/URL upload + indexing + traceability.
5. Approve workflow, SSOT confirmation, Pre-Export-Gate, Export.
6. Brownfield: structure import + mapping → SSOTs.

## Dependencies

Python 3.10+, streamlit, pyyaml, jsonschema, openai. See `requirements.txt` in this folder.

**Discovery Chat (LLM):** Set one of (priority: Gemini → Azure → OpenAI):
- **Google Gemini:** `GOOGLE_API_KEY` or `GEMINI_API_KEY`; optional `GEMINI_MODEL` (default `gemini-2.5-flash`). Same key can be used for other Google APIs if Gemini is enabled. See [docs/GEMINI_GCP_SETUP.md](docs/GEMINI_GCP_SETUP.md) to enable the API in your GCP project.
- **OpenAI:** `OPENAI_API_KEY`; optional `OPENAI_MODEL` (default `gpt-4o-mini`).
- **Azure OpenAI:** `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` (e.g. `gpt-4o`).  
If none is set, chat shows a short hint instead of calling the API.
