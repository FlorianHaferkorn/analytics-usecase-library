# Umsetzungsplan — ALUCA Superversion (ALUCA × Meridian)

> **Heimat-Repo:** `analytics-usecase-library` (ALUCA). Meridian-Engine wird eingezogen
> (vendored/dependency), nicht geforkt. **Scope:** komplett bis Z4. **Taktung:**
> geschichtet — **I-Blöcke** (Initiative, eine Wette + eine Messgröße) → **Tasks**
> (= je eine Claude-Code-Session, 1–3 h, isoliert startbar). **Stand:** 2026-06-22.
> **Grundlagen:** `PRODUCT_PLAN.md` (Phasen/Zielbild), `SYNERGY_ALUCA_MERIDIAN.md`
> (Architektur), `KPI_Framework_Discovery_ALUCA_EN_v3.xlsx` (ehrlicher Reifegrad).
> Doktrin: `GOI_DOKTRIN.md` §9 (DoD), `CLAUDE.md`/`AGENTS.md` (Drift-Gate, TMDL-Hardrules).

---

## 0. Wie dieser Plan zu lesen & auszuführen ist

### 0.1 Für die ausführende Claude-Code-Session (Pflicht-Protokoll)
Jede Task ist **eine Session**. Vor Beginn:
1. **Lies zuerst** `AGENTS.md` → `CLAUDE.md` → diesen Plan (nur den eigenen Task-Block) →
   die in der Task genannten Detail-Dateien. **Nicht** den ganzen Repo-Baum scannen.
2. **Branch:** `superversion/<task-id>-<kurzslug>` (z. B. `superversion/I1-2-cost-bracket`).
3. **Arbeite nur am Task-Scope.** Wächst er über den Scope → flaggen (⚠️ UNKLAR im
   Ledger §6), nicht still erweitern (GOI §7).
4. **DoD ist bindend:** erst „fertig", wenn die Prüfung (unten je Task) grün ist.
5. **Vor Commit (hart, nicht umgehbar):**
   - `python -m pytest tooling/superversion/ tooling/tests/ -q` (bzw. Task-Suite)
   - `python scripts/check_index.py --strict` (Drift-Gate)
   - bei TMDL/PBIR-Berührung: PostToolUse-Hooks beachten (Tabs, `=` statt `:=`,
     `/// Purpose:` statt `description:`); blockt ein Hook → fixen, nie umgehen.
6. **Commit-Konvention:** `feat(superversion): <I-x.y> <was>` / `fix(...)` / `test(...)`.
   Body: kurzer Was/Warum + „Closes I-x.y".
7. **Ledger abhaken:** den Task-Status in §6 (Tabelle) im **selben Commit** auf ✅ +
   Datum + Beleg (Test-Kommando/Exit) setzen. Kein Status nur im Fließtext.
8. **Bewusst-nicht-gemacht** am Session-Ende explizit auflisten (GOI §3).

### 0.2 DoD-Format (jede Task trägt es)
`Input · Output · Fehlerfall · Rollback · Prüfung (mechanisch/agent)`. „Mechanisch" =
ein Kommando entscheidet grün/rot. „Agent" = QA/SA-Review nötig (s. 0.4).

### 0.3 Nicht-verhandelbare Invarianten (gelten in JEDER Task)
- **I1 Neutraler Core:** Measures tragen `expressions{}` je Dialekt; `expression`/DAX ist
  nur EIN Dialekt, nie Primat. Ein Test, der hartcodiertes DAX im Source-Adapter findet,
  muss rot werden (`test_neutral_core_no_dax_primacy`-Muster).
- **I2 Determinismus ab Freigabe:** kein LLM auf dem Compile-/Test-Pfad; gleicher Input →
  byte-stabiler Output. Jeder Generator/jedes Gate läuft ohne KI.
- **I3 Official-First je Stack:** offizielle Validatoren adoptieren (PBI:
  `powerbi-report-author`/`check_pbir`; OSI: vendored `osi-schema.json`), nie nachbauen.
- **I4 Standalone + integratable:** jedes Layer-Tool läuft gegen einen nackten Stack
  (ohne ALUCA-Core) UND integriert. Ein Standalone-Smoke-Test pro Tool.
- **I5 Quality-Floor (Premium):** kein Artefakt unter F1–F6 (PRODUCT_PLAN §2). Floor =
  Gate, das rot wird, keine Absicht.

### 0.4 QA/SA-Doppelreview (für premium-gatende Tasks)
Tasks mit Tag **[QA/SA]** brauchen vor Merge zwei unabhängige Sub-Agent-Reviews:
**QA** = Fakten/Code-Treue + Tests echt grün; **SA** = Architektur-Kohärenz + Invarianten
I1–I5. Befunde konsolidieren, bei ≥1 Critical/Major re-review bis 0 Critical.

