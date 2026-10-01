# ADR-0022 — AuthN/AuthZ-Stack für die Studios: Better Auth, Kunden-Entra-ID, ReBAC bei Bedarf

| Feld | Wert |
|---|---|
| Status | **Proposed** (01.10.2026) |
| Entscheider | Florian Haferkorn |
| Kontext | Flo, 01.10.2026: „aktuell nicht, aber es sollte künftig mehrere Rollen geben, die darauf zugreifen“; Frage, ob die Juli-Entscheidung noch die beste Lösung ist |
| Schreibt fort | ADR-0016-Entwurf „AuthN/AuthZ-Stack für die Studios“ (PR #401, am 15.07.2026 als Option A akzeptiert, **nie gemergt**; Stand im Archiv-Branch `archive/verwaiste-branches-2026-10-01`, Commit `4a538af5`). Die Nummer 0016 trägt in `main` heute ein anderes ADR. |
| Betrifft | `studio/src/lib/auth/config.ts` · `studio/src/lib/auth/require-role.ts` · `studio/src/lib/db/rbac-repo.ts` · `studio/src/lib/auth/rbac-types.ts` · `studio/package.json` |
| Bezug | ADR-0014 (Org-Schicht über lokal-first) · ADR-0007 (lokal-first/BYOK) · `../../compliance/_INDEX.md` (EU-Hosting, AVV) · Meridian Charter §3.2 (SaaS-Pfad offen) und §3.3 (kein Login, kein Backend) · Meridian-Spiegel D-623 |

## 1. Kontext

**Bedarf.** Heute gibt es keinen Kundenbedarf für Mehrbenutzer-Login. Künftig sollen mehrere
Rollen auf die Studios zugreifen (Florian, 01.10.2026). Diese ADR legt den Stack fest, damit die
Umsetzung beim ersten Anlass ohne neue Grundsatzdebatte beginnen kann; sie löst selbst keinen Bau aus.

**Ist-Zustand ALUCA** (gelesen 01.10.2026 in `main`):

- AuthN: `next-auth` `^5.0.0-beta.30` mit den Providern GitHub und Credentials (`config.ts`).
- AuthZ: handgebautes RBAC. Projektrollen `admin`/`editor`/`viewer` mit Hierarchie
  (`rbac-types.ts`), Org-Rollen `owner`/`admin`/`member` mit konservativem Fallback (ADR-0014),
  Prüfung über `checkAccess` (`rbac-repo.ts`).

**Ist-Zustand Meridian:** Single-File-HTML ohne Backend und Login (Charter §3.3). Betroffen ist nur
der spätere SaaS-Pfad; beide Studios sollen dann denselben Stack nutzen.

**Was sich seit Juli 2026 geändert hat** (je zwei Belege, erhoben 01.10.2026; „npm“ = eigene Messung im npm-Register):

| Befund | Quelle 1 | Quelle 2 |
|---|---|---|
| Auth.js v5 ist seit September 2025 im Wartungsmodus (nur Sicherheitspatches), gepflegt vom Better-Auth-Team, das für neue Projekte Better Auth empfiehlt | [next-auth Discussion #13252](https://github.com/nextauthjs/next-auth/discussions/13252) | [LogRocket, 2026](https://blog.logrocket.com/best-auth-library-nextjs-2026/) |
| next-auth v5 ist nie stabil erschienen: `latest` = 4.24.15, `beta` = 5.0.0-beta.32 (veröffentlicht 20.07.2026) | npm: `npm view next-auth dist-tags` | [LogRocket, 2026](https://blog.logrocket.com/best-auth-library-nextjs-2026/) |
| Vercel hat Better Auth am 07.07.2026 übernommen; Lizenz bleibt MIT, Bibliothek bleibt Open Source | [Vercel-Blog](https://vercel.com/blog/vercel-acquires-better-auth) | [WeeTracker, 09.07.2026](https://weetracker.com/2026/07/09/better-auth-acquired-vercel-ethiopian-startup/) |
| OpenFGA ist seit 28.10.2025 CNCF-Incubating | [CNCF-Blog](https://www.cncf.io/blog/2025/11/11/openfga-becomes-a-cncf-incubating-project/) | [openfga.dev/project](https://openfga.dev/project) |
| Better Auth hatte 2026 viele Sicherheitsmeldungen: 1.6.10 trägt 9 GitHub-Advisories (1 critical, 7 high, 1 low; Fixes bis 1.6.22), die aktuelle 1.7.7 keine; Lizenz MIT | npm: `npm audit` gegen `better-auth@1.6.10` bzw. `@1.7.7`, `npm view better-auth license` | GitHub Advisory Database (z. B. [GHSA-qq9h-g4jm-xgf3](https://github.com/advisories/GHSA-qq9h-g4jm-xgf3)) |

Nur einfach belegt (ANNAHME, ungeprueft): CVE-2026-53515, Authentifizierungsumgehung im SSO-Plugin
1.2.10–1.6.10 ([SentinelOne](https://www.sentinelone.com/vulnerability-database/cve-2026-53515/)); im
`npm audit` des Kernpakets nicht enthalten, vermutlich im Paket `@better-auth/sso`.

Folge für die Juli-Entscheidung: Der Rahmen (keine Managed-US-CIAM-Cloud, self-hosted, ein Stack für
beide Studios) trägt weiter. Die AuthN-Hälfte von Option A (Auth.js) nicht: Eine Beta im
Wartungsmodus widerspricht dem Endprodukt-Anspruch (Meridian Charter §3.3, D-155).

## 2. Entscheidung (vorgeschlagen)

1. **Rahmen unverändert aus dem Juli-Entwurf:** keine Managed-CIAM-Cloud als Laufzeit-Abhängigkeit,
   alles self-hosted in EU-Infrastruktur, Daten in eigener Datenbank, ein Stack für ALUCA und den
   künftigen Meridian-SaaS-Pfad.
2. **AuthN: Better Auth statt Auth.js.** Bibliothek im eigenen Prozess (MIT), Sitzungen in der eigenen
   Datenbank, Organisationen, Teams und Rollen als offizielles Plugin. Versionen exakt gepinnt und
   `npm audit` ohne offene Advisories als Tor (die Meldungsdichte 2026 macht das zur Pflicht, nicht zur Kür).
3. **Anmeldung beim Kunden über dessen eigenen Identity-Provider (OIDC), Microsoft Entra ID zuerst.**
   Kein eigener Identity-Provider im Betrieb; der Kunde verwaltet Konten, MFA und Austritte selbst.
   SAML nur, wenn ein Kunde kein OIDC anbietet.
4. **AuthZ in Stufen:**
   - **Stufe 1 (beim ersten Mehrbenutzer-Anlass):** die vorhandenen Rollen bleiben das Modell
     (`ProjectRole`, `OrgRole`), gespeichert über die Rollen der Better-Auth-Organisation;
     `checkAccess` bleibt die eine Prüfstelle.
   - **Stufe 2 (nur bei Auslöser, s. u.):** OpenFGA (Zanzibar-ReBAC, CNCF) ersetzt `checkAccess`.
5. **Ory** (Kratos/Hydra/Keto) bleibt aufgeschoben wie im Juli; **Keycloak** bleibt Rückfallebene,
   falls ein Kunde einen eigenen Identity-Provider von uns betrieben haben will.

### Auslöser (maschinenlesbar, je Zeile ein prüfbares Ereignis)

| ID | Auslöser | Folge |
|---|---|---|
| T-1 | Erster Kunde oder erstes internes Team braucht mehr als einen Login je Studio-Instanz | Stufe 1 umsetzen (Better Auth + Kunden-OIDC) |
| T-2 | Rechte hängen an Beziehungen statt an Rollen (z. B. Freigabe eines Projekts an Nutzer einer anderen Org, Vererbung Ordner → Report) | Stufe 2 (OpenFGA) prüfen |
| T-3 | Kunde verlangt SAML oder einen von uns betriebenen Identity-Provider | Keycloak bzw. Ory neu bewerten |
| T-4 | Better Auth ändert Lizenz oder Selbsthostbarkeit | ADR neu öffnen |

## 3. Optionen erwogen

| Option | Bewertung |
|---|---|
| **A' Better Auth + Kunden-OIDC, OpenFGA bei Bedarf** (gewählt) | ein Dienst weniger als A, kein Beta-Pin, Login mit dem Microsoft-Konto des Kunden |
| A Auth.js + OpenFGA (Juli 2026) | AuthN im Wartungsmodus und nie stabil; OpenFGA sofort wäre Betrieb ohne Bedarf |
| B Ory (Kratos/Hydra/Keto) | vollständig, EU-Anbieter, aber mehrere Dienste und größerer Umbau ohne heutigen Bedarf |
| Keycloak | ausgereift, SAML/LDAP, aber ein eigener schwerer Dienst; Rückfallebene für T-3 |
| Zitadel | AGPL-3.0 seit 2025; heikel, sobald Auth-Code in ausgelieferte Artefakte gelangt |
| Managed Cloud (Descope, Clerk, Auth0) | widerspricht dem Rahmen (Data-Residency, Vendor-Lock-in) |

## 4. Folgen

- Kein Code jetzt. Bei T-1: Migration `next-auth` → Better Auth in `studio/src/lib/auth/`, Rollen-Mapping
  auf die Organisation, Tests `auth-session`, `rbac-repo`, `org-rbac` nachziehen.
- Abhängigkeit von Vercel als Träger: Die Bibliothek läuft vollständig bei uns; ein Wechsel des Trägers
  ändert den Betrieb nicht, wohl aber die Pflege. Beobachtet über T-4.
- Meridian bleibt ohne Login, bis der SaaS-Pfad entschieden ist (Spiegel-Eintrag D-623).

## 5. Offene Punkte

- O-1: Welche Rollen konkret? Heute fachlich offen; Startpunkt sind die vorhandenen drei Projekt- und
  drei Org-Rollen.
- O-2: Betrieb der Datenbank für Sitzungen und Organisationen (SQLite lokal vs. Postgres beim Kunden).
- O-3: Ratifizierung dieser ADR (Status Proposed).
