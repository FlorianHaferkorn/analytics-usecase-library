# ReBAC-Schema (engine-neutral) — Backlog T2

> **Status:** Draft-Spec (kein Code). Bildet das heute handgebaute `checkAccess`
> ([`../../../studio/src/lib/db/rbac-repo.ts`](../../../studio/src/lib/db/rbac-repo.ts)) +
> die ADR-0014-Auflösung als **deklaratives Relations-Modell** ab. Companion zu
> [`authn-authz-stack-build-backlog.md`](authn-authz-stack-build-backlog.md) (T2) und
> [`../adr/0014-org-layer-over-local-first.md`](../adr/0014-org-layer-over-local-first.md).
>
> **Engine-neutral:** die kanonische Relations-Definition (§2) ist die Autorität; die
> OpenFGA-Fassung (§3, gewählter Stack A) und die Ory-Keto-Parität (§4) sind daraus
> **abgeleitet** — ein späterer A→B-Wechsel bleibt so offen (ADR-0016 O-1).
> **Datensparsamkeit (T1 §2):** Subjekt jeder Relation ist ausschließlich die pseudonyme
> `usr-…`-ID — nie E-Mail/Name.

## 1. Ist-Modell (T2.1) — belegt aus dem Code

**Rollen-Hierarchien** (`studio/src/lib/auth/rbac-types.ts`):
- Projekt: `viewer < editor < admin` (`ROLE_HIERARCHY`).
- Org: `member < admin < owner` (`ORG_ROLE_HIERARCHY`).
- `roleAtLeast(userRole, minRole)` = Index-Vergleich.
- `projectRoleFromOrgRole`: **owner/admin → admin, member → viewer** — bewusst **kein**
  Fallback-Pfad zu `editor`.

**Auflösung** (`checkAccess(projectId, userId, minRole)`, `rbac-repo.ts`, ADR-0014 Festlegung 4):
1. Existiert eine explizite `project_members`-Zeile für `(projectId, userId)` → **sie
   entscheidet, Punkt** (`roleAtLeast(row.role, minRole)`), **unabhängig von jeder
   Org-Rolle, kein Merge, kein Upgrade**.
2. Sonst, falls das Projekt einer Org angehört (`projects.org_id != NULL`) **und** der
   Nutzer Org-Mitglied ist (`checkOrgAccess(org, user, 'member')`) → Org-Rolle als
   **Fallback-Level** (`projectRoleFromOrgRole`).
3. Sonst → **kein Zugriff**.

**Die kritische, nicht-additive Eigenschaft:** Stufe 1 wirkt **in beide Richtungen** — eine
explizite `viewer`-Zeile **deckelt** auch einen Org-`owner` auf `viewer` für genau dieses
Projekt (ADR-0014 O-4-Lockout). Das ist **kein** „höhere Rolle gewinnt", sondern
„explizite Zeile **überschreibt** die Org-Ableitung vollständig".

## 2. Kanonisches Relations-Modell (T2.2, engine-neutral)

**Typen:** `user`, `organization`, `project`.

| Typ | Relation | Algebra | Bedeutung |
|---|---|---|---|
| `organization` | `owner` | direkt `[user]` | Org-Owner |
| | `admin` | `[user] ∪ owner` | Org-Admin (owner ist auch admin) |
| | `member` | `[user] ∪ admin` | Org-Mitglied (owner/admin sind auch member) |
| `project` | `parent` | direkt `[organization]` | `org_id`-FK; **fehlt = Solo-Projekt** |
| | `admin_explicit` | direkt `[user]` | explizite `project_members`-Zeile Rolle admin |
| | `editor_explicit` | direkt `[user]` | … editor |
| | `viewer_explicit` | direkt `[user]` | … viewer |
| | `explicit_any` | `admin_explicit ∪ editor_explicit ∪ viewer_explicit` | **„hat irgendeine explizite Zeile" — der Override-Schalter** |
| | `org_admin_src` | `admin` **from** `parent` | owner/admin der Parent-Org (→ mappt auf Projekt-admin) |
| | `org_view_src` | `member` **from** `parent` | jedes Mitglied der Parent-Org (→ mappt auf Projekt-viewer) |
| | `admin_fallback` | `org_admin_src` **∖ (but not)** `explicit_any` | Org-admin-Fallback, **nur wenn keine explizite Zeile** |
| | `view_fallback` | `org_view_src` **∖ (but not)** `explicit_any` | Org-viewer-Fallback, **nur wenn keine explizite Zeile** |
| | `can_admin` | `admin_explicit ∪ admin_fallback` | effektives Admin-Recht |
| | `can_edit` | `editor_explicit ∪ admin_explicit ∪ admin_fallback` | effektives Edit-Recht (**kein** Org-Editor-Pfad) |
| | `can_view` | `viewer_explicit ∪ editor_explicit ∪ admin_explicit ∪ view_fallback` | effektives View-Recht |

