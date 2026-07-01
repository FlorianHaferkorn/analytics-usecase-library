# ADR 0010 — Team-/Org-Schicht + Industry-Packs über dem lokal-first-Core

- **Status:** Proposed
- **Date:** 2026-07-01
- **Scope:** Das **Modell + die Verträge** für die Skalierung der *Form* (Mehrbenutzer, Rollen, geteilter Katalog, Branchen-Packs) über demselben Core (I-9), **ohne** das lokal-first-Design (ADR-0007, BYO-Key, SQLite-lokal, standalone) zu brechen. **Kein Code** — Discovery. Implementierung folgt in I-9.2 (geteilter Katalog + Rollen/Approvals serverseitig, opt-in) / I-9.3 (erstes Industry-Pack als Content-Pack).
- **Supersedes:** —
- **Related:** [`0003-customer-activation-and-capability-gating.md`](0003-customer-activation-and-capability-gating.md) (Aktivierung/Capability-Gating), [`0004-industry-variant-use-case-tier-taxonomy.md`](0004-industry-variant-use-case-tier-taxonomy.md) (Industry-Taxonomie = Pack-Inhalt), [`0007-studio-generate-docks-onto-superversion-core.md`](0007-studio-generate-docks-onto-superversion-core.md) (lokal-first + Freigabe-Schleuse), [`0008-ai-orchestration-routing-tokens-tracking-roi-config.md`](0008-ai-orchestration-routing-tokens-tracking-roi-config.md) (L0/L1/L2-Config-Schichtung als Präzedenz-Muster), `studio/src/lib/db/rbac-repo.ts`, `studio/src/lib/governance/approval-workflow.ts`, `studio/src/lib/db/audit-chain.ts`, [`../../../UMSETZUNGSPLAN_SUPERVERSION.md`](../../../UMSETZUNGSPLAN_SUPERVERSION.md) (I-9)

---

## Context

**Wette (I-9):** Skalierung der *Form*, nicht der Arbeit — mehrere Bearbeiter, Rollen,
ein geteilter Katalog (Nagarro-Pfad) und Branchen-Packs über demselben governten Core.
Das ist die Z4-Wette: der Wert wird organisatorisch multipliziert, ohne den Core neu zu
bauen.

Das ist **Neuland gegenüber dem heutigen Design**, aber die **Primitive existieren im
Repo bereits** (deshalb ein Modell-ADR und keine grüne-Wiese-Erfindung):

- **Per-Projekt-RBAC ist schon da:** `studio/src/lib/db/rbac-repo.ts` führt
  `project_members` mit Rollen `admin | editor | viewer` (`roleAtLeast`-Ordnung),
  Ersteller wird Admin, `checkAccess` gated Zugriffe. Rollen sind kein Neubau — sie
  sind heute nur lokal, single-user-dominiert.
- **Approvals + Zwei-Personen-Regel sind schon da:** `studio/src/lib/governance/approval-workflow.ts`
  + `review-repo.ts` implementieren die Freigabe-Schleuse (ADR-0007) — genau das Gate,
  das ein geteilter Katalog für konfliktfreie Mehrbenutzer-Mutation braucht.
- **Tamper-evidenter Audit ist schon da:** `studio/src/lib/db/audit-chain.ts` (Hash-Kette)
  — die Grundlage für „wer hat was am geteilten Katalog geändert" ohne Vertrauensbruch.
- **Industry-Identität ist schon ratifiziert:** ADR-0004 entscheidet Identität + Foldering
  für cross-industry-/sektor-Varianten (`EXT`/`IND-*`, `core/usecases/industry/`). Ein
  Industry-Pack ist damit **Inhalt** über einer entschiedenen Taxonomie, keine neue
  Governance.
- **Schicht-Präzedenz ist schon modelliert:** ADR-0008 hat L0/L1/L2 (universal → org → kunde)
  mit Merge-Regeln + Freigabe-Schleuse für L1/L2 eingeführt — dasselbe Muster trägt einen
  „org-über-lokal"-Katalog.

Was fehlt, ist das **Schicht-Modell**, das eine optionale Org-Schicht *über* das
lokal-first-Design legt — so, dass der Standalone-Einzelnutzer (BYO-Key, keine Server,
kein Account) **unverändert weiterläuft** und die Org-Schicht rein additiv + opt-in ist.

## Decision

**Adoptiere eine optionale, additive Team-/Org-Schicht als „geteilter Ursprung + lokale
Arbeitskopie", die den lokal-first-Core nie voraussetzt: Der geteilte Katalog ist eine
weitere, höher-präzedente Config-/Content-Schicht (Muster wie ADR-0008 L0/L1/L2), Rollen
+ Approvals sind die schon vorhandenen RBAC-/Freigabe-Primitive serverseitig gespiegelt,
und ein Industry-Pack ist ein versioniertes, signierbares Content-Bündel über der
ADR-0004-Taxonomie — nie eine neue Governance oder eine Core-Mutation.**

