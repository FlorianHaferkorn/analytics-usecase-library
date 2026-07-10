# ADR 0014 — Org-Schicht über lokal-first (Discovery, I-9.1)

- **Status:** Proposed. Wie bei ADR-0009 (I-8.1) gilt: ein Discovery-ADR mit Governance-Tragweite
  wird von einem Agenten nie eigenmächtig auf Accepted gesetzt — das braucht eine echte
  Maintainer-Ratifikation (E-x, nachzutragen, sobald sie stattfindet).
- **Date:** 2026-07-10
- **Scope:** Nur das **Modell + die Entscheidung** für eine Organisations-Schicht über Studios
  heutigem lokal-first-Design (I-9.1). **Kein Code, keine Migration** — Implementierung folgt in
  I-9.2 (geteilter Katalog + Rollen/Approvals serverseitig, opt-in), inkl. der
  Deployment-Topologie-Frage (lokale SQLite vs. gehosteter Shared-Server), die dieses ADR bewusst
  offen lässt.
- **Supersedes:** —
- **Related:** [`0007…`](0007-studio-generate-docks-onto-superversion-core.md) (lokal-first-Doktrin,
  Freigabe-Schleuse, ehrliche Degradation), [`0009…`](0009-wirkungs-loop-action-kpi-attribution.md)
  (Discovery-ADR-Präzedenz: Proposed bis Maintainer-Ratifikation), `PRODUCT_PLAN.md` (G5:
  Team/Multi-Tenant/RBAC — "customer-operable-solo first"), `docs/architecture/studio-capability-inventory.md`
  ("Multi-Tenant-Gerüst"), [`../../../UMSETZUNGSPLAN_SUPERVERSION.md`](../../../UMSETZUNGSPLAN_SUPERVERSION.md)
  (I-9), `studio/src/lib/db/sqlite.ts`, `studio/src/lib/db/rbac-repo.ts`,
  `studio/src/lib/auth/`, `core/organization/org_roles.yaml`.

---

## Context

**Wette (I-9, Z4):** Skalierung der Form, nicht der Arbeit — Mehrbenutzer/Rollen/geteilter Katalog
über demselben Core (Nagarro-Pfad), plus Branchen-Packs (I-9.3). Der Ledger benennt die Spannung
selbst: *"RBAC, Multi-Tenant widersprechen heutigem lokal-first-Design"* — deshalb **Discovery
zuerst**, kein Code (`UMSETZUNGSPLAN_SUPERVERSION.md:235-236`).

**Sequenz-Hinweis.** Der Ledger sequenziert I-9 explizit *"erst nach grüner I-10-Abnahme"*
(`UMSETZUNGSPLAN_SUPERVERSION.md:278`). I-10 ist inzwischen weitgehend grün (I-10.0–I-10.6
abgeschlossen), aber laut `docs/architecture/premium-acceptance-F0-F6.md` bleiben **F1** und
**F6-Teil2** ehrlich rot — beide brauchen einen echten Fabric-Tenant, den diese Sandbox nicht hat,
kein Code-Defekt. Dieses Discovery-ADR entsteht auf eine Anweisung des Maintainers **innerhalb
dieser Session** ("mach ... dann I-9"), diese Arbeit jetzt zu beginnen — festgehalten hier statt
stillschweigend über die Ledger-Sequenzierung hinwegzugehen. **Bewusste Einschränkung:** anders
als bei einer echten Ratifikation (s. Status) gibt es für diese Sequenz-Abweichung selbst **kein
externes, unabhängig prüfbares Artefakt** (kein Issue/Commit-Trailer) — nur den Konversationsverlauf
dieser Session. Dieses ADR bleibt trotzdem entsprechend vorsichtig eingestuft: **Proposed**, nicht
Accepted, und die Sequenz-Abweichung ist hier explizit benannt statt verschwiegen, damit ein
Reviewer sie selbst bewerten kann. Das Risiko der Abweichung ist gering: ein Discovery-ADR ändert
keinen Code und keinen Core.

**Was heute schon existiert (kein Neubau nötig):**

