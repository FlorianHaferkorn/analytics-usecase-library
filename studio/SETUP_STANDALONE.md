# ActionReady Studio — Standalone-Setup (lokal-first, BYO-Key) · I-6.5

Fresh-Install-Durchlauf: das Cockpit läuft **lokal-first** auf der eigenen Maschine,
mit **eigenem LLM-Key** (BYO-Key). Keine Cloud-Abhängigkeit nötig.

## Voraussetzungen
- **Node.js** ≥ 20 (Next.js 16) + npm
- **Python 3** auf dem PATH (oder via `SUPERVERSION_PYTHON` gesetzt) — für die governte
  Generate/Gate-Bridge (ADR-0007). Aufruf aus dem **Repo-Wurzelverzeichnis**.
- Ein LLM-Key eines unterstützten Providers (Priorität Google → Anthropic → OpenAI).

## Schritte
1. **Abhängigkeiten installieren** (im `studio/`-Ordner):
   ```bash
   npm install
   ```
2. **BYO-Key setzen** (in `studio/.env`, vgl. `.env.example`). Einer genügt:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-…      # oder
   OPENAI_API_KEY=sk-…             # oder
   GOOGLE_API_KEY=…
   # optional: SECRETS_PROVIDER=env (Default) | azure | aws
   ```
   Keys werden nie direkt aus `process.env` gelesen, sondern über
   `getSecret()` (siehe `studio/CLAUDE.md` → Secrets); für `azure`/`aws` liegt der
   Key im jeweiligen Vault unter demselben Namen.
3. **Starten:**
   ```bash
   npm run dev      # Entwicklung (Turbopack)
   # oder: npm run build && npm start
   ```
4. **Readiness prüfen** — der Preflight bestätigt den Fresh-Install-Durchlauf:
   ```bash
   curl -s localhost:3000/api/setup | jq
   ```
   Antwort = `SetupReadiness`: `ready` + pro Pflicht-Check (`llm_key`,
   `secrets_provider`, `python_bridge`, `core_artifacts`) ein Status; `auth` ist
   optional (Dev-Credentials reichen lokal). Bei `ready:false` nennt `blockers`
   genau den fehlenden Schritt.

## Bridge-Probe (ohne UI)
Die Python-Seite lässt sich direkt prüfen (aus der Repo-Wurzel):
```bash
python3 -m tooling.superversion.bridge ping
# {"ok": true, "engines_available": [...], "targets_available": ["pbir","tmdl"]}
```
Ist die Bridge offline, degradiert das Studio **ehrlich** (Generierung „nicht
gate-validiert", ADR-0007 R5) statt ein Ergebnis vorzutäuschen.

## Auth (lokal)
Ohne `GITHUB_ID`/`GITHUB_SECRET` läuft NextAuth im **Dev-Credentials**-Modus
(lokal-first ok). Für geteilten/Server-Betrieb GitHub-OAuth setzen — das ist Z4
(I-9), nicht Teil des Standalone-Durchlaufs.