Sechs Festlegungen:

1. **Lokal-first bleibt der Default, Org ist opt-in + additiv.** Ohne konfigurierte
   Org-Schicht verhält sich das Studio exakt wie heute (ADR-0007): ein Nutzer, lokale
   SQLite, BYO-Key, keine Server-Abhängigkeit. Die Org-Schicht ist **zusätzlich**
   einschaltbar; sie darf keinen lokal-first-Pfad zur Voraussetzung machen. Fehlt der
   Server → lokal weiterarbeiten, nicht blockieren (offline-tolerant).

2. **Geteilter Katalog = geteilter Ursprung + lokale Arbeitskopie.** Der Org-Katalog ist
   die höher-präzedente Schicht (Analogie ADR-0008: universal < org < lokal-kunde). Ein
   Bearbeiter zieht den geteilten Stand, arbeitet lokal, und **schlägt** Änderungen zum
   geteilten Katalog **vor** — er schreibt ihn nie direkt. Zwei Bearbeiter driften nicht,
   weil der geteilte Stand nur über die Freigabe-Schleuse (Festlegung 4) mutiert.

3. **Rollen = die vorhandenen RBAC-Rollen, serverseitig gespiegelt.** Keine neue
   Rollen-Ontologie: `admin | editor | viewer` aus `rbac-repo.ts` (`roleAtLeast`) gelten
   auch für den geteilten Katalog. `viewer` liest, `editor` schlägt vor, `admin` verwaltet
   Mitglieder + gibt frei. Der server-Modus spiegelt dasselbe Modell, das lokal schon gilt.

4. **Mutation des geteilten Katalogs nur über die Freigabe-Schleuse.** Jede Änderung am
   geteilten Katalog läuft durch `approval-workflow.ts` (Zwei-Personen-Regel, ADR-0007) und
   wird in der Audit-Hash-Kette (`audit-chain.ts`) verankert. „2 Bearbeiter parallel ohne
   Drift" (I-9-Messgröße) ist damit strukturell: konkurrierende Vorschläge werden gereiht +
   gegated, nicht last-write-wins überschrieben.

5. **Industry-Pack = versioniertes, signierbares Content-Bündel über ADR-0004.** Ein Pack
   ist ein deklaratives Bündel (Use-Cases/KPIs-Referenzen/Action-Code-Referenzen/Themes)
   mit `pack_id`, `version`, Kompatibilitäts-Range zum Core-Schema und optionaler Signatur.
   Es **referenziert** governte KPIs/Action-Codes (Golden Thread) und **definiert nie**
   Bedeutung/Target neu; es nutzt die ADR-0004-Identität (`IND-*`/`EXT`). „1 Pack lädt"
   heißt: validiert gegen das Core-Schema, Referenzen lösen auf, lädt additiv — bricht
   nichts Bestehendes.