1. **Projekt-Scoping ist bereits real, nicht nur Schema-Stub.** `projects`/`project_members`
   (`sqlite.ts:38-55`) haben echtes CRUD (`project-repo.ts`) und eine echte UI
   (`ProjectSwitcher.tsx`: Cookie-basierter Projekt-Wechsel, Projekt anlegen). Der
   Ist-Zustand ist eher *"Ein Projekt per Default, Multi-Projekt end-to-end verdrahtet, aber
   nicht als Multi-Org/Multi-Tenant genutzt"* als "hart single-tenant".
2. **Auth trägt Projekt-Mitgliedschaft schon im Token.** NextAuth/JWT
   (`auth/config.ts`), der JWT-Callback lädt `project_memberships` (`{projectId, role}[]`) beim
   Login. Eine Org-Ebene daran anzuhängen ist inkrementell, kein Rewrite.
3. **RBAC ist strikt pro Projekt, ohne Hierarchie.** `rbac-repo.ts::checkAccess(projectId, userId,
   minRole)` schlägt genau eine `project_members`-Zeile nach — keine Vererbung, keine Gruppierung
   mehrerer Projekte. Das ist die eigentliche Lücke, die eine Org-Schicht schließen muss.
4. **Lokal-first/BYOK/Solo-Betrieb ist explizite Produktstrategie, nicht Zufall.** Login-Seite:
   *"Self-hosted · Your data stays local · BYOK for AI"*; `preflight.ts` (I-6.5) prüft Standalone-
   Betriebsfähigkeit; `PRODUCT_PLAN.md` benennt Team/Multi-Tenant/RBAC explizit als **G5**,
   aufgeschoben zugunsten *"customer-operable-solo first"*. Jede Org-Schicht muss **opt-in** sein
   (deckt sich mit I-9.2s eigener Formulierung *"serverseitig (opt-in)"*) und darf den
   Solo-Betrieb nicht verschlechtern — dieselbe ehrliche-Degradation-Doktrin wie ADR-0007 Regel 5,
   nur umgekehrt: *kein Org konfiguriert → verhält sich exakt wie heute*, nicht wie ein
   degradierter Modus.
5. **Drei verschiedene "Org"-Begriffe existieren bereits im Repo — nicht verwechseln:**
   - `core/organization/org_roles.yaml` — eine governte **Geschäfts-Rollen-Taxonomie** (flache
     Registry `{id, title, domain, ...}`), referenziert von den `owner_domain`/`owner_role`/
     `steward_role`-Feldern, die repo-weit in Action-Codes/Brackets vorkommen (nicht Felder von
     `org_roles.yaml` selbst — die Action-Codes zeigen per Rollen-ID auf diese Registry), pro
     Showcase austauschbar über `ANALYTICS_SHOWCASE`. Governter Content, kein Auth-Primitiv.
   - Studios `ProjectRole` (`admin`/`editor`/`viewer`) — Zugriffskontrolle pro Projekt, existiert
     bereits.
   - Die in diesem ADR zu entwerfende **Organisation** (Mandant/Firma, die mehrere Projekte + Nutzer
     gruppiert) — existiert noch nicht.
   - G1 ("Live-Tenant-Deploy", `UMSETZUNGSPLAN_SUPERVERSION.md:278`) meint einen **dritten,
     wieder anderen** "Tenant"-Begriff — den Ziel-Fabric-Workspace des Kunden, in den Studio
     Artefakte deployt. Auch das ist nicht dieselbe Sache wie die Org-Schicht hier.

## Decision

**Adoptiere eine additive, opt-in Organisations-Schicht über dem bestehenden Projekt-Modell —
minimal genug, um den Core unberührt zu lassen und den Solo-Betrieb byte-identisch zu erhalten.**

Acht Festlegungen:

