# ADR 0016 — AuthN/AuthZ-Stack für die Studios (Descope-Prior-Art → EU-OSS-Optionen)

- **Status:** Proposed. Wie bei ADR-0009/0014 gilt: ein ADR mit Governance-/Compliance-Tragweite
  wird von einem Agenten nie eigenmächtig auf Accepted gesetzt — das braucht eine echte
  Maintainer-Ratifikation. Dieses ADR trifft **keine** Stack-Wahl; es stellt zwei gleichwertige
  Optionen mit dem entscheidenden Kriterium gegenüber, damit der Maintainer entscheidet.
- **Date:** 2026-07-15
- **Scope:** Nur die **Bewertung + der Entscheidungsrahmen** für den geteilten AuthN/AuthZ-Stack
  beider Studios (ActionReady Studio = ALUCA, Meridian Studio = Freelancing). **Kein Code, keine
  Migration.** Auslöser war die Frage, ob sich die Descope-Ansätze (deklarative Auth-Flows +
  Zanzibar-artige Fine-Grained-Authorization) für uns übertragen lassen — selbst gebaut und/oder
  über ein EU-/Open-Source-Gegenstück.
- **Supersedes:** —
- **Related:** [`0014-org-layer-over-local-first.md`](0014-org-layer-over-local-first.md)
  (das bestehende, handgebaute Pro-Projekt-/Org-RBAC-Modell, das dieses ADR als Ist-Zustand
  voraussetzt und dessen AuthZ-Schicht die hier bewerteten Optionen ersetzen bzw. formalisieren
  würden), [`0007-studio-generate-docks-onto-superversion-core.md`](0007-studio-generate-docks-onto-superversion-core.md)
  (lokal-first/BYOK-Doktrin, ehrliche Degradation), `../../studio/src/lib/auth/config.ts`
  (NextAuth/JWT-Callback), `../../studio/src/lib/auth/require-role.ts`,
  `../../studio/src/lib/db/rbac-repo.ts` (`checkAccess`), `../../studio/package.json`
  (`next-auth ^5.0.0-beta.30`), `../../compliance/_INDEX.md` (EU-Hosting/AVV/Art.-30 —
  das Entscheidungskriterium). **Cross-Repo:** ein feld-gespiegelter Decision-Stub liegt in
  Freelancing/Meridian `meridian/studio/DECISIONS.md` (SaaS-Auth-Adapter-Pfad), da Meridian
  denselben Stack teilen soll, sobald es auf ALUCA-Niveau gehoben wird.

---

## Context

**Ausgangsfrage (Maintainer, diese Session):** „Können wir die Descope-Ansätze für uns übernehmen,
aber selbst machen? Gibt es ein EU-Gegenstück, bestenfalls kostenlos? Meridian soll künftig auf
dieselbe Stufe wie ActionReady Studio kommen."

**Descope** ist eine Managed-CIAM-Cloud (US-SaaS): deklarative Auth-Flows (Login-Journeys als
versionierte Config statt Code) + Fine-Grained-Authorization im Zanzibar-Stil (Relations-Schema +
`check()`-API). Zwei Beobachtungen entkoppeln „Ansatz" von „Produkt":

1. **Deklarative Flows** sind wertvoll, aber eine eigene Flow-Engine nachzubauen lohnt nicht — das
   liefert jeder ausgereifte IdP mit.
2. **Zanzibar-ReBAC** ist der eigentlich übertragbare Kern und existiert vollständig als
   self-hostbare Open Source (OpenFGA, SpiceDB, Ory Keto — alle Apache-2.0).

**Ist-Zustand ALUCA (kein Neubau nötig, aber Lücke benannt):**

- **AuthN:** `next-auth` / Auth.js v5 (JWT-Cookie via `auth()`, `studio/src/lib/auth/config.ts`).
  Der Pin ist **Beta** (`^5.0.0-beta.30`) — ein bewusst zu benennendes Risiko für ein
  Endprodukt-Niveau (Charter-Analogie D-155: Endprodukte bestehen die offiziellen Validatoren ihrer
  Zielplattform).
- **AuthZ:** **handgebaut** — `require-role.ts` → `checkAccess(projectId, userId, minRole)` in
  `rbac-repo.ts`, plus Org-Fallback aus ADR-0014 (`org-membership-lookup.ts`). Das ist ein
  funktionierendes, aber selbst gepflegtes RBAC — genau die Fläche, die ein Zanzibar-Modell
  deklarativ und auditierbar ablöst.

