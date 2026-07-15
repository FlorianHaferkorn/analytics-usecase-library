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

### T2 — ReBAC-Schema-Modellierung · depends-on: T1
- **Z:** Das handgebaute `checkAccess` (ADR-0014) ist als deklaratives Relations-Schema abgebildet — Typen, Relationen, Auflösungsreihenfolge.
- T2.1 Ist-Modell extrahieren: `project_members(project,user,role)` + `org_members(user,org,role)` + Auflösung „Projekt-Zeile > Org-Rolle > kein Zugriff, kein Merge" (ADR-0014 Festlegung 4) · **DoD:** Ist-Modell-Doku als Referenz · role: `mechanical`
- T2.2 Relations-Schema entwerfen (Typen `user`/`org`/`project`; Relationen `member`/`admin`/`editor`/`viewer`; computed `can_view`/`can_edit`/`can_admin`); die ADR-0014-Auflösungsreihenfolge muss 1:1 abbildbar sein (inkl. „explizite Projekt-Zeile deckelt Org-Owner") · **DoD:** Schema-Datei + Check-Beispiele, die die ADR-0014-Fälle reproduzieren · role: `architect`
- T2.3 verify: die Break-Glass-/Lockout-Fälle (ADR-0014 O-4) im Schema durchspielen · **DoD:** dokumentierte Testfälle, kein Merge-Leck · role: `verify`

### T3 — AuthZ-Engine self-host + Studio-Anbindung · depends-on: T2
- **Z:** Der gewählte ReBAC-Dienst läuft lokal/self-hosted, `checkAccess` delegiert an ihn hinter einem Feature-Flag (ehrliche Degradation offline).
- T3.1 Deployment (Docker/Compose) des Dienstes (OpenFGA **oder** Ory Keto je T0) · **DoD:** Dienst startet lokal, Health-Check grün · role: `codegen`
- T3.2 `rbac-repo.ts::checkAccess` → Adapter auf `check()` der Engine, Feature-Flag `AUTHZ_BACKEND=local|fga` · **DoD:** bestehende require-role-/enforce-project-access-Tests grün mit beiden Backends · role: `codegen`
- T3.3 verify: Parität lokal vs. FGA über die ADR-0014-Fallmatrix · **DoD:** identische Zugriffsentscheidungen · role: `verify`

### T4 — Migration der bestehenden RBAC-Daten · depends-on: T3
- **Z:** `project_members`/`org_members` sind als Relation-Tuples in der Engine, ohne Datenverlust, mit Dual-Write-Übergang.
- T4.1 Backfill-Skript `SQLite-Zeilen → Relation-Tuples` · **DoD:** Roundtrip-Test (jede Zeile → Tuple → gleiche `check()`-Antwort) · role: `codegen`
- T4.2 Dual-Write-/Umschalt-Strategie + Rollback · **DoD:** dokumentierter Cutover, Solo-Modus (org_id NULL) byte-identisch · role: `architect`

### T5 — AuthN-Entscheidung umsetzen · depends-on: T0 (parallel zu T2–T4)
- **Z:** Der Auth.js-Beta-Pin ist adressiert.
- T5.1 **(Option A)** Auth.js-Beta → stable v5, sobald verfügbar; bis dahin Beta-Risiko dokumentiert (ADR-0016 O-4) · **DoD:** Pin stabil ODER Risiko-Zeile in ADR-0016; Login/Session-Flow grün · role: `codegen`
- T5.1' **(Option B)** next-auth → Ory Kratos/Hydra migrieren · **DoD:** Kratos-Session ersetzt JWT-Callback; `session.ts`/`config.ts` umgestellt; Tests grün · role: `codegen`

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