### 0.45 Modellwahl je Task (GOI §3 operationalisiert)
Die GOI nennt das Prinzip („Haiku mechanisch · Sonnet Standard · Opus Architektur/harte
Trade-offs; im Zweifel kleiner"), aber eine laufende Session wechselt ihr Modell **nicht
selbst** — die Wahl trifft der Mensch **beim Session-Start**. Darum hier das verbindliche
Mapping:

| Modell | Wofür | Tasks |
|---|---|---|
| **Sonnet (Default-Builder)** | gut spezifizierte, test-getriebene Ausführung | I-1.x, I-2.2–2.4, I-3.2–3.5, I-4.x, I-5.x, I-7.2–7.3, I-6.2–6.6 |
| **Opus** | Architektur-/Doktrin-Entscheidungen, harte Trade-offs, Neuland-Discovery | alle **[QA/SA]**- und ADR-Tasks: I-2.1, I-3.1, I-8.1, I-9.1; sowie I-6.1 (Inventur+Soll-Schnitt) |
| **Haiku** | rein mechanisch, kein Urteil | I-1.1 (testpaths/Index), Snapshot-Regen in I-1.5, reine Formatier-/Lint-Fixes |

**QA/SA-Doppelreview (§0.4):** der Review-Sub-Agent läuft mit **Opus** (Urteil über
Architektur/Invarianten I1–I5) — unabhängig davon, mit welchem Modell gebaut wurde. Der
Premium-Floor-Review **vor jedem Merge nach `main`** ist Pflicht und Opus-getrieben.

**Warum das robust ist:** Jede Task hat eine harte mechanische DoD (pytest grün,
`check_pbir` 0 Errors, Drift-Gate grün). Ein zu kleines Modell scheitert damit **sichtbar
am Gate**, statt etwas Kaputtes durchzuschmuggeln — die Gates entkoppeln Korrektheit von
der Modellwahl. Die Staffelung optimiert also Kosten/Geschwindigkeit, nicht Sicherheit.

### 0.5 Abhängigkeits-Graph (grob)
```
I-1 (from_aluca härten) ──┬─▶ I-3 (PBI-Stack-Adapter/Delivery) ──▶ I-4 (Value-Cert)
                          ├─▶ I-5 (Layer-Tools standalone)
I-2 (Core-Heimat+CI)  ────┘
I-3+I-4 ──▶ I-6 (Studio-Cockpit) ──▶ I-7 (2. Stack/agnostisch)
I-6 ──▶ I-8 (Wirkungs-Loop, Z3) ──▶ I-9 (Team/Org, Z4)
```
Regel: I-N+1 startet erst, wenn I-Ns Messgröße grün ist. Parallelisierbares ist markiert ∥.

### 0.6 Z-Stufen-Mapping (Zielbild → Initiativen)
| Z | Zustand (PRODUCT_PLAN §6) | Initiative |
|---|---|---|
| Z0 | Neutraler Core, ALUCA angedockt, 1 Stack grün | I-1, I-2, I-3 |
| Z1 | Golden-Thread-Gate grün, ≥2 Stacks (sandbox) | I-3, I-7 |
| Z2 | Compliance-Regeln über alle Stacks, premium | I-4, I-5 |
| Z3 | Wirkungs-Loop Action→KPI | I-8 |
| Z4 | Team/Org-Schicht + Industry-Packs | I-9 |

---

## NOW — aktive Initiativen

### I-1 · `from_aluca` zum produktiven Source-Adapter härten
**Wette:** ALUCAs Bedeutungs-/Visual-Schicht speist den kanonischen Core verlustarm über
**alle universellen Use-Cases**, nicht nur COM-001.
**Messgröße:** ≥5 universelle Brackets → `CanonicalModel`, alle Adapter-Tests grün,
0 ungemappte Pflichtfelder (oder explizit als ⚠️ geledgert).
**Ausgangslage (✅ Phase-0-Spike, 2026-06-22):** `tooling/superversion/from_aluca.py` +
`canonical_contract.py` + 7 Tests grün an COM-001.
**Verfügbare Brackets (verifiziert 2026-06-22, alle unter `core/usecases/core/`):**
COM-001..004, FIN-001/002, OPS-001/002/003, SCM-001/002/003, XD-001..004 — **16 Stück,
je mit `UseCase_Bracket.yaml`.** Reichlich Material; kein Bracket muss neu angelegt werden.

| Task | DoD (Input · Output · Fehlerfall · Rollback · Prüfung) |
|---|---|
| **I-1.1** `superversion` in Test-/Index-Pfade aufnehmen | Input: `pyproject.toml` `testpaths`, `_INDEX`-Pflicht · Output: `tooling/superversion` in `testpaths`; `tooling/superversion/_INDEX.md` angelegt + im zuständigen Index verlinkt · Fehlerfall: `check_index.py` rot → Datei nachtragen · Rollback: Pfad entfernen · **Prüfung (mechanisch):** `pytest -q` sammelt superversion-Tests, `check_index.py --strict` Exit 0 |
| **I-1.2** Adapter gegen COM-002 + COM-003 härten | Input: `core/usecases/core/COM-002_Margin_Price_Performance/`, `COM-003_Customer_Value/UseCase_Bracket.yaml` · Output: beide bauen valides `CanonicalModel`; neue Tests je UC (Tabellen/Measures/Pages) · Fehlerfall: ungemapptes Feld → Test rot + ⚠️ im Ledger · Rollback: Test xfail markieren · **Prüfung (mechanisch):** `pytest tooling/superversion/ -q` grün |
| **I-1.3** Cost- + OTIF-Bracket abdecken (Cross-P&L-Breite) | Input: `FIN-002_Cost_Performance/` + `SCM-002_Supply_Reliability_OTIF/UseCase_Bracket.yaml` (beide **verifiziert vorhanden**) · Output: Adapter mappt beide; `_Measures`-Fallback + fact-Routing getestet · Fehlerfall/Rollback wie I-1.2 · **Prüfung (mechanisch):** pytest grün |
| **I-1.4** `component_300s` Evidence-Grid sauber mappen (Spike-TODO) | Input: COM-001 `component_300s` (evidence_grain/columns) · Output: Evidence-Detail wird zu measure-bindendem Visual statt leerer Karte; Test prüft binds_measures auf Page 2 · Fehlerfall: kein Measure ableitbar → dokumentierter Platzhalter · Rollback: v0-Karte behalten · **Prüfung (mechanisch):** pytest |
| **I-1.5** `from_aluca` CLI + golden snapshot je UC | Input: Adapter-API · Output: `python -m tooling.superversion.from_aluca <bracket> --out model.json`; ein eingecheckter Golden-Snapshot je UC; Regressions-Test diff't dagegen · Fehlerfall: Snapshot-Drift → bewusst regenerieren oder Bug fixen · Rollback: CLI additiv · **Prüfung (mechanisch):** pytest + byte-stabiler Re-Run |

**Sequenz:** I-1.1 → (I-1.2 ∥ I-1.3) → I-1.4 → I-1.5. **Bewusst nicht:** Relationships
aus Brackets ableiten (gehören in Stack/data_contracts, → I-3).

### I-2 · Core-Heimat & CI für die Superversion in ALUCA
**Wette:** Die Superversion lebt sauber in ALUCA, Meridian-Engine wird **eingezogen**
(nicht kopiert), und CI hält die Invarianten I1–I5 grün.
**Messgröße:** `make`/CI-Lauf grün auf frischem Klon inkl. superversion-Suite + ein ADR
fixiert die Heimat-/Einzieh-Entscheidung.

| Task | DoD |
|---|---|
| **I-2.1 [QA/SA]** ADR „Superversion-Heimat & Meridian-Einzug" | Input: `PRODUCT_PLAN §0`, ADR-Konvention `docs/architecture/adr/` · Output: ADR mit **nächster freier Nummer** (⚠️ 0004 ist seit origin #325 = Industry-variant-tier VERGEBEN → vermutlich `0005-superversion-home-and-meridian-vendoring.md`; vor Anlage `ls docs/architecture/adr/` prüfen, max+1 nehmen) (Accepted): ALUCA = Heimat; Meridian-Core als **vendored submodule/pinned dep**; `canonical_contract` ist Spiegel bis Einzug, dann Import der Originale · Fehlerfall: ADR-Nummern-Kollision → `ls adr/` + max+1 · Rollback: Status „proposed" · **Prüfung (agent QA/SA + mechanisch check_index)** |
| **I-2.2** Meridian-Engine-Einzug (Mechanik) | Input: ADR I-2.1 Entscheid · Output: Meridian `core/pbi_engine` als gepinnte Quelle erreichbar (submodule **oder** `vendor/`-Sync mit Pin-Datei); `canonical_contract` re-exportiert die Originale, wenn verfügbar (Soft-Fallback auf Spiegel) · Fehlerfall: Import bricht → Soft-Skip + ⚠️ · Rollback: Spiegel bleibt aktiv · **Prüfung (mechanisch):** `test_contract_parity_with_meridian` grün gegen die eingezogene Quelle |
| **I-2.3** CI-Job „superversion" | Input: `.github/workflows/`, vorhandene `stage1.yml` · Output: Job läuft superversion-pytest + `check_index --strict`; dokumentiert (CI-Quota-Hinweis aus CLAUDE.md beachten — lokal grün ist Pflicht) · Fehlerfall: Quota-Rot ignorieren (bekannt) · Rollback: Job entfernen · **Prüfung (mechanisch):** lokal `pytest` + Workflow-Lint |
| **I-2.4** Upstream-Pin-Drift-Sensor für Meridian-Pin + OSI-Schema | Input: Meridians `make check-upstream`-Muster (D-238) · Output: ALUCA-seitiger Pin-Check meldet, wenn der Meridian-Core-Pin oder `osi-schema.json` driftet (meldet, bumpt nie) · Fehlerfall: kein Netz → Soft-Skip · Rollback: Sensor entfernen · **Prüfung (mechanisch):** Sensor-Lauf gibt Pin-Status |

**Sequenz:** I-2.1 → I-2.2 → (I-2.3 ∥ I-2.4). Läuft ∥ zu I-1 (nur I-2.2 hängt nicht an I-1).

### I-3 · PBI-Stack-Adapter & Delivery schließen (die harte Lücke Q15) → Z0/Z1
**Wette:** Aus dem kanonischen Modell entsteht ein **offiziell-validierter, deterministisch
gerenderter** Power-BI-Report — über die offizielle MS-Skill, nicht den ALUCA-Prototyp.
**Messgröße:** Voll-Report für ≥1 universellen UC besteht `check_pbir` / official validator
mit **0 Errors**; deterministisch (byte-stabil).
**Anlass:** Q15 = einziges „does not exist" im Reifegrad (v3); ALUCA-PBIR ist Template-Copy.

| Task | DoD |
|---|---|
| **I-3.1 [QA/SA]** Stack-Adapter-Vertrag definieren | Input: Meridian Target-Registry `emit(canonical)->{path:content}`, ADR-0036 · Output: `tooling/superversion/targets/base.py` (Adapter-Protokoll) + Registry; ADR-Notiz · Fehlerfall: Vertragsbruch zu Meridian → angleichen · Rollback: proposed · **Prüfung (agent + pytest)** |
| **I-3.2** TMDL-Emit aus kanonischem Modell (Semantic Model) | Input: `CanonicalModel`, Meridians TMDL-Templates/`semantic_model.py`, TMDL-Hardrules (AGENTS.md) · Output: gültige `_Measures.tmdl`/Tabellen je Domäne; Dialekt `expressions{}`→DAX hier (Stack-Schritt, nicht Source) · Fehlerfall: Hook blockt (Tabs/`:=`/`description:`) → fixen · Rollback: hinter Flag · **Prüfung (mechanisch):** TMDL-Hooks grün + Parse-Test |
| **I-3.3** PBIR-Report-Emit via offizieller MS-Skill (I3) | Input: `CanonicalModel.report`, `microsoft/skills-for-fabric` / `powerbi-report-authoring`, `scripts/check_pbir.py` · Output: PBIR-Report, der **`check_pbir` 0 Errors** besteht; ALUCA-Prototyp-Renderer hinter Flag deprecated · Fehlerfall: Skill deckt Visual-Typ nicht → Delta als legitimer Eigen-Scope ledgern (P1) · Rollback: Prototyp-Flag · **Prüfung (mechanisch):** `check_pbir` Exit 0 |
| **I-3.4** Golden-Thread-Gate `validate_golden_thread()` | Input: ALUCA `registry_builder.py`-Logik, `CanonicalModel` · Output: Gate: jede Measure hat strategischen Anker, sonst FAIL; als Stage-Gate verdrahtet · Fehlerfall: Broken-Ref → FAIL (wie ALUCA-Drift heute) · Rollback: als WARN schaltbar · **Prüfung (mechanisch):** pytest + ein bewusst gebrochener UC wird rot |
| **I-3.5** E2E-Smoke: Bracket → TMDL+PBIR → validate (1 UC) | Input: COM-001 · Output: ein Kommando fährt Bracket→Modell→TMDL+PBIR→`check_pbir` grün; in CI · Fehlerfall: jede Stufe rot blockt · Rollback: — · **Prüfung (mechanisch):** E2E-Skript Exit 0 |

**Sequenz:** I-3.1 → I-3.2 → I-3.3 → (I-3.4 ∥ I-3.5). Hängt an I-1.1/I-2.2.

### I-4 · Value-Zertifizierung & Eval-Suite (Premium F6) → Z2
**Wette:** Falsche KPI-**Werte** werden maschinell gefangen, nicht nur falsche Struktur;
Qualität ist gegen ≥2 Referenz-Ontologien abgesichert (nicht nur Aurora/COM-001).
**Messgröße:** ein absichtlich falscher Wert wird von einem Gate rot; Evals laufen in CI.
**Anlass:** Q29 = „no value verification" (103/127 „manual review").

