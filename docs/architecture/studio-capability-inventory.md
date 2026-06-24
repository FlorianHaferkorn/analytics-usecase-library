---
last-reviewed: 2026-06-24
shelf-life-days: 90
---
# Studio-Capability-Inventur + Soll-Schnitt (I-6.1)

> **Gate-Dokument für Initiative I-6 (Studio als Kunden-Cockpit).** Hält den
> Ist-Stand des Studio (`studio/`) gegen den Soll-Schnitt und leitet daraus den
> konkreten Schnitt für I-6.2–6.6 ab. Prüfung der Task: Agent-Inventur (durchgeführt
> 2026-06-24, Evidenz mit `file:line` im Studio-Subtree). **Kein Code-Build** —
> reine Discovery (Opus-Task laut Plan §0.56).

| Feld | Wert |
|---|---|
| Stand | 2026-06-24 |
| Rolle | Inventur + Soll-Schnitt für I-6 |
| Methode | Agent-Inventur über `studio/src/**` (Routen, API, lib, Tests, Build) |
| Ergebnis | Studio ist **real** (kein Demo), aber **generiert an der governten Python-Superversion vorbei** → zentrale Architektur-Entscheidung für I-6.2/6.3 |

---

## 1. Ist-Stand je Soll-Bereich (EXISTS / PARTIAL / MOCK / ABSENT)

| Bereich | Verdikt | Belege (Studio-Subtree) |
|---|---|---|
| **Blueprint / Authoring** | **EXISTS** | `/blueprint` Steering-Hub (`src/app/(forge)/blueprint/page.tsx`); Bracket-Create schreibt YAML + Factsheet-Template (`/api/core/brackets` POST, ID-Regex `^[A-Z]{2,3}-\d{3}$`, audit-logged); AI-Wizard real, multi-Provider (`/api/ai/wizard`, `src/lib/ai/orchestrator.ts`); Ajv-Runtime-Validierung gegen `tooling/ai/schemas/*.schema.json` |
| **Generate** | **EXISTS — aber Shadow-Pfad** | Drei Export-Adapter (Fabric/OSS/CI-CD) über IR-Builder (`src/lib/delivery/ir-builder.ts`) → `fabric-adapter.ts` (TMDL/PBIP), `oss-adapter.ts` (SQL/Evidence), `cicd-adapter.ts`. **In TypeScript re-implementiert**, ruft die Python-Superversion (`from_aluca`, TMDL/PBIR-Emitter, e2e_smoke) **nicht** auf. CI-CD-Adapter trägt TODO „integrate with studio CLI validator". |
| **Approvals / Freigabe-Schleuse** | **EXISTS** | State-Machine `draft→review→approved/rejected→deprecated` (`src/lib/governance/approval-workflow.ts`, `VALID_TRANSITIONS`); SQLite `bracket_lifecycle`; Self-Approval-Sperre; Admin-Gate via RBAC (`/api/governance/approve`); jede Transition audit-logged |
| **Catalog** | **EXISTS** | KPI-/Bracket-/Action-/Contract-Browser, server-side aus Core-Artefakten geladen (`src/lib/core/*-loader.ts`); Tabs + Suche + Detail-Routen (`/catalog`, `/library`, `/detail/[type]/[id]`) |

**Querschnitt:** Auth (NextAuth, GitHub-OAuth + Dev-Credentials), RBAC (editor/viewer/admin), Audit-Chain, Secrets-Adapter (env/Azure/AWS), Multi-Tenant-Gerüst (Default-Projekt real, Multi-Projekt scaffolded). Tech: Next.js 16 / React 19 / Vitest. **Build-Status:** Dependencies nicht installiert (`npm install` nötig); E2E (Playwright) konfiguriert, aber **keine** E2E-Suite.

### Test-/Reife-Marker (ehrlich)
- **Fallback-Degradation:** Report-Export fällt auf `SAMPLE_KPIS` zurück, wenn Bracket nicht gefunden — graceful, aber sample-data-Pfad existiert.
- **Test-only (nicht prod-verdrahtet):** `spine-enforcer.ts`, `contrast-checker.ts`, `notifications/{execution-log,persistence-tracker,volume-guard}.ts`, `plugins/version-check.ts`.

---

## 2. Soll-Schnitt (was das Cockpit für „customer-operable" können muss)

Aus Plan §I-6 + §8 (Reihenfolge-Logik) abgeleitet:

