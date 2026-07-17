# AuthN/AuthZ-Stack — Build-Backlog & Loop-Plan (Draft)

> **Status:** Draft-Plan (kein Code). Companion zu
> [`../adr/0016-authn-authz-stack-for-the-studios.md`](../adr/0016-authn-authz-stack-for-the-studios.md)
> (die Entscheidung/das Warum) und zu ADR-0014 (das handgebaute RBAC, das hier
> formalisiert/abgelöst wird).
>
> **Zweck:** die noch fehlenden Themen sammeln, um von der ADR-0016-**Entscheidung**
> zur **Umsetzung** zu kommen — jede Task-Card mit Zielbild (Z) und gate-verifizierbarer
> Definition of Done (DoD), dependency-geordnet, damit ein späterer Loop die nächste
> nicht-blockierte Task ziehen kann. **Noch nichts davon ist gebaut** — das ist die
> Feinausarbeitungs-Grundlage.
>
> **Cross-Repo:** Meridian führt ein eigenes, nicht byte-identisches Pendant
> (`meridian/studio/builds/BACKLOG_SAAS_AUTH.md`), weil ALUCA bereits next-auth + RBAC
> hat (Migration) und Meridian von Null baut (Backend + Auth). Der **gewählte Stack ist
> geteilt** (T0); die Wege dorthin unterscheiden sich.

---

## 1. Capability-Rolle → Modell-Routing

Tasks sind mit einer **Capability-Rolle** getaggt (kein Modell-ID — ADR-0008). Die Rolle
löst über die geschichtete L0/L1/L2-Config (`tooling/generator/schemas/ai_config.schema.json`,
`studio/src/lib/ai/…`) zu einem Modell auf.

| Rolle | Wofür | L0-Default (in Config übersteuerbar) |
|---|---|---|
| `architect` | Schema-/Contract-Design, ADR-/Compliance-Edits, Topologie-Entscheid | Opus 4.8 |
| `codegen` | Adapter, Migrationsskripte, Engine-Anbindung, Tests | Sonnet 5 |
| `mechanical` | Register/Index-Wiring, Doku-Stempel, Boilerplate | Haiku 4.5 |
| `verify` | adversariale DoD-Prüfung, Security-/AuthZ-Review | Opus 4.8 |

---

## 2. Loop-Protokoll

Deterministisch, one-in-one-out: (1) niedrigste Task ziehen, deren `depends-on` alle `done`
sind; (2) Subtask unter ihrer Rolle bauen; (3) DoD-Gate prüfen — **nie done bei rotem Gate**;
(4) grün → im Ledger `_INDEX.md` §3 (A-14-Folge) abhaken; (5) **WIP = 1**. Honesty-Gates:
kein Raten bei Kundenkontext-Bedarf (bewusst-offen markieren), keine Managed-Cloud-Abhängigkeit
einschleusen (ADR-0016 Festlegung 1), self-hostbar bleiben.

---

## 3. Task-Backlog (dependency-geordnet)

Legende: **Z** = Zielbild · **DoD** = der Check, der grün sein muss · **role** je Subtask.

### T0 — Stack-Entscheid ratifizieren (A vs. B) · depends-on: — · ✅ **ERLEDIGT (2026-07-15)**
- **Z:** ADR-0016 ist von *Proposed* auf *Accepted* mit **einer** gewählten Option gehoben, damit Bauarbeit autorisiert ist.
- T0.1 ✅ **Option A (next-auth+OpenFGA) gewählt** (Maintainer Flo, 2026-07-15); Option B (Ory) als reife-gebundene Re-Evaluation aufgeschoben (gekoppelt an T6/O-3). **DoD erfüllt:** ADR-0016-Status = Accepted, gewählte Option benannt, `adr/README.md` aktualisiert, `check_index.py --strict` grün · role: `architect`
- T0.2 Zitadel-Vorbehalt final einordnen (AGPL vs. Meridian-Auslieferung) · **DoD:** Notiz in ADR-0016, ob Zitadel endgültig raus oder Sonderfall · role: `architect` *(offen — für die A-Umsetzung nicht blockierend)*