**Ist-Zustand Meridian (Scope-Grenze):** Single-File-HTML, per Doppelklick beim Kunden, **bewusst
kein Backend/Login/SaaS** (Charter-Regel 5, „Adapter-Pattern für späteren SaaS-Pfad"). Descope hat
dort **heute keinen Platz**; die Frage ist ausschließlich der *künftige* SaaS-Pfad. „Auf dieselbe
Stufe wie ALUCA" heißt konkret: **derselbe** AuthN/AuthZ-Stack — sonst driften die beiden Studios in
zwei Auth-Systeme auseinander. Deshalb ist die Stack-Wahl hier eine gemeinsame, keine
ALUCA-lokale.

**Doktrin als Entscheider, nicht die Feature-Liste.** Der ALUCA-Kern ist DSGVO / EU-Hosting /
Vendor-Unabhängigkeit / self-hostable (DE-Markt, `compliance/_INDEX.md`; Login-Seite:
„Self-hosted · Your data stays local"). Eine Managed-US-CIAM-Cloud liefe dieser Posture direkt
zuwider (Data-Residency, AVV, Vendor-Lock-in). **Das entscheidet die Sache — nicht, welche Option
mehr Häkchen hat.**

## Decision

**Keine Stack-Wahl in diesem ADR.** Festgelegt wird nur der Rahmen:

1. **Descope (und jede Managed-US-CIAM-Cloud) ist als Laufzeit-Abhängigkeit für die Studios
   ausgeschlossen** — unvereinbar mit der EU-Hosting-/Self-Hosted-Doktrin (`compliance/_INDEX.md`).
   Descope bleibt **Referenz-Vorbild** für das Zielmodell (deklarative Flows + ReBAC), nicht als
   Produkt.
2. **Der übernommene Kern ist Zanzibar-artige ReBAC/FGA als deklaratives Relations-Schema**, das
   das handgebaute `checkAccess`/`rbac-repo` aus ADR-0014 formalisiert bzw. ablöst — self-hosted,
   Open Source, in eigener EU-Infra.
3. **Beide Studios teilen sich denselben Stack.** Die Wahl gilt für ALUCA *und* den künftigen
   Meridian-SaaS-Pfad gemeinsam.
4. **Zwei gleichwertige Optionen** (bewusst ohne Empfehlung — Maintainer-Entscheid):

### Option A — next-auth + OpenFGA (minimaler Bruch)

- **AuthN:** `next-auth` / Auth.js bleibt (schon verdrahtet, MIT, self-host, Daten bei uns).
- **AuthZ:** **OpenFGA** self-hosted (Apache-2.0, CNCF, Postgres/MySQL/SQLite) ersetzt das
  handgebaute `checkAccess` durch ein deklaratives Autorisierungs-Modell — passt zum
  „Schema-First / JSON-SSOT"-Prinzip.
- **Kosten:** Software gratis; nur Betrieb (ein zusätzlicher Dienst + DB).
- **Preis:** AuthN bleibt am Auth.js-**Beta**-Pin; Enterprise-SSO/SAML pro Verbindung weiter
  Eigenarbeit. Zwei Bausteine (IdP + FGA) statt einem.

### Option B — Ory (voller EU-Stack, ein Anbieter)

- **AuthN + AuthZ aus einer Hand:** Ory Kratos (Identity) + Hydra (OAuth2/OIDC) + **Keto**
  (Zanzibar-ReBAC), optional Oathkeeper. **Deutscher Anbieter**, Apache-2.0, API-first/headless.
- **Vorteil:** Enterprise-SSO/SAML out-of-the-box; ein kohärentes Modell für beide Studios;
  stärkster DSGVO-Pitch (EU-Anbieter + self-host).
- **Preis:** größerer Umbau in ALUCA (next-auth → Kratos/Hydra); Microservice-Betrieb (mehrere
  Dienste).

**Verworfen bzw. mit Vorbehalt (nicht Teil der zwei Optionen):**

- **Zitadel** — technisch attraktiv (event-sourced, native Multi-Tenancy für B2B-SaaS), aber 2025
  von Apache-2.0 auf **AGPL-3.0** (Copyleft mit Netzwerk-Klausel) gewechselt. Für ein gehostetes
  SaaS meist tragbar, **aber Meridian liefert als Artefakt an den Kunden aus** — sobald
  Auth-Code in einem verteilten Artefakt landet, ist AGPL ein reales Lizenz-Thema. Deshalb bewusst
  nicht in den zwei Kern-Optionen; nur relevant, falls Meridian den ausgelieferten Modus aufgibt.
- **Keycloak** (Red Hat/IBM, Apache-2.0, feature-komplett, SAML/OIDC/LDAP) — valide, aber
  schwergewichtiger als für den Studio-Scope nötig; als Fallback dokumentiert, nicht als
  Kern-Option.
- **Descope selbst / managed Ory Network / Zitadel Cloud** — jede Managed-Variante bringt die
  Data-Residency-/Vendor-Frage zurück und ist damit durch Festlegung 1 ausgeschlossen (Kern-OSS
  darf jederzeit self-hosted bleiben).

## Entscheidungskriterium (das den Ausschlag gibt)

Nicht die Feature-Matrix, sondern in dieser Reihenfolge:

1. **DSGVO / EU-Hosting / Data-Residency** — muss vollständig self-hostbar in eigener EU-Infra
   laufen (`compliance/_INDEX.md`). Beide Optionen erfüllen das; jede Managed-Cloud fällt hier
   raus.
2. **Lizenz-Verteilbarkeit** — Apache/MIT bevorzugt, weil Meridian ausgeliefert wird (AGPL-Risiko,
   s. Zitadel).
3. **Umbau-Kosten in ALUCA jetzt** vs. **Ein-Stack-Kohärenz für beide Studios langfristig** — die
   eigentliche Abwägung A vs. B.
4. **Enterprise-SSO/SAML-Bedarf** — falls B2B-Mandanten das früh brauchen, verschiebt sich das
   Gewicht Richtung B (out-of-the-box) gegenüber A (pro Verbindung Eigenarbeit).

## Consequences

**Positiv**
- Der wertvolle Descope-Kern (deklaratives ReBAC) wird übernommen, ohne die Self-Hosted-/
  EU-Doktrin zu brechen — gratis, in eigener Infra.
- Formalisiert die in ADR-0014 benannte AuthZ-Lücke (`checkAccess` ohne Hierarchie) über ein
  Standardmodell statt weiterem Eigen-RBAC-Wachstum.
- Zwingt die Stack-Frage als **gemeinsame** Entscheidung für beide Studios — verhindert Auth-Drift
  zwischen ALUCA und einem künftigen Meridian-SaaS.

**Negativ / offen**
- Dieses ADR entscheidet **nicht** A vs. B — bis zur Ratifikation bleibt der Stack unbestimmt
  (bewusst, s. Status).
- Der Auth.js-Beta-Pin bleibt in Option A ein Endprodukt-Risiko, das dort separat adressiert werden
  muss.
- Migration des bestehenden `checkAccess`/`rbac-repo` auf ein FGA-Modell ist in beiden Optionen
  echte Arbeit (Relations-Schema modellieren, Tests, Datenmigration der `project_members`/
  `org_members`-Zeilen) — nicht Teil dieses ADR.

## Open decisions (an Maintainer-Ratifikation)

- **O-1 Stack-Wahl A vs. B.** Der Kern-Entscheid dieses ADR — bewusst offen gelassen, Maintainer.
- **O-2 Meridian-SaaS-Pfad.** Charter-Regel-5-Änderung („kein Backend/Login/SaaS jetzt") ist
  Voraussetzung, bevor Meridian den Stack überhaupt nutzt; als `D-XXX`-Stub in Meridian gespiegelt,
  nicht hier entschieden.
- **O-3 Enterprise-SSO/SAML-Zeitpunkt.** Ob/wann B2B-Mandanten SAML brauchen — verschiebt das
  Gewicht A↔B; ohne realen Kundenkontext bewusst nicht geraten (dieselbe DoD-Fehlerfall-Klausel wie
  ADR-0009/0014).
- **O-4 Auth.js-Beta-Ausstieg** (nur relevant bei Option A) — auf stabiles v5 warten vs. IdP-Wechsel.

## External sources (Abrufdatum 2026-07-15)

- Zanzibar-OSS-Implementierungen (OpenFGA/SpiceDB/Keto, Lizenzen): pkgpulse.com „OpenFGA vs Permify
  vs SpiceDB (2026)"; authzed.com „Alternatives to OpenFGA"; osohq.com „OpenFGA Alternatives".
- IdP-Vergleich + Lizenz-/Herkunfts-Stände (Keycloak/Zitadel/Authentik/Ory, Zitadel-AGPL-Wechsel
  2025): startwithidentity.com „Top 10 Open-Source IAM 2026"; skycloak.io „Open Source
  Authentication 2026"; wz-it.com „Authentik vs. Zitadel 2026"; houseoffoss.com „Keycloak vs
  Authentik vs Zitadel (2026)".
- Descope-Referenzmodell (Flows/Screens, FGA/ReBAC, UI-Integration): docs.descope.com/flows,
  docs.descope.com/authorization/rebac, descope.com/blog/post/ui-integration.

## References

- Intern: [`0014-org-layer-over-local-first.md`](0014-org-layer-over-local-first.md),
  [`0007-studio-generate-docks-onto-superversion-core.md`](0007-studio-generate-docks-onto-superversion-core.md),
  `../../studio/src/lib/auth/config.ts`, `../../studio/src/lib/auth/require-role.ts`,
  `../../studio/src/lib/auth/session.ts`, `../../studio/src/lib/db/rbac-repo.ts`,
  `../../studio/src/lib/auth/org-membership-lookup.ts`, `../../studio/package.json`,
  `../../compliance/_INDEX.md`.
- Cross-Repo: Freelancing/Meridian `meridian/studio/DECISIONS.md` (gespiegelter SaaS-Auth-Adapter-
  Decision-Stub, O-2).