| Task | DoD |
|---|---|
| **I-4.1** Value-Check-Konzept + Referenzdatensatz | Input: data_contracts (Grain), ein kleiner Referenz-Fakt (synthetisch, eingecheckt) · Output: `tooling/superversion/eval/` mit Referenzdaten + erwarteten KPI-Werten je UC · Fehlerfall: kein Grain ableitbar → ⚠️ · Rollback: — · **Prüfung (mechanisch):** Daten laden testbar |
| **I-4.2** Value-Gate (KPI-Zahl vs. Referenz) | Input: I-4.1, generiertes Modell · Output: Gate rechnet KPI gegen Referenz, FAIL bei Abweichung > Toleranz · Fehlerfall: kein Rechenpfad ohne Live-Engine → als „advisory" markieren (P3) · Rollback: advisory-Schalter · **Prüfung (mechanisch):** falscher Wert → rot |
| **I-4.3** Zweite Referenz-Ontologie (gegen „nur ein Demo-Tenant") | Input: ein zweiter UC-Satz oder Branchen-Mini-Ontologie · Output: Eval läuft gegen ≥2 Ontologien; Regressions-Suite · Fehlerfall: Ontologie unvollständig → Teil-Eval + ⚠️ · Rollback: auf 1 reduzieren · **Prüfung (mechanisch):** pytest eval-suite |
| **I-4.4** COMP*-DSGVO-Regelkategorie (gespeist aus ALUCA-Compliance) | Input: `compliance/`-Stack als Single Source, `data_protection` je UC · Output: COMP-Regeln (PII ohne RLS → FAIL) im Gate · Fehlerfall: fehlende PII-Klassifik. → WARN „unklassifiziert" · Rollback: WARN statt FAIL · **Prüfung (mechanisch):** PII-UC ohne RLS rot |

**Sequenz:** I-4.1 → I-4.2 → (I-4.3 ∥ I-4.4). Hängt an I-3.

### I-5 · Layer-Tools standalone + integratable (incl. gov/eng/arch) → Z2
**Wette:** Jedes Layer-Tool (report-gen, visual library, page-templates, documenter, sowie
gov/eng/arch-Auditor) läuft gegen einen nackten Stack UND integriert; gov/eng/arch kommen
aus Meridian (ALUCA hat sie nicht).
**Messgröße:** je Tool ein Standalone-Smoke-Test grün + integrierter Lauf grün; gebrandeter
Doc-Output je Layer.

| Task | DoD |
|---|---|
| **I-5.1** Visual-Library + Page-Template-Engine als Tool | Input: `core/templates/page_templates/`, `visual_registry.yaml`, `layout_330300` · Output: standalone aufrufbares Tool (Registry→Visual-Spec) + Integration in I-3.3 · Fehlerfall: Visual-Typ fehlt → Katalog-Eintrag · Rollback: additiv · **Prüfung:** standalone-smoke + integriert |
| **I-5.2** Report-Documenter je Layer (DOCX/MD via Meridian-Branding) | Input: Meridians `docx_branding`/`xlsx_branding`, `CanonicalModel` · Output: gebrandete Handover-Doku (business+technical); Standalone-Modus · Fehlerfall: Branding-Layout bricht → Regressions-Snapshot · Rollback: MD-only · **Prüfung:** Doc-Gen-Snapshot |
| **I-5.3** gov/eng/arch-Engines einziehen (aus Meridian) | Input: Meridian `gov_engine`/`dataarch_engine`/`dataeng_engine` (dual-modal: ingest+greenfield) · Output: in ALUCA-Superversion aufrufbar, standalone gegen nackten Stack + integriert; je Engine ein Smoke-Test · Fehlerfall: dünne Engine (dataeng Stub) → als Beta ledgern, nicht als ready labeln (Ehrlichkeit v3) · Rollback: Engine deaktivieren · **Prüfung (mechanisch):** je Engine smoke grün |
| **I-5.4** Tool-spezifische Domänen-Packs (G7, je Plattform) | Input: I-5.3, Plattform-APIs (Unity Catalog/Purview/dbt-evaluator) · Output: ≥1 tool-spezifisches Regelpack pro Domäne (Official-First), je eigene DoD bei Start · Fehlerfall: API-Zugang fehlt → Pack als „geplant" · Rollback: generische Regeln bleiben · **Prüfung:** Pack-Test |

**Sequenz:** I-5.1 → I-5.2 → I-5.3 → I-5.4. ∥ zu I-4 möglich (nach I-3).

---

## NEXT — skopiert, kein Termin

### I-6 · Studio als Kunden-Cockpit (customer-operable) → MVP-Ship
**Wette:** Ein Kunde fährt den vollen Flow (Authoring→Freigabe→Generate→Validate→
Deliverable) ohne den Builder — Studio verbindet „vor dem Core" und „nach dem Core".
**Messgröße:** ein Kunde schließt einen universellen UC im Studio ab, ohne YAML-Handarbeit;
Premium-UX-Pass.

| Task | DoD (Kurzform — bei Aktivierung voll ausformulieren) |
|---|---|
| **I-6.1** Studio-Inventur: was kann der ALUCA-Cockpit heute (blueprint/generate/approvals/catalog) vs. Soll · **Prüfung (agent)** |
| **I-6.2** „Vor dem Core"-Panels: Quellen/gov/eng/arch-Realität verbinden (ingest) · **Prüfung:** UI-Flow-Test |
| **I-6.3** „Nach dem Core"-Panels: Target-Wahl + Deploy-Handoff + Gate-Report sichtbar · **Prüfung:** Flow-Test |
| **I-6.4** E2E-Flow Authoring→Freigabe-Schleuse→Generate→Validate→Deliverable im Studio · **Prüfung (agent+mechanisch):** Kunde-ohne-Builder-Durchlauf |
| **I-6.5** Setup/Onboarding + Standalone-Betrieb (lokal-first, BYO-Key) · **Prüfung:** Fresh-Install-Durchlauf |
| **I-6.6** Modell-Routing + Token-Budget je Schritt (P3) als Health-Metrik · **Prüfung:** Budget sichtbar/messbar |

**Sequenz:** I-6.1 → I-6.2 ∥ I-6.3 → I-6.4 → (I-6.5 ∥ I-6.6). Hängt an I-3/I-4.

### I-7 · Tool-Agnostik-Beweis (2.+ Stack) → Z1/Z2
**Wette:** Derselbe Core emittiert PBI **und** ≥1 weiteren Stack, beide validiert —
Agnostik bewiesen, nicht nur behauptet. **Teil-vorhanden:** OSI ist in Meridian schon
offiziell schema-validiert (Reconciliation §0 PRODUCT_PLAN).
**Messgröße:** derselbe freigegebene Core → PBI + (Cube|Databricks|OSI) je validiert.

| Task | DoD (Kurzform) |
|---|---|
| **I-7.1** OSI-Target via eingezogenen Meridian-Adapter an `from_aluca` anschließen · **Prüfung:** OSI-jsonschema-validate grün |
| **I-7.2** Zweiter Semantic-Layer-Stack (Cube **oder** Databricks Metric Views) end-to-end · **Prüfung:** offizieller Validator des Stacks 0 Errors |
| **I-7.3** Stack-Indifferenz-Test: ein Core → N Targets, KPI-Bedeutung identisch (Lackmustest §7 Synergy) · **Prüfung (mechanisch):** Cross-Target-Equivalence-Test |

**Sequenz:** I-7.1 → I-7.2 → I-7.3. Hängt an I-3.1 (Adapter-Vertrag).

---

## LATER — niedrige Konfidenz, braucht Discovery (echtes Neuland)

### I-8 · Wirkungs-Loop (Decision Intelligence) → Z3
**Wette:** Eine ausgelöste Action wird gegen die spätere KPI-Bewegung gemessen; die
Ontologie lernt, welche Entscheidung wirkte. **Heute bei keinem gebaut** (G2; Meridian-DI
= alert-only, AIS = advisory-Level-1). **Discovery zuerst.**
- I-8.1 Discovery/ADR: Loop-Modell (Action-Code → KPI-Snapshot-Delta → Attribution). [QA/SA]
- I-8.2 Action→KPI-Effekt-Tracking (deterministisch, ehrlich über fehlende Werte).
- I-8.3 Feedback in die Ontologie (Refinement-Trigger aus Wirkung).
**Messgröße:** für 1 Action ist der KPI-Effekt nachvollziehbar attribuiert.

### I-9 · Team-/Org-Schicht + Industry-Packs → Z4
**Wette:** Skalierung der Form, nicht der Arbeit — Mehrbenutzer/Rollen/geteilter Katalog
(Nagarro-Pfad) + Branchen-Packs über demselben Core. **Discovery zuerst** (RBAC, Multi-
Tenant widersprechen heutigem lokal-first-Design).
- I-9.1 Discovery/ADR: Org-Schicht über lokal-first (ohne den Core zu brechen). [QA/SA]
- I-9.2 Geteilter Katalog + Rollen/Approvals serverseitig (opt-in).
- I-9.3 Erstes Industry-Pack (Manufacturing — Meridian hat Skizze) als Content-Pack.
**Messgröße:** 2 Bearbeiter parallel an einem Katalog ohne Drift; 1 Branchen-Pack lädt.

---

## 6. Ledger — Single Source of Truth für Status (hier abhaken, nicht im Fließtext)

> Regel (CLAUDE.md/GOI): beantwortete Tasks + Entscheidungen **im selben Commit** hier
> abhaken (Status · Datum · Beleg). Offene Punkte nie nur in einer Notiz lassen.

| Task | Status | Datum | Beleg |
|---|---|---|---|
| Phase-0-Spike (from_aluca @ COM-001) | ✅ | 2026-06-22 | `pytest tooling/superversion/` 7/7 grün |
| I-1.1 testpaths+_INDEX | ✅ | 2026-06-22 | `pytest tooling/superversion/` 7/7 grün · `check_index.py --strict` 0 Befunde · Discovery sammelt 7 Tests via testpaths · Bugfix: `check_index` nutzt `rel.as_posix()` (Windows-Backslash-False-Positive behoben) · pyproject truncation (Cloud-Sync) repariert |
| I-1.2 COM-002/003 | ✅ | 2026-06-22 | `python -m pytest tooling/superversion/ -q` 25 passed, 1 skipped (Meridian-Parity) · `check_index.py --strict` Exit 0 · neue Tests je UC (Tabellen aus Lineage, Measures-Anzahl, 2 Report-Pages, measure-bindende Visuals); neutraler Core (I1) + Determinismus (I2) auf COM-001/002/003 parametrisiert · ⚠️ UNKLAR: column-lose Lineage (z. B. `crm.complaint.count` → `['fact_experience']`) routet ins `_Measures`-Fallback statt in die gleichnamige Fact-Tabelle — als Beobachtung getestet (`test_com003_measures_fallback_to_measures_table`), NICHT still umgemappt (würde `_split_lineage` für alle UCs ändern → eigener Task) |
| I-1.3 Cost+OTIF | ✅ | 2026-06-22 | `python -m pytest tooling/superversion/ -q` 42 passed, 1 skipped · `check_index.py --strict` Exit 0 · FIN-002 testet breites fact-Routing (≥4 Fact-Tabellen: fact_cost/fact_finance/fact_ops/…), SCM-002 testet `_Measures`-Fallback (Order Lines Count + Shipments Count); je UC Tabellen/Measures-Anzahl/2 Pages/measure-bindende Visuals/Rollen · neutraler Core (I1) + Determinismus (I2) auf alle 5 Brackets (COM-001/002/003, FIN-002, SCM-002) ausgeweitet · ⚠️ UNKLAR (geteilt mit I-1.2): column-lose Lineage `['fact_fulfillment']` (order.lines, shipments.count) routet ins `_Measures`-Fallback statt in die — hier sogar parallel existierende — `fact_fulfillment`-Tabelle; als Beobachtung getestet, NICHT still umgemappt |
| I-1.4 component_300s | ✅ | 2026-06-22 | `python -m pytest tooling/superversion/ -q` 51 passed, 1 skipped · `check_index.py --strict` Exit 0 · Adapter-Änderung: `_collect_visual_kpi_ids` liest jetzt `evidence_columns` und bindet katalog-auflösbare Spalten als Measures (Dimensions-Felder bleiben Dimensionen), dedupe; Page-2-Evidence-Grid bindet damit Measures statt leerer v0-Karte. Tests: COM-001 (named input) bindet Net Sales Amount/Gross Margin %, Dimensions-Ausschluss (region/channel/…), Dedupe, graceful Fallback (nur-Dimensions → binds=False, v0-Karte bleibt), parametrisiert über alle 5 UCs · neutraler Core + Determinismus weiter grün |
| I-1.5 CLI+Snapshots | ✅ | 2026-06-22 | `python -m pytest tooling/superversion/ -q` 63 passed, 1 skipped · `check_index.py --strict` Exit 0 · additive CLI `python -m tooling.superversion.from_aluca <bracket> [--out model.json] [--kpis dir]` + deterministische `model_to_json` (asdict, sort_keys=False, trailing newline); je UC eingecheckter Golden-Snapshot unter `tooling/superversion/tests/golden/<UC>.json` (5 Stück); Regressions-Test diff't byte-genau gegen Snapshot, CLI-Smoke (--out == golden, stdout == serializer), byte-stabiler Re-Run pro UC verifiziert (extern + Test) |
| I-2.1 ADR Heimat/Vendoring [QA/SA] | ✅ | 2026-06-22 | `docs/architecture/adr/0005-superversion-home-and-meridian-vendoring.md` (Accepted) angelegt — Nummer 0005 (0004 = Industry-tier #325 belegt, max+1) · Entscheid: ALUCA = Heimat; Meridian-Core vendored+pinned (vendor-sync default, submodule als Alternative verworfen), `canonical_contract` parity-gated Standalone-Mirror mit Import-Originals-when-present + Soft-Fallback, Neutral-Core (I1) über die Naht gewahrt, Pin drift-gesensed (I-2.4) · in `docs/architecture/_INDEX.md` §1/§2/§3 (A-8) + `adr/README.md` registriert · `check_index.py --strict` Exit 0 · QA/SA-Doppelreview durchgeführt (Sub-Agenten), Befunde eingearbeitet |
| I-2.2 Meridian-Einzug | ✅ | 2026-06-23 | Meridian-Contract-Subtree (`core/pbi_engine` model+parsers) vendored unter `tooling/superversion/vendor/meridian/` + `PIN.json` (sha256-Manifest, vendor-sync gem. ADR-0005) · `canonical_contract.py` ist jetzt Seam: re-exportiert vendored Originale via `_meridian_vendor.py` (importlib by-path, kein `core`-sys.modules-Konflikt — ALUCA nutzt `core.brand.*`!), Soft-Fallback auf verbatim `_canonical_mirror.py` · Mirror auf **volle Feldparität** gebracht; Golden-Snapshots regeneriert (byte-stabil) · Paritätstest gehärtet: alle 16 Dataclasses, beide Richtungen, Namen+Reihenfolge+Defaults, via Vendor-Pfad (kein Hardcode); +Mirror≡Originals-Serialisierungs-Äquivalenz +Manifest-Integrität +Re-Export-aktiv-Test · `pytest tooling/superversion/ -q` 67 passed (Parität läuft, skippt nicht mehr) · `check_index --strict` Exit 0 · vendored Code aus ruff ausgenommen · ⚠️ exakter Upstream-Commit unbekannt (aus Zip-Archiv, nicht git) → bei nächstem git-Sync pinnen |
| I-2.3 CI-Job | ✅ | 2026-06-22 | `.github/workflows/superversion.yml` (eigener Workflow) — Job `superversion` läuft `check_index.py --strict` + `pytest tooling/superversion/ -q`; path-gefiltert auf superversion/usecases/kpi_catalog/check_index; CI-Quota-Hinweis aus CLAUDE.md im Header dokumentiert · lokal grün: pytest 63 passed/1 skipped, `check_index --strict` Exit 0 · Workflow-Lint: YAML+Struktur validiert (actionlint env-seitig n/a) · vorgezogen vor I-2.2/I-2.4 (hängen an Meridian-Quelle, in Session n/v) · Rollback: Datei entfernen |
| I-2.4 Pin-Drift-Sensor | ✅ | 2026-06-23 | `scripts/check_superversion_pins.py` — ALUCA-seitiger Sensor (Modell: Meridians `check_upstream_freshness.py`/D-238): meldet Drift, **bumpt nie**; advisory (Exit 0) default, `--strict` macht harte Drift (fehlende/divergierte vendored Datei) zu Exit 1; offline/Netz-Slice → Soft-Skip. Prüft: vendored-Core-Integrität (sha256 vs `PIN.json`), Pin-Provenance (synced_at-Staleness + commit_pinned), Contract-Parität (Re-Export vs Mirror), OSI-Schema (in ALUCA n/v → Meridian-owned, flagged für I-3/I-7). Reine Cores netz-frei unit-getestet (`tests/test_pin_sensor.py`) + E2E-Smoke gegen echtes Pin; als advisory Schritt in `superversion.yml` verdrahtet · `pytest tooling/superversion/ -q` 75 passed · `check_index --strict` Exit 0 · ruff clean · Sensor-Lauf: ADVISORY (commit UNKNOWN aus Zip), Exit 0 |
| I-3.1 Adapter-Vertrag [QA/SA] | ✅ | 2026-06-23 | `tooling/superversion/targets/base.py` — Target-(Stack-)Adapter-Vertrag: `emit(canonical)→{Pfad:Inhalt}` (rein/deterministisch), `TargetAdapter`-Metadaten feldgleich zu Meridian (ADR-0036), `REGISTRY`+`register/get/available/render`-Dispatch mit Shape-Validierung; `CanonicalModel` nur über die `canonical_contract`-Naht (ADR-0005 rule 4); Vertrag-only (Registry leer, Adapter folgen I-3.2/3.3, official-first) · ADR-0006 (Accepted) angelegt + in `docs/architecture/_INDEX.md` §1/§2/§3 (A-9) + `adr/README.md` registriert · Tests `tests/test_targets.py` (Dispatch, Vertragsbruch, Determinismus, Protocol, Registry-leer-bei-Import via Subprozess, Kollisions-register, Pfad-Containment) · `pytest tooling/superversion/ -q` 87 passed · `check_index --strict` Exit 0 · ruff clean · QA/SA-Doppelreview (Opus-Sub-Agenten): 0 Critical; QA-M1 (Meridian 8→9 targets +duckdb) + SA-M1 (Target-Parität als akzeptierte ungeschützte Grenze dokumentiert) + Minors (echtes `__init__`-Re-Export, Pfad-Containment, Kollisions-register) eingearbeitet |
| I-3.2 TMDL-Emit | ✅ | 2026-06-23 | `tooling/superversion/targets/tmdl.py` — erster konkreter Adapter auf dem I-3.1-Vertrag: `emit(canonical)→{<Model>.SemanticModel/definition/tables/<table>.tmdl}`; Dialekt/DAX hier materialisiert (I1: Source bleibt neutral) — reale `expressions['dax']`/`expression` verbatim, sonst deterministischer HITL-`BLANK()`-Platzhalter + `/// HITL`-Marker (ALUCA = Bedeutung, nicht DAX); TMDL-Hardrules: Tabs, `=` statt `:=`, `/// Purpose:` statt `description:`, `summarizeBy`/`formatString`. Registriert bei Import von `targets.tmdl` (Registry bleibt leer bei reinem base-Import → I-3.1-Invariante gewahrt) · Tests `tests/test_tmdl_target.py`: **echter `validate_tmdl_style.sh`-Hook grün** auf emittierten Files, Parse-Round-Trip durch vendored `tmdl_parser._parse_table`, Determinismus, Hardrule-Checks · `pytest tooling/superversion/ -q` 95 passed · `check_index --strict` Exit 0 · ruff clean |
| I-3.3 PBIR via MS-Skill | ✅ | 2026-06-23 | `tooling/superversion/targets/pbir.py` — zweiter konkreter Adapter auf dem I-3.1-Vertrag, **official-first**: `emit(canonical)→{<Report>.Report/definition/…}` (`definition.pbir` v4.0, `version.json` 2.0.0, `pages.json`+`pageOrder`, `page.json` je Page, `visual.json` je Visual). File-Layout/`$schema`-URLs/ID-Regeln/Visual-Rollen-Kontrakt nach `microsoft/skills-for-fabric` @`792cd09` (`powerbi-report-authoring`); **Gate = offizielle CLI `powerbi-report-author validate` (0 Errors)**, nie nachgebaut (§0.5). Visual-Typ→PBIR-Typ + Rollen/`maxPerRole` als deterministische Konstanten aus `catalog describe` (emit bleibt rein, I2). ALUCA trägt Bedeutung, nicht Layout → fehlende **Pflichtrollen** (z. B. Chart-`Category`) bzw. `maxPerRole`-Überlauf (waterfall `Y` max 1) erhalten deterministischen **HITL-Platzhalter** (PBIR-Analogon zu I-3.2s `BLANK()`) + `hitl_gaps()`-Ledger (P1-Delta), nie erfundene Daten; Measure-only-Rollen bekommen Measure-Kind-Platzhalter (kein `PBIR_ROLE_KIND_MISMATCH`). Prototyp-Renderer (`generate_full_report.py`) hinter `--allow-deprecated-prototype`/`ALUCA_ALLOW_PROTOTYPE_RENDERER=1` deprecated (Rollback-Flag); Orchestrator `generate_phase5_reports.ps1` opt-in. Tests `tests/test_pbir_target.py`: **offizieller `validate` 0 Errors** (CLI-gated, sonst skip) auf COM-001 + **alle 16 UCs extern verifiziert (0 err/0 warn)**, Parse-Round-Trip durch vendored `pbir_parser` (Pages+Visual-IDs), Determinismus, queryState/Pflichtrollen, Kind-Match-Platzhalter, `maxPerRole`-Drop, Unknown-Fallback · `pytest tooling/superversion/ -q` 106 passed · `check_index --strict` Exit 0 · ruff clean |
| I-3.4 Golden-Thread-Gate | ✅ | 2026-06-23 | `tooling/superversion/golden_thread.py` — `validate_golden_thread(model)` + `assert_golden_thread` + CLI-Stage-Gate (`python -m tooling.superversion.golden_thread`), in `superversion.yml` verdrahtet. Zwei Befundklassen: `unresolved_measure` (kein strategischer Anker) = **error**, `dangling_visual_bind` (Visual bindet nicht-existente Measure) = **warn** per Default; `--strict` eskaliert, `--warn` = Rollback. Tests `tests/test_golden_thread.py`: bewusst gebrochener UC (bogus KPI) wird rot, WARN-Schaltbarkeit, reale UCs 0 unresolved · `pytest tooling/superversion/ -q` 113 passed · `check_index --strict` Exit 0 · ruff clean · ⚠️ ECHTER BEFUND (geledgert für I-3-Follow-up): COM-001 (3) + COM-002 (1) Visuals binden Vergleichs-Measures (Plan/LY/Plan GM), die der Adapter nicht materialisiert → als WARN gemeldet (nicht still gefixt; Bracket/Adapter-Fix ist eigener Scope) |
| I-3.5 E2E-Smoke | ✅ | 2026-06-23 | `tooling/superversion/e2e_smoke.py` — ein Kommando fährt die ganze Kette für 1 UC (`python -m tooling.superversion.e2e_smoke [<bracket>] [--require-cli]`): **source** (`from_aluca`→`CanonicalModel`) → **golden_thread** (I-3.4-Gate, error blockt) → **tmdl** (I-3.2-Emit + TMDL-Hardrule-Hook, sonst struktureller Fallback) → **pbir** (I-3.3-Emit + offizielles `powerbi-report-author validate`, check_pbir 0 Errors). Jede Stufe `PASS/FAIL/SKIP`; **jede rote Stufe → Exit 1**. PBIR-Gate ist official-first (I3): CLI fehlt → SKIP (lokal nicht-blockend), `--require-cli` (CI) macht daraus FAIL. In `superversion.yml` verdrahtet inkl. Node-Setup + `npm i -g @microsoft/powerbi-report-authoring-cli`, dann `e2e_smoke --require-cli`. Tests `tests/test_e2e_smoke.py`: COM-001 alle Stufen grün, `main([])`==0, CLI-absent→SKIP (nicht-blockend) vs `--require-cli`→FAIL, fehlendes Bracket→Exit 1, `--keep` materialisiert TMDL+PBIR-Artefakte · `pytest tooling/superversion/ -q` 130 passed · `check_index --strict` Exit 0 · ruff clean · E2E lokal mit echter CLI: alle Stufen PASS, Exit 0 |
| I-4.1 Value-Check-Konzept + Referenzdatensatz | ✅ | 2026-06-23 | `tooling/superversion/eval/` — Value-Zertifizierungs-Substrat: synthetischer, eingecheckter Referenz-Fakt `eval/data/commercial_invoice_lines.yaml` (Grain invoice_line, 8 Zeilen) + erwartete KPI-Werte je UC `eval/data/expected/COM-001.yaml` (Net Sales/GM Amount/GM %/vs-Plan) + Loader `refdata.py` (`load_dataset`/`load_expectations`, Dataclasses) + transparente Referenz-Aggregation `refcalc.py` (lesbare Formel-DSL `sum(col)` / `sum(a)/sum(b)`, kein Engine — Invariant I2, Oracle für I-4.2). Golden-Werte sind **reproduzierbar**, nicht hand-codiert: Self-Consistency-Test rechnet jede `value` aus ihrer `formula` über den Datensatz nach. Tests `tests/test_eval_refdata.py`: Laden+Grain+Spalten, governte KPIs tragen `kpi_id`, Self-Consistency, bekannte Aggregate (Net Sales=10000, GM%=0.409), DSL-Ablehnung (unbekannte Funktion/Spalte, Division durch 0), fehlende Datei → Fehler · `pytest tooling/superversion/ -q` 138 passed · `check_index --strict` Exit 0 · ruff clean |
| I-4.2 Value-Gate (KPI-Zahl vs. Referenz) | ✅ | 2026-06-24 | `tooling/superversion/eval/value_gate.py` — vergleicht **berechnete** KPI-Werte gegen die I-4.1-Referenz, **FAIL bei |Δ| > Toleranz** (fängt falsche Werte, nicht nur Struktur). `check_values`/`assert_values` (rein) + CLI-Stage-Gate `python -m tooling.superversion.eval.value_gate <UC> [--values f] [--advisory]`. Werteherkunft: kein Live-Engine auf dem det. Pfad (I2) → Werte aus Engine-Lauf/Values-Datei/`refcalc`-Oracle; **ohne Werte advisory (P3)**, blockt nie. `--advisory` = Rollback (Verstöße → nicht blockend). In `superversion.yml` als advisory-Stage verdrahtet (CI ohne Engine → Exit 0; das blockende „falscher Wert → rot" deckt die Test-Suite). Tests `tests/test_value_gate.py`: korrekte Werte (refcalc-Oracle) grün, **absichtlich falscher Wert → ValueGateError/Exit 1**, advisory-Downgrade, uncomputed≠Verstoß, Toleranz-Grenze (genau auf Toleranz grün, knapp darüber rot), CLI rot/grün/advisory · `pytest tooling/superversion/ -q` 146 passed · `check_index --strict` Exit 0 · ruff clean |
| I-4.3–4.4 2.-Ontologie/COMP | ⬜ offen | | |
| I-5.1–5.4 Layer-Tools+gov/eng/arch | ⬜ offen | | |
| I-6.x Studio-Cockpit | ⬜ offen (NEXT) | | |
| I-7.x 2. Stack | ⬜ offen (NEXT) | | |
| I-8.x Wirkungs-Loop | ⬜ offen (LATER, Discovery) | | |
| I-9.x Team/Org+Industry | ⬜ offen (LATER, Discovery) | | |

---

## 7. Risiken & bewusst-nicht (GOI §3)

**Top-Risiken (mit Mitigation):**
1. **Meridian-Einzug-Mechanik** (submodule vs. vendor-sync) — Lizenz/Pin/Drift. *Mitig.:*
   ADR I-2.1 entscheidet vor Code; `canonical_contract`-Spiegel hält ALUCA lauffähig bis Einzug.
2. **MS-Skill deckt nicht alle Visual-Typen** (I-3.3) — Delta = Eigen-Scope. *Mitig.:* P1
   erlaubt Eigenbau nur im offiziell nicht abgedeckten Scope; ledgern, nicht still nachbauen.
3. **gov/eng/arch dünn** (v3: dataeng Stub-nah) — nicht als „ready" labeln. *Mitig.:*
   I-5.3 zwingt Beta-Label bis QA-Freigabe (Meridian-Muster I-10.6).
4. **CI-Quota rot bis Juli 2026** (CLAUDE.md) — nicht verwirren lassen. *Mitig.:* lokal-grün
   ist die Pflichtprüfung; rote Quota-Läufe nicht re-investigieren.
5. **Solo-Kapazität vs. Scope bis Z4** — *Mitig.:* NOW (I-1..I-5) ist der MVP-Pfad; NEXT/LATER
   erst nach grünem Z2 anfassen; one-in-one-out.

**Bewusst NICHT in diesem Plan (Stand 2026-06-22):**
- **Kein Deprecaten von ALUCAs Eigen-Engine** (P5; Adapter ist additiv).
- **Kein Live-Tenant-Deploy (G1)** — eigener Track, hängt an Tenant-Zugang; Handoff-Artefakt
  shippt zuerst.
- **Kein Monolith-Merge** (Option B verworfen, PRODUCT_PLAN §9).
- **Industry-Packs/Multi-Tenant** erst Z4 (I-9), nach MVP.

## 8. Reihenfolge-Logik (eine Zeile)
Härte den Andock-Adapter (I-1) + gib ihm eine Heimat (I-2) → mach ihn lieferfähig
(I-3, schließt Q15) → mach ihn zertifizierbar (I-4) → verbreitere die Layer-Tools (I-5) →
mach ihn kundenbedienbar (I-6) → beweise Agnostik (I-7) → dann das Neuland Wirkung (I-8)
und Skalierung (I-9). Revenue-fähig (service-assisted) ab Ende I-3/I-4; customer-operable
ab I-6.