1. **Zwei neue Tabellen, kein Umbau bestehender.** `organizations(id, name, created_at)` +
   `org_members(user_id, org_id, org_role, created_at, PK(user_id, org_id))` mit
   `org_role ∈ {owner, admin, member}` — eigenes Vokabular, nicht `ProjectRole` wiederverwendet
   (eine Org-Rolle ist kein Projekt-Zugriffslevel, s. Festlegung 4). `created_at` auf
   `org_members` (nicht nur auf `organizations`) konsequent zur Audit-Doktrin des restlichen
   Schemas — eine Org-Mitgliedschafts-Vergabe ist ein sicherheitsrelevantes Ereignis wie jede
   andere Statusänderung in diesem Repo. `projects.org_id → organizations.id` **ON DELETE SET
   NULL**: löscht man eine Org, fallen ihre Projekte auf `NULL` zurück (Solo-Modus) statt verwaist
   oder blockiert zu sein — verstärkt Festlegung 2 („NULL = primärer, nie kaputter Modus")
   strukturell statt nur als Text.

2. **`projects.org_id` als nullable FK.** `NULL` = lokal-first/Solo-Projekt (heutiger
   Default-Zustand, bleibt Default) — **kein degradierter Fallback, sondern der primäre,
   unveränderte Modus.** Multi-Tenancy ist eine Schicht *obendrauf*, nicht die neue Baseline.

3. **`project_members` bleibt die feingranulare Wahrheit, unverändert — auch über einen
   Org-Wechsel hinweg.** Keine Migration bestehender Zeilen nötig. Explizit festgelegt (nicht nur
   implizit aus Festlegung 4 folgend): wird ein Projekt einer Org zugeordnet oder zwischen Orgs
   verschoben, bleiben seine `project_members`-Zeilen unverändert bestehen — sie sind „sticky"
   und wandern nicht automatisch mit. Das kann bedeuten, dass ein Projekt nach einem Org-Wechsel
   noch explizite Zeilen aus einer früheren Zuordnung trägt, während neue Org-Mitglieder nur über
   den Fallback (Festlegung 4b) Zugriff haben — bewusst in Kauf genommen zugunsten von
   Vorhersagbarkeit (keine stille Zeilen-Migration bei einem Org-Wechsel).

4. **RBAC-Auflösung: explizite Projekt-Zeile schlägt Org-Rolle immer, kein Merge.** Reihenfolge in
   `checkAccess`: (a) existiert eine `project_members`-Zeile für `(projectId, userId)` → diese
   entscheidet, Punkt, unabhängig von jeder Org-Rolle; (b) sonst, falls das Projekt einer Org
   angehört (`org_id IS NOT NULL`) und der Nutzer Org-Mitglied ist → Org-Rolle als Fallback-Level
   (`owner`/`admin`→projektweit `admin`, `member`→projektweit `viewer` — **bewusst konservativ,
   kein Fallback-Pfad zu `editor`:** wer nur über die Org und nicht explizit auf dem Projekt
   berechtigt ist, bekommt entweder volle Admin-Rechte oder nur Lesezugriff, nichts dazwischen;
   eine feinere Abstufung kann I-9.2 bei Bedarf nachziehen); (c) sonst → kein Zugriff, wie heute.
   Kein Merge/Upgrade der beiden Ebenen — vorhersagbar, auditierbar, verhindert stille
   Privilegien-Eskalation über eine Org-Mitgliedschaft, wenn ein Projekt einen Nutzer explizit auf
   `viewer` gesetzt hat.
   **Anerkannter Kompromiss (nicht verschwiegen):** dieselbe Regel wirkt in beide Richtungen — eine
   explizite `viewer`-Zeile deckelt auch einen Org-`owner` unterhalb seiner Org-Rolle auf genau
   diesem Projekt. Da nur ein Projekt-Admin `project_members` ändern kann, ist ein Org-Owner mit
   einer alten, engen Projekt-Zeile potenziell von der Verwaltung eines Projekts seiner eigenen Org
   ausgesperrt — ein reales, vorhersehbares Deadlock-Szenario, keine Randnotiz. Die naheliegende
   Auflösung ist **kein Merge**, sondern ein separates, auditiertes **Org-Owner-Override**
   ("Break-Glass", z. B. eine explizite, geloggte Aktion statt stiller Rollen-Vereinigung) — als
   O-4 unten offen geführt statt hier vorwegzunehmen.

5. **Auth-Token erweitert, nicht ersetzt.** `org_memberships: {orgId, role}[]` zusätzlich zu
   `project_memberships` im JWT — additive Erweiterung des bestehenden Callbacks
   (`auth/config.ts`), kein neues Auth-System.

6. **Der Core bleibt governance-unwissend — das ist strukturell erzwungen, nicht nur behauptet.
   Das ist etwas anderes als eine Daten-Isolationsgarantie (s. u.).** Kein `org_id` (und kein
   `tenant`/`workspace`-Äquivalent) irgendwo unter `tooling/superversion/` oder `core/`. Der
   Bridge-Vertrag (`bridge.py`: Bracket-Pfad rein, JSON raus — unverändert seit ADR-0007) braucht
   keine Anpassung; eine Org-Schicht ist eine reine Studio/TypeScript-Erweiterung um `ProjectRole`
   herum, exakt wie `ProjectRole` selbst schon heute den Core nicht berührt. **Präzisierung, damit
   diese Festlegung nicht mehr verspricht als sie hält:** "der Core kann keine Org-Semantik lernen"
   ist etwas anderes als "der Core kann kein Daten-Leck zwischen Projekten verarbeiten". Der Bridge
   verarbeitet treu, welches Bracket-YAML Studio ihm übergibt — wenn ein Bug in Studios
   Projekt-Auflösung (nicht im Bridge selbst) dem Nutzer fälschlich das Bracket eines anderen
   Projekts zuspielt, ist der Bridge strukturell blind dagegen, genau weil er org-/projekt-unwissend
   ist. **Isolation bleibt vollständig ein Studio-seitiges `checkAccess`-/Projekt-Auflösungs-Problem
   — dieses ADR löst es nicht, es hält den Core nur aus der Verantwortung heraus.** Festlegung 4b
   (der neue Org-Fallback-Pfad) vergrößert diese Studio-seitige Prüf-Fläche sogar (eine weitere
   Bedingung, die `checkAccess` richtig auswerten muss), das ist ein Preis dieser Erweiterung, kein
   Nebeneffekt, der sich von selbst löst.

7. **Datenmodell ist für lokale Solo-/Multi-Projekt-Nutzung vollständig ausreichend; für eine
   echte gehostete Multi-Org-Instanz ist es eine notwendige, aber keine hinreichende Grundlage.**
   Im lokalen Fall (eine SQLite-Datei pro Installation = ein vertrauenswürdiger Kunde) reicht
   projekt-scopte Isolation über `project_id` aus, wie heute — die Org-Schicht ist dort reine
   Gruppierung ohne neue Sicherheitsgrenze. Für einen **gehosteten** Shared-Server, auf dem mehrere
   Orgs dieselbe Datenbank teilen, reicht dieses Modell **nicht automatisch**: keine der
   Leaf-Tabellen (`bracket_edits`, `discovery_sessions`, `audit_events`, `llm_step_events`,
   `ai_config_layers`, `notification_rules`, `refinement_lifecycle`, …) trägt eine `org_id`/
   `tenant_id`-Spalte — Mandantentrennung hinge dort vollständig davon ab, dass jede Abfrage die
   richtige `project_id` aus einem korrekten Org→Projekt-Join herleitet, ohne zweite,
   spalten-basierte Verteidigungslinie (Row-Level-Security oder eine `tenant_id` je Zeile). Das ist
   selbst eine **Datenmodell-Frage**, keine reine Deployment-Frage — deshalb hier explizit als O-5
   offen geführt statt stillschweigend unter „I-9.2 entscheidet Hosting" mitgemeint.

8. **Deployment-Topologie bleibt explizit I-9.2.** Ob eine Org ausschließlich lokal (eine SQLite pro
   Installation, mehrere Nutzer greifen z. B. über ein gemeinsames Netzlaufwerk/VPN darauf zu) oder
   über einen gehosteten Shared-Server läuft, entscheidet dieses ADR nicht — diese Frage ist
   orthogonal zum Datenmodell aus Festlegung 1–4 für den lokalen Fall, hängt aber am gehosteten
   Fall direkt an O-5 (Isolationsprimitive), s. Festlegung 7. Wird in I-9.2 getroffen, wenn ein
   echter Bedarf (Kundenkontext) vorliegt.

## Ratifiziert vs. aufgeschoben

- **Ratifiziert (Modell):** `organizations`/`org_members`-Schema-Form inkl. `created_at` auf
  beiden Tabellen und `ON DELETE SET NULL` auf `projects.org_id`; `projects.org_id` als nullable
  FK, `NULL` = Default/Solo (nicht Degradation); `project_members`-Zeilen bleiben „sticky" über
  Org-Zuordnungen/-Wechsel hinweg (keine stille Migration); RBAC-Auflösungsreihenfolge
  (Projekt-Zeile > Org-Rolle > kein Zugriff, kein Merge, Org-Fallback ohne `editor`-Stufe); der
  damit anerkannte Org-Owner-Lockout-Kompromiss (Festlegung 4) bleibt bewusst ungelöst und als O-4
  offen; Auth-Token-Erweiterung additiv; Core bleibt **governance**-unwissend (kein neuer
  Bridge-Parameter) — ausdrücklich **keine** Aussage über Daten-Isolation, die bleibt vollständig
  Studio-seitig; die drei bestehenden "Org"-Begriffe (Geschäfts-Rollen-Taxonomie / `ProjectRole` /
  G1-Tenant) bleiben getrennt, diese Org-Schicht ist ein viertes, eigenständiges Konzept; das
  Datenmodell ist für lokale Solo-/Multi-Projekt-Nutzung vollständig ausreichend, für gehostete
  Multi-Org-Nutzung notwendig aber nicht hinreichend (Festlegung 7).
- **Aufgeschoben (I-9.2), Stand nach dem lokal-only Slice (2026-07-10):** die
  Datenmodell-/RBAC-/Auth-Token-Festlegungen (1, 2, 3, 4, 5, 6) sind implementiert und getestet
  (`org-repo.ts`, `rbac-repo.ts::checkAccess`, `config.ts`/`org-membership-lookup.ts`, API-Routen
  unter `api/org/**`, minimale UI unter `/organizations`) — s. Ledger-Zeile I-9.2. **Weiterhin
  offen:** Deployment-Topologie (lokal vs. gehostet); Org-Einladungs-/Onboarding-UX inkl. Bootstrap
  der ersten `owner`-Zeile (O-1 — die Implementierung verlangt bewusst einen bereits existierenden
  Nutzer statt einen Phantom-Account zu provisionieren, entscheidet O-1 also nicht still mit);
  Isolationsprimitive für den gehosteten Fall — `tenant_id` je Leaf-Tabelle und/oder
  Row-Level-Security (O-5); Org-Owner-Break-Glass-Override-Mechanismus (O-4 — der lokal-only Slice
  verhindert stattdessen nur, dass der letzte Owner entfernt wird, löst das Lockout-Szenario aber
  nicht); ob/wie `core/organization/org_roles.yaml` für Anzeige-Zwecke (nicht Auth) verknüpft wird
  (O-3) — optional, nicht blockierend; Abrechnung/Kontingente, falls I-9.2 sich für gehostet
  entscheidet (O-2) — nur dann überhaupt relevant.

## Consequences

**Positiv**
- Additiv und rückwärtskompatibel: bestehende Solo-Nutzer (kein Org, `org_id IS NULL`) sehen
  keinerlei Verhaltensänderung — byte-identisch zum heutigen Zustand.
- Nutzt bestehende Maschinerie (Projekt-CRUD, `project_members`, Audit-Log, RBAC-Helper) statt
  Neubau — gleiches Muster wie die "parallel statt Refactor"-Entscheidung der
  Studio-Approval-Verdrahtung (kleine, saubere Erweiterung statt Umbau eines produktiv laufenden
  Systems).
- Der Core bleibt nachweisbar governance-unwissend, nicht nur behauptet: der Bridge-Vertrag hat
  keinen Ort, an dem Org-*Semantik* je auftauchen könnte. (Das ist bewusst enger formuliert als
  „der Core ist sicher" — s. Festlegung 6/Negativ unten.)

**Negativ / Kosten**
- `checkAccess` wird zweistufig (Projekt-Zeile, dann Org-Fallback) — mehr Testfläche, um stille
  Privilegien-Eskalation auszuschließen; Festlegung 4 (kein Merge) ist die Gegenmaßnahme, muss aber
  bei der Implementierung (I-9.2) durch Tests abgesichert werden, nicht nur durch dieses ADR.
- Daten-**Isolation** bleibt vollständig ungelöst und vollständig Studio-seitig — die
  Core-Unwissenheit aus Festlegung 6 schützt nicht vor einem Studio-seitigen
  Projekt-Auflösungs-Bug, der dem Bridge das falsche Bracket zuspielt; Festlegung 4b vergrößert
  diese Prüf-Fläche sogar leicht. Kein neues Risiko gegenüber heute (dasselbe gilt schon für
  `ProjectRole`), aber auch keine Verbesserung — nur ehrlich benannt statt durch Festlegung 6
  verdeckt.
- Der Org-Owner-Lockout-Kompromiss aus Festlegung 4 ist real, nicht nur theoretisch, und bleibt mit
  diesem ADR ungelöst (O-4).
- Für eine gehostete Topologie ist das Datenmodell allein nicht ausreichend (Festlegung 7/O-5) —
  löst keine Hosting-/Abrechnungs-/Einladungs-/Isolations-Fragen; diese bleiben nach diesem ADR
  vollständig offen.

**Neutral**
- Der Ist-Zustand ("Multi-Projekt schon verdrahtet") bedeutet, dieses ADR ist kleiner als ein
  Team/Multi-Tenant-Redesign von Grund auf — die eigentliche Neuerung ist ausschließlich die
  Gruppierungsebene (Org) über bereits vorhandenen Projekten.

## Alternatives considered

- **Globale (nicht projekt-gebundene) Rollen pro Nutzer.** Verworfen: bricht das bestehende,
  produktiv genutzte feingranulare Pro-Projekt-Modell (`project_members`); Nutzer, die mehreren
  Projekten mit unterschiedlichen Rollen angehören (heute schon möglich), würden diese Granularität
  verlieren.
- **`core/organization/org_roles.yaml` direkt als Auth-Rollen-Quelle wiederverwenden.** Verworfen:
  das ist eine governte, pro Showcase austauschbare Geschäfts-Content-Registry (wer stewardet
  welche KPI), kein Identitäts-/Zugriffsprimitiv. Eine Vermischung würde Content-Registry-Churn in
  Auth durchsickern lassen und die Showcase-Unabhängigkeit brechen.
- **RBAC-Merge (Projekt-Rolle UND Org-Rolle kombiniert, höhere gewinnt).** Verworfen zugunsten
  Festlegung 4 (explizite Projekt-Zeile gewinnt immer): ein Merge-nach-Maximum würde eine explizite
  `viewer`-Einschränkung eines Projekt-Admins durch eine spätere Org-`admin`-Mitgliedschaft
  unterlaufen können — unvorhersagbar und schwer auditierbar.
- **I-9.1 und I-9.2 in einem Schritt (Modell + Hosting-Entscheidung zusammen).** Verworfen:
  vermischt eine Datenmodell-Entscheidung mit einer Deployment-Topologie-Entscheidung; die
  lokal-first-Doktrin verlangt "customer-operable-solo first" — die Hosting-Frage sollte erst
  getroffen werden, wenn ein realer Kundenkontext sie beantwortbar macht (Präzedenz: ADR-0009s O-1/O-2
  bleiben aus demselben Grund bewusst offen).
- **Org als reines Tag/Namenskonvention auf `projects` statt eigener Tabelle.** Verworfen: eine
  Org braucht eigene Mitgliedschaft (`org_members`) und eigenen Lifecycle (anlegen/löschen,
  Festlegung 1) unabhängig von einem einzelnen Projekt — ein Tag auf `projects` könnte weder
  „Nutzer X gehört zu Org Y, unabhängig von jedem Projekt" noch „Org Y hat noch kein einziges
  Projekt" abbilden. Eine eigenständige Entität ist der kleinste Baustein, der beides trägt.
- **`tenant_id` auf jeder Leaf-Tabelle + Row-Level-Security von Anfang an, statt `project_id`-only
  mit späterer Nachrüstung.** Nicht verworfen, sondern **bewusst als O-5 offen geführt**: für den
  heute einzigen realen Betriebsmodus (lokal, ein Kunde pro Installation) wäre das vorgezogene
  Komplexität ohne Nutzen; für einen künftigen gehosteten Modus wäre es vermutlich die richtige
  Antwort. Diese Entscheidung jetzt zu erzwingen würde das lokal-first-Ziel „minimal genug"
  verletzen — sie gehört an den Punkt, an dem I-9.2 sich tatsächlich für gehostet entscheidet.

## Open decisions (an I-9.2 oder späteren Kundenkontext)

- **O-1 Org-Einladungs-/Onboarding-Flow, inkl. Bootstrap der ersten `owner`-Zeile.** Produkt-/
  UX-Entscheidung, aus dem Repo heraus nicht generisch beantwortbar.
- **O-2 Deployment-Topologie (lokal vs. gehostet) und alles, was gehostet mit sich bringt**
  (Abrechnung, Kontingente, Multi-Instance-Sync) — nur relevant, falls I-9.2 sich für gehostet
  entscheidet; bewusst nicht vorweggenommen.
- **O-3 Anzeige-Verknüpfung zu `core/organization/org_roles.yaml`** (z. B. Org-Mitglied ↔
  Business-Steward-Label in der Governance-UI) — optionale UX-Politur, nicht blockierend für I-9.2.
- **O-4 Org-Owner-Break-Glass-Override.** Festlegung 4 erkennt an, dass „kein Merge" einen
  Org-Owner unterhalb seiner Org-Rolle deckeln kann, wenn eine ältere, engere `project_members`-
  Zeile besteht (potenzielles Lockout-Szenario auf einem Projekt der eigenen Org). Ob/wie ein
  separater, auditierter Override-Mechanismus aussieht (statt eines stillen Rollen-Merges) ist
  eine echte Sicherheits-/UX-Abwägung, die I-9.2 mit Tests treffen muss, nicht dieses ADR.
- **O-5 Isolationsprimitive für eine gehostete Topologie.** `tenant_id` je Leaf-Tabelle und/oder
  Row-Level-Security vs. ausschließlich `project_id`-Joins — nur relevant, falls I-9.2 sich für
  gehostet entscheidet (s. O-2), aber selbst dann eine Datenmodell-Entscheidung, keine reine
  Infrastruktur-Frage (Festlegung 7). Bewusst nicht vorweggenommen, da ohne realen
  Mehrmandanten-Betrieb nicht generisch entscheidbar — dieselbe DoD-Fehlerfall-Klausel wie bei
  ADR-0009s O-1/O-2 ("Kundenkontext nötig → als bewusst-offen markieren, nicht raten").

## References

- Intern: `studio/src/lib/db/sqlite.ts` (`projects`/`project_members`-Schema),
  `studio/src/lib/db/rbac-repo.ts` (`checkAccess`), `studio/src/lib/db/project-repo.ts`,
  `studio/src/components/AppShell/ProjectSwitcher.tsx`, `studio/src/lib/auth/config.ts`
  (JWT-Callback, `project_memberships`), `studio/src/lib/auth/require-role.ts`,
  `studio/src/lib/setup/preflight.ts` (lokal-first/BYOK-Doktrin, I-6.5),
  `core/organization/org_roles.yaml` + `core/organization/README.md`,
  `docs/architecture/studio-capability-inventory.md`, `PRODUCT_PLAN.md` (G5),
  `UMSETZUNGSPLAN_SUPERVERSION.md` (I-9, I-10-Gate-Hinweis Zeile 278),
  [`0007…`](0007-studio-generate-docks-onto-superversion-core.md),
  [`0009…`](0009-wirkungs-loop-action-kpi-attribution.md) (Discovery-ADR- und
  Ratifikations-Präzedenz).