1. **Vor dem Core (I-6.2):** Quellen/gov/eng/arch-Realität verbinden (Ingest) — der Kunde bringt seine Datenrealität an, nicht nur ein leeres Bracket.
2. **Nach dem Core (I-6.3):** Target-Wahl + Deploy-Handoff + **Gate-Report sichtbar** — der Golden-Thread-Gate-Status (I-3.4) und das E2E-Ergebnis (I-3.5) müssen im UI erscheinen.
3. **E2E im Studio (I-6.4):** Authoring → Freigabe-Schleuse → Generate → **Validate** → Deliverable, vom Kunden ohne Builder durchlaufbar.
4. **Standalone/Onboarding (I-6.5):** lokal-first, BYO-Key, Fresh-Install-Durchlauf.
5. **Health (I-6.6):** Modell-Routing + Token-Budget je Schritt sichtbar/messbar.

---

## 3. Zentrale Lücke (die Entscheidung, an der I-6 hängt)

**Das Studio generiert über einen TypeScript-Shadow-Pfad, nicht über die governte Python-Superversion (I-1…I-5).**

- Python-Core liefert: `from_aluca`→`CanonicalModel` (I-1), TMDL/PBIR-Emitter + offizielle Validatoren (I-3.2/3.3), Golden-Thread-Gate (I-3.4), E2E-Smoke (I-3.5), gov/eng/arch-Engines (I-5.3), Tool-Packs (I-5.4).
- Studio liefert: eigener IR-Builder + `fabric-adapter.ts`/`oss-adapter.ts` in TS — **zweite Wahrheit** für „was ein Bracket erzeugt".

Das verletzt das Golden-Thread-Prinzip (eine governte Quelle, referenzieren statt neu definieren) und doppelt genau die Arbeit, die I-1…I-5 gehärtet + getestet haben. Es ist **keine** sofort zu fixende Code-Lücke, sondern die **Architektur-Frage von I-6.2/6.3**:

> **Soll der Studio-Generate-Pfad auf den Python-Core andocken (Studio ruft `from_aluca`/E2E-Smoke statt TS-Adapter) — oder bleibt der TS-Pfad die UI-Schnellbahn und der Python-Core das CI-/Service-Gate?**

Diese Frage ist [QA/SA]-würdig (Opus) und sollte **vor** I-6.2-Code entschieden werden, sonst baut I-6.2/6.3 auf der falschen Naht.

---

## 4. Schnitt für I-6.2–6.6 (Backlog-Vorschlag, kein Commitment)

| Task | Konkreter Schnitt aus dieser Inventur | Hängt an Entscheidung §3 |
|---|---|---|
| **I-6.2** „Vor dem Core" | Ingest-Panel an `from_aluca`-Eingang + Quellen-Realität (gov/eng/arch-Engines I-5.3 als Vorab-Audit im UI) | ja |
| **I-6.3** „Nach dem Core" | Target-Wahl an die **Python**-Target-Registry (ADR-0006) statt TS-Adapter; **Gate-Report** (Golden-Thread I-3.4 + E2E I-3.5) im UI sichtbar | ja (Kern der Frage) |
| **I-6.4** E2E im Studio | Kunde-ohne-Builder-Durchlauf; reuse Freigabe-Schleuse (existiert) + Validate-Schritt (E2E-Smoke I-3.5) | ja |
| **I-6.5** Onboarding/Standalone | BYO-Key existiert (Secrets-Adapter); Fresh-Install-Durchlauf + lokal-first dokumentieren/härten | nein |
| **I-6.6** Health | Token-Budget/Modell-Routing je Schritt — heute kein Budget-Tracking im Studio sichtbar | nein |

**Reuse statt Neubau:** Approvals (I-6.4) und Catalog sind bereits real — nicht neu bauen, nur einbinden. Authoring ist real — I-6.2 ergänzt nur den Ingest-Vorlauf.

---

## 5. Offene Entscheidung (an den Maintainer)

**E-1 — Generate-Naht (§3): ENTSCHIEDEN (2026-06-24, [`adr/0007-studio-generate-docks-onto-superversion-core.md`](adr/0007-studio-generate-docks-onto-superversion-core.md)).**
Studio-Generate **dockt auf den Python-Core**: das Studio ruft `from_aluca` →
`targets.render` (ADR-0006) → Golden-Thread-Gate (I-3.4) → E2E-Smoke (I-3.5) über
eine dünne Brücke und zeigt deren Artefakte + Gate-Report. Die TS-Adapter werden zu
**Preview-only/nicht-autoritativ** degradiert (Core gewinnt bei Divergenz); offline
zeigt das Studio nur Preview mit „nicht gate-validiert" (keine Fake-Green-Auslieferung).
I-6.2/6.3 implementieren die Brücke (Transport offen: Subprocess/CLI vs. lokales HTTP).