6. **Determinismus + Golden Thread + Ehrlichkeit.** Derselbe geteilte Stand + dasselbe Pack
   → derselbe aufgelöste Katalog (testbar). Die Org-Schicht **referenziert** governte
   Definitionen, mutiert den Core nie automatisch, und labelt Server-/Sync-Zustände ehrlich
   (z. B. „lokal, nicht synchronisiert" statt stiller Fehlannahme von Aktualität).

## Ratifiziert vs. aufgeschoben

- **Ratifiziert (Modell + Verträge):** Org-als-additive-opt-in-Schicht; geteilter Katalog =
  geteilter Ursprung + lokale Arbeitskopie mit Vorschlag-nicht-Direktschreiben;
  Wiederverwendung der RBAC-Rollen + Freigabe-Schleuse + Audit-Kette; Industry-Pack als
  versioniertes Content-Bündel über ADR-0004; die Invarianten (lokal-first-Default,
  Golden Thread, kein Auto-Mutate, ehrliche Sync-Labels).
- **Aufgeschoben (Implementierung):** I-9.2 = serverseitiger geteilter Katalog + Rollen/
  Approvals (opt-in) konkret verdrahtet, Sync-/Vorschlag-Protokoll, Konflikt-Reihung;
  I-9.3 = erstes Industry-Pack (Manufacturing — Meridian-Skizze) als ladbares Content-Pack.
  Messgröße: **2 Bearbeiter parallel an einem Katalog ohne Drift; 1 Branchen-Pack lädt.**

## Consequences

**Positiv**
- Skaliert die Form auf den schon vorhandenen Primitiven (RBAC, Approval, Audit, ADR-0004-
  Taxonomie, ADR-0008-Schichtung) — minimaler Neubau, maximale Kohärenz.
- Lokal-first bleibt unangetastet: der Standalone-Einzelnutzer verliert nichts, die
  Org-Schicht ist rein additiv + abschaltbar.
- Drift-frei by design: geteilter Katalog mutiert nur gegated (Zwei-Personen) + auditiert,
  nicht last-write-wins.

**Negativ / Kosten**
- Ein Server-Modus (opt-in) bringt Betriebsfläche (Hosting, Auth, Konflikt-Reihung), die
  lokal-first nicht hatte — bewusst hinter opt-in gehalten, nicht dem Einzelnutzer aufgezwungen.
- Sync zwischen geteiltem Ursprung + lokaler Arbeitskopie ist ein echtes verteiltes Problem
  (Konflikte, Staleness); ehrlich zu labeln statt Aktualität zu fingieren.

**Neutral**
- Die Schicht ist bewusst **katalog-/content-, nicht workflow-orchestrierungs-vollständig**:
  kein Multi-Tenant-Billing, keine Org-weite Job-Orchestrierung in I-9 — späteres Neuland,
  falls je nötig.

## Alternatives considered

- **Multi-Tenant-first (Server als Default) neu bauen.** Verworfen: bricht das lokal-first-
  Versprechen (ADR-0007), erzwingt Server/Account für alle, dupliziert Governance. Die
  Org-Schicht muss additiv über lokal-first liegen, nicht es ersetzen.
- **Neue Rollen-/Governance-Ontologie für „Org".** Verworfen: `rbac-repo.ts` +
  `approval-workflow.ts` + `audit-chain.ts` decken Rollen, Freigabe + Nachweis bereits ab.
  Eine zweite Ontologie wäre Drift-Quelle.
- **Industry-Pack als Code-Fork / neue KPI-/Action-Namespaces.** Verworfen: verletzt Golden
  Thread + ADR-0004. Ein Pack referenziert governte Definitionen, es erfindet keine.
- **Direktschreiben in den geteilten Katalog (last-write-wins).** Verworfen: erzeugt genau
  die Drift, die die I-9-Messgröße ausschließt. Mutation bleibt gegated (Festlegung 4).

## Open decisions (vor/within I-9.2/9.3)

- **O-1 Sync-Protokoll:** Pull-geteilter-Ursprung + push-als-Vorschlag — konkretes Format
  (Diff/Patch vs. voller Snapshot), Konflikt-Reihung + Staleness-Signal.
- **O-2 Server-Speicher + Auth:** wo lebt der geteilte Katalog serverseitig (SQLite-gespiegelt
  vs. anderer Store), und welcher Auth-Kontext liefert `user_id`/`role` server-seitig (heute
  lokal implizit).
- **O-3 Pack-Manifest + Signatur:** genaues `pack_id`/`version`/Kompatibilitäts-Range-Schema,
  ob + wie Packs signiert/verifiziert werden, und der Lade-/Validierungs-Vertrag.
- **O-4 Pack-Layering vs. Core:** Präzedenz eines Packs relativ zu core-16 + geteiltem Katalog
  (additiv-only vs. override), analog zur ADR-0008-Merge-Semantik.

## References

- Intern: `studio/src/lib/db/rbac-repo.ts` (`project_members`, `admin/editor/viewer`, `checkAccess`),
  `studio/src/lib/governance/approval-workflow.ts` + `governance/review-repo.ts` (Freigabe-Schleuse,
  Zwei-Personen-Regel), `studio/src/lib/db/audit-chain.ts` (tamper-evidenter Audit),
  [`0003-customer-activation-and-capability-gating.md`](0003-customer-activation-and-capability-gating.md),
  [`0004-industry-variant-use-case-tier-taxonomy.md`](0004-industry-variant-use-case-tier-taxonomy.md),
  [`0007-studio-generate-docks-onto-superversion-core.md`](0007-studio-generate-docks-onto-superversion-core.md),
  [`0008-ai-orchestration-routing-tokens-tracking-roi-config.md`](0008-ai-orchestration-routing-tokens-tracking-roi-config.md),
  `UMSETZUNGSPLAN_SUPERVERSION.md` (I-9).
- Extern (Muster, by reference): geteilter-Ursprung-plus-Arbeitskopie (VCS-artig), Zwei-Personen-
  Freigabe, opt-in-additive-Schichtung — Standard-Ansätze; live zu vertiefen, falls I-9.2 über den
  Katalog-Sync hinausgeht.