> **Konsequenz der A-Wahl für den Rest des Backlogs:** T3 baut **OpenFGA** (nicht Ory Keto); T5 fährt den **Auth.js-Pfad** (T5.1, nicht T5.1'). Das ReBAC-Schema (T2) bleibt trotzdem **engine-neutral** modelliert, damit ein späterer A→B-Wechsel offen bleibt (O-1).

### T1 — Compliance-Gate: DSGVO/EU-Hosting des gewählten Stacks · depends-on: T0 · ✅ **ERLEDIGT (2026-07-15)**
- **Z:** Der gewählte Stack ist compliance-geprüft, bevor eine Zeile Code entsteht — das ist laut ADR-0016 der eigentliche Entscheider.
- T1.1 ✅ Self-Hosting-Topologie + Data-Residency dokumentiert · **DoD erfüllt:** [`../../../compliance/auth_stack_data_residency.md`](../../../compliance/auth_stack_data_residency.md) §3 (verlinkt aus `compliance/_INDEX.md`); „100% self-hosted, EU-Infra", einziger Vorbehalt = externer Social-IdP (im Default vermeiden) · role: `architect`
- T1.2 ✅ AVV/DPA-Bedarf geklärt · **DoD erfüllt:** §4 — Auth-Software self-hosted ⇒ kein Vendor-AVV; **einziger AVV-pflichtiger Beteiligter = EU-Hosting-Provider** (ohnehin nötig, nicht auth-spezifisch); Art.-30-Entwurf in §5 · role: `architect`

> **T1-Auflagen für die Bauphase** (aus dem Gate): (1) kein externer Social-IdP im Default (T5); (2) AVV mit EU-Host liegt vor; (3) OpenFGA hält nur pseudonyme IDs — Data-Minimization im ReBAC-Schema (T2) wahren.

### T2 — ReBAC-Schema-Modellierung · depends-on: T1 · ✅ **ERLEDIGT (2026-07-15)**
- **Z:** Das handgebaute `checkAccess` (ADR-0014) ist als deklaratives Relations-Schema abgebildet — Typen, Relationen, Auflösungsreihenfolge. → [`authn-authz-rebac-schema.md`](authn-authz-rebac-schema.md)
- T2.1 ✅ Ist-Modell extrahiert (Rollen-Hierarchien, zweistufige Auflösung, `projectRoleFromOrgRole` ohne Editor-Pfad) · **DoD erfüllt:** §1 mit Code-Belegen · role: `mechanical`
- T2.2 ✅ Relations-Schema entworfen (Typen user/organization/project; `can_view/edit/admin`); **Kern-Finding: die „explizite Zeile überschreibt Org, kein Merge"-Semantik ist nicht-additiv → braucht `but not`-Exklusion.** OpenFGA-DSL + Keto-Parität · **DoD erfüllt:** §2/§3/§4 + Matrix · role: `architect`
- T2.3 ✅ Break-Glass/Lockout durchgespielt · **DoD erfüllt:** §5 Matrix (8 Fälle) + §6 Break-Glass = Tupel-Write, kein Merge-Leck · role: `verify`

> **Konsequenz für T3/T4:** `checkAccess(P,U,minRole)` wird durch **drei computed relations** (`can_view/edit/admin`) ersetzt (kein Laufzeit-Ranking); Break-Glass-API-Härtung bleibt im API-Layer; Solo-Projekt (`org_id NULL`) = kein `parent`-Tupel → byte-identisch.

### T3 — AuthZ in-process (ADR-0016-Präzisierung) · depends-on: T2 · ✅ **ERLEDIGT (2026-07-15, lokal grün)**
- **Z:** `checkAccess` löst über das deklarative ReBAC-Modell auf — self-hosted, **ohne Engine**, hinter `AUTHZ_BACKEND` (Default `local` unverändert).
- **Pivot (2026-07-15, Flo):** OpenFGA-*Dienst* bringt bei Studio-Scale keinen Nutzen und ist beim Kunden (Nagarro) via Docker gesperrt → **in-process Evaluator** statt Engine. OpenFGA bleibt optionaler Scale-Swap (s. u.). ADR-0016 „Umsetzungs-Präzisierung".
- T3a.1 ✅ **geschrieben:** `studio/src/lib/authz/rebac-eval.ts` (pure Modell-Auswertung, `but not`-Override) + `rebac-backend.ts` (Fakten aus SQLite, reuse `getOrgMember`) + Dispatch in `rbac-repo.ts::checkAccess` (`AUTHZ_BACKEND=rebac`; Default `local` unverändert). Logik **verifiziert** (Node-Spiegel 9/9). · role: `codegen`
- T3a.2 ✅ **Test geschrieben:** `tests/lib/rebac-eval.test.ts` (9 Fälle, facts-level Pendant zu `authz-fga-cases.json`). · role: `verify`
- ✅ **Lokal verifiziert (Flo, 2026-07-15, node-only, KEIN Docker):** `npm run build` grün (TypeScript 17.1s, 68 Seiten) — der zuvor gemeldete Fehler war ein stale `.next`-Cache, kein Code. `npm test` **410/410** grün, unter `AUTHZ_BACKEND=rebac` ebenfalls 410/410 inkl. `rbac-repo.test.ts` → **Parität `local` ↔ `rebac` bewiesen.**

> **Optionaler Scale-Swap (OpenFGA — nur falls je nötig, kein Muss):** die Artefakte [`../../../studio/docker-compose.yml`](../../../studio/docker-compose.yml) + [`../../../studio/src/lib/authz/model.fga`](../../../studio/src/lib/authz/model.fga) liegen bereit; ein künftiges `fga`-Backend implementiert dieselbe `checkAccess`-Signatur via Engine-`check()`, reuse [`authz-fga-cases.json`](authz-fga-cases.json). Erfordert Docker/Binary → nur in einer Umgebung, wo das compliance-seitig ok ist.

### T4 — Migration der bestehenden RBAC-Daten · depends-on: T3
- **Z:** `project_members`/`org_members` sind als Relation-Tuples in der Engine, ohne Datenverlust, mit Dual-Write-Übergang.
- T4.1 Backfill-Skript `SQLite-Zeilen → Relation-Tuples` · **DoD:** Roundtrip-Test (jede Zeile → Tuple → gleiche `check()`-Antwort) · role: `codegen`
- T4.2 Dual-Write-/Umschalt-Strategie + Rollback · **DoD:** dokumentierter Cutover, Solo-Modus (org_id NULL) byte-identisch · role: `architect`

### T5 — AuthN · depends-on: T0 · **Weg C ✅ (2026-07-15), Magic-Link (A) aufgeschoben**
- **Z:** Login ist compliance-konform by default; die produktive Methode ist entschieden/dokumentiert.
- **Login-Methoden-Entscheid (Flo): Weg C** — jetzt compliant machen, echte Methode = **A (Magic-Link)** später. (B Ory-AuthN entfällt, da Stack-Option A gewählt.)
- T5-C ✅ **umgesetzt (Doku/Policy, kein Verhaltens-Change):** `auth/config.ts` ist **verifiziert social-IdP-frei by default** (GitHub opt-in nur bei Creds; Demo-Login dev-only) — Policy als Code-Kommentar + `.env.example` + Compliance-Doc §7 festgehalten, inkl. der **ehrlichen Prod-Lücke** (heute nur GitHub oder kein Prod-Login). · role: `codegen`
- T5-A ⏳ **aufgeschoben (Prod-Default):** passwortloser Magic-Link — **blockiert auf EU-E-Mail-Provider** (SMTP/Resend, DSGVO). Dann next-auth Email-Provider verdrahten. · **DoD:** Magic-Link-Login/Session grün, kein Social-IdP · role: `codegen`
- T5-Beta: Auth.js-Beta-Pin (`^5.0.0-beta.30`) → stable v5 bumpen, sobald verfügbar (ADR-0016 O-4); bis dahin Risiko dokumentiert. · role: `codegen`

### T6 — Enterprise-SSO/SAML · depends-on: T5 · **optional/deferred (ADR-0016 O-3)**
- **Z:** B2B-Mandanten können per SAML/OIDC anmelden — nur bauen, wenn realer Kundenbedarf.
- T6.1 eine Test-Tenant-SSO-Verbindung (Option B: out-of-the-box; Option A: pro Connection) · **DoD:** dokumentierter SSO-Login-Flow ODER „aufgeschoben bis Kundenbedarf" · role: `architect`

### T7 — Deployment-Topologie (Kopplung an ADR-0014 O-5) · depends-on: T4 · **deferred bis gehosteter Bedarf**
- **Z:** Entscheidung lokal-SQLite vs. gehosteter Shared-Server; falls gehostet, Isolationsprimitive (`tenant_id`/RLS).
- T7.1 Topologie-Entscheidung dokumentieren (verweist auf ADR-0014 O-5) · **DoD:** Topologie in ADR-0016/0014 festgehalten; falls gehostet, `tenant_id`/RLS-Plan · role: `architect` *(Kundenkontext nötig → bewusst-offen bis dahin)*

### T8 — Tests, Doku-Konsistenz, Ledger · depends-on: T3–T5
- **Z:** Auth ist test-abgesichert und die Register sind konsistent.
- T8.1 AuthZ-Test-Suite (positive/negative/Break-Glass) · **DoD:** `pytest`/`vitest` grün · role: `codegen`
- T8.2 ADR-0016-Status + Ledger A-14 nachziehen; `_INDEX.md` bei neuen Dateien registrieren · **DoD:** `check_index.py --strict` grün · role: `mechanical`

---

## 4. Abhängigkeitsgraph (Kurzform)

```
T0 (Stack-Wahl, Maintainer)
 └─ T1 (Compliance-Gate)
     ├─ T2 (ReBAC-Schema) ─ T3 (Engine+Anbindung) ─ T4 (Migration) ─ T7 (Topologie, deferred)
     └─ T8 (Tests/Doku)
T0 ─ T5 (AuthN) ─ T6 (SSO, optional)
```

## 5. Offene Punkte (spiegeln ADR-0016)

- **O-1 Stack A vs. B** → T0 (Maintainer).
- **O-2 Meridian-SaaS-Pfad** → im Meridian-Backlog (`BACKLOG_SAAS_AUTH.md`, M0 Charter §9).
- **O-3 SSO/SAML-Zeitpunkt** → T6 (nur bei Kundenbedarf).
- **O-4 Auth.js-Beta-Ausstieg** → T5.1 (nur Option A).
- **O-5 (aus ADR-0014) Isolationsprimitive** → T7 (nur gehostet).