**Der Kern-Trick — die `but not`-Exklusion.** Zanzibar/ReBAC ist von Haus aus ein
**Vereinigungs-Modell** (additiv, „OR"). Die ADR-0014-„explizite-Zeile-überschreibt-auch-nach-unten,
kein-Merge"-Semantik ist **nicht additiv** und lässt sich **nur** über den
**Differenz-Operator** (`but not`) ausdrücken: der Org-Fallback gilt genau dann, wenn der
Nutzer **keine** explizite Zeile hat (`… but not explicit_any`). **Das ist der eine
nicht-triviale Punkt des ganzen Modells** — und der Grund, warum die gewählte Engine
`but not`/Exklusion beherrschen muss (OpenFGA und Ory Keto tun das).

## 3. OpenFGA-Fassung (Stack A) — abgeleitet aus §2

```
model
  schema 1.1

type user

type organization
  relations
    define owner: [user]
    define admin: [user] or owner
    define member: [user] or admin

type project
  relations
    define parent: [organization]

    define admin_explicit: [user]
    define editor_explicit: [user]
    define viewer_explicit: [user]

    define explicit_any: admin_explicit or editor_explicit or viewer_explicit

    define org_admin_src: admin from parent
    define org_view_src: member from parent

    # Override: Org-Fallback nur ohne explizite Zeile (die nicht-additive Stelle)
    define admin_fallback: org_admin_src but not explicit_any
    define view_fallback: org_view_src but not explicit_any

    define can_admin: admin_explicit or admin_fallback
    define can_edit: editor_explicit or admin_explicit or admin_fallback
    define can_view: viewer_explicit or editor_explicit or admin_explicit or view_fallback
```

> Bewusst über **Hilfsrelationen** (`admin_fallback`/`view_fallback` = je ein einzelnes
> `but not`) modelliert statt `or`/`but not` inline zu schachteln — das ist über
> OpenFGA-Versionen hinweg das robusteste Idiom.

**Query-Mapping:** `checkAccess(P, U, 'admin')` → `check(user:U, can_admin, project:P)`;
`'editor'` → `can_edit`; `'viewer'` → `can_view`. Der `minRole`-Vergleich der Alt-Logik
wird also durch **drei distinkte computed relations** ersetzt (kein Laufzeit-Ranking mehr).

## 4. Ory-Keto-Parität (Stack B, reife-gebunden) — Struktur identisch

Ory Keto (OPL) nutzt dasselbe Userset-Rewrite-Modell inkl. Ausschluss. Die §2-Relationen
mappen 1:1: `owner/admin/member` als Namespace-`organization`-Relationen, die
`*_explicit`/`can_*` als `project`-Relationen, `admin from parent` als
Subject-Set-Traversal, `but not` als Ausschluss in der Permit-Regel. Damit ist der
A→B-Wechsel ein **Re-Rendering derselben kanonischen §2-Tabelle**, kein Neuentwurf.

## 5. Verifikations-Matrix (T2.3) — reproduziert die ADR-0014-Fälle

Tupel-Notation: `P#parent@O` = Projekt P gehört zu Org O; `O#owner@U` = U ist Owner von O;
`P#viewer_explicit@U` = explizite Projekt-viewer-Zeile.

| # | Tupel-Setup | can_view | can_edit | can_admin | Alt-Code-Erwartung |
|---|---|---|---|---|---|
| 1 | `P#parent@O`, `O#owner@U`, `P#viewer_explicit@U` | ✓ | ✗ | ✗ | explizite viewer-Zeile **deckelt Org-Owner** (O-4-Lockout) |
| 2 | `P#parent@O`, `O#owner@U` (keine Zeile) | ✓ | ✓ | ✓ | Org-owner-Fallback → admin |
| 3 | `P#parent@O`, `O#member@U` (keine Zeile) | ✓ | ✗ | ✗ | Org-member-Fallback → viewer |
| 4 | `P` solo (kein parent), `P#admin_explicit@U` | ✓ | ✓ | ✓ | explizite admin-Zeile |
| 5 | `P#parent@O`, `O#owner@U`, `P#editor_explicit@U` | ✓ | ✓ | ✗ | explizite editor-Zeile deckelt Owner |
| 6 | `P` solo, U ohne alles | ✗ | ✗ | ✗ | kein Zugriff |
| 7 | `P#parent@O`, `O#admin@U` (keine Zeile) | ✓ | ✓ | ✓ | Org-admin-Fallback → admin |
| 8 | `P#parent@O`, U **nicht** in O | ✗ | ✗ | ✗ | keine Mitgliedschaft |

Jede Zeile ist ein späterer Test (`check()` gegen die Engine) — die DoD von T2.3.

**Verifiziert (2026-07-15):** Diese Matrix wurde gegen einen eigenständigen Referenz-Evaluator
des §2-Modells laufen gelassen — **9/9 Fälle bestehen** (inkl. Owner-Lockout Fall 1/5 und
Break-Glass Fall 9). Die Vektoren sind engine-agnostisch als
[`authz-fga-cases.json`](authz-fga-cases.json) abgelegt und dienen sowohl der späteren
OpenFGA-`check()`-Suite (T3.2) als auch jedem Re-Rendering (Keto). Der Evaluator selbst ist
ein Wegwerf-Verifikat (nicht committet, um kein drittes drift-fähiges Modell zu schaffen — SoT
bleibt §2/§3 + die Vektoren).

## 6. Break-Glass (ADR-0014 O-4) — im ReBAC-Modell ohne Sonderlogik

Das Lockout-Szenario (Fall 1) löst ADR-0014 über eine separate, auditierte Mutation
(`POST /api/org/[orgId]/break-glass`). Im Relations-Modell ist das schlicht **das Schreiben
eines expliziten Tupels** `P#admin_explicit@U` durch den Org-Owner:

| # | Setup | can_admin |
|---|---|---|
| 9 | Fall 1 **+** Owner schreibt `P#admin_explicit@U` (Break-Glass) | ✓ (`admin_explicit` gewinnt) |

- **Auditierbar von Natur aus:** Break-Glass = ein Tupel-Write (mit Pflicht-Begründung im
  API-Layer), Self-Revert = Tupel-Delete. Kein stiller Rollen-Merge in der Auflösung — exakt
  ADR-0014s Anspruch, hier ohne Schema-Sonderfall erfüllt.
- **ADR-0014-Härtung (a)** „POST verweigert, wenn Owner ohnehin schon admin ist" bleibt eine
  **API-Layer-Regel** (T3), nicht Teil des Schemas — das Schema drückt nur den End-Zustand aus.

## 7. Offene Punkte → Folge-Tasks

- **T3 (Engine-Anbindung):** `checkAccess` → `check(can_*)`-Adapter hinter Feature-Flag;
  Break-Glass-API-Härtung (a)/(b) bleibt im API-Layer.
- **T4 (Migration):** `project_members`/`org_members`-Zeilen → Relation-Tupel
  (`*_explicit` bzw. `owner/admin/member`), Roundtrip gegen diese Matrix.
- **Solo-Projekt (`org_id NULL`):** kein `parent`-Tupel → beide Fallbacks leer → Verhalten
  byte-identisch zum heutigen Solo-Modus (ADR-0014 Festlegung 2).
- **`business_role_id`** (ADR-0014 O-3, reine Anzeige) bleibt **außerhalb** des ReBAC-Schemas
  — kein Auth-Primitiv, wird nie von `check()` gelesen.
