---
last-reviewed: 2026-07-15
shelf-life-days: 90
---
# Auth-Stack — Datenschutz, Data-Residency & AVV (Option A: next-auth + OpenFGA)

> **Zweck:** DSGVO/EU-Hosting-Gate **vor** der Umsetzung des in
> [`../docs/architecture/adr/0016-authn-authz-stack-for-the-studios.md`](../docs/architecture/adr/0016-authn-authz-stack-for-the-studios.md)
> gewählten **Option-A-Stacks** (next-auth für AuthN + self-hosted OpenFGA für AuthZ).
> Erfüllt **Backlog-T1** (`../docs/architecture/research/authn-authz-stack-build-backlog.md`).
> Dies ist ein **eigener Verarbeitungskontext** — der Betrieb des ActionReady Studio als
> SaaS (Nutzer-Login), **nicht** das analytische Kunden-Deliverable. Es **ergänzt** die
> bestehenden Legal-Docs für diesen neuen Kontext, statt sie zu duplizieren:
> `DPIA.md` (PII-Klassifikation), `eu_hosting_guarantee.md` (Region/Subprozessoren),
> `data_processing_record.md` (Art. 30), `retention_policy.md`.
>
> `⚠️ TO BE COMPLETED BY LEGAL`-Punkte sind rechtliche Festlegungen — der Agent liefert
> die **technischen Fakten**, die Rechtsabteilung die **rechtliche Würdigung**.

## 1. Scope & Grundsatzentscheidung

Aus ADR-0016 (Festlegung 1): **keine Managed-CIAM-Cloud** (Descope & Co.) im Auth-Pfad.
Beide Komponenten sind **Software, die wir selbst betreiben**, kein Dienst, an den Daten
abfließen:

- **next-auth / Auth.js** — Bibliothek, läuft **in-process** im Next.js-Server. Kein
  Datenabfluss an einen Vendor.
- **OpenFGA** — **self-hosted** Dienst (eigener Container + DB), Apache-2.0. Kein
  Datenabfluss an einen Vendor.

## 2. PII-Inventar des Auth-Stacks (Ist-Stand, belegt aus dem Code)

| Datum | Quelle | Kategorie | Zweck | Wo gespeichert |
|---|---|---|---|---|
| E-Mail-Adresse | `studio/src/lib/db/sqlite.ts` `users.email` (UNIQUE, NOT NULL) | direkter Identifikator | Login-Identität, Nutzer-Auflösung | App-DB (SQLite/Host-DB) |
| Anzeigename | `users.name` (NOT NULL; Default = E-Mail-Local-Part) | Personenbezug | UI-Anzeige | App-DB |
| Pseudonyme User-ID `usr-…` | `user-repo.ts` `findOrCreateUser` | Pseudonym | interner Schlüssel überall sonst | App-DB |
| Anlage-Zeitstempel | `users.created_at` | Metadatum | Audit/Onboarding | App-DB |
| Session | `studio/src/lib/auth/session.ts` — **JWT im Cookie** (`id`/`email`/`name`) | Auth-Token | Sitzungsführung | **nur Client-Cookie**, kein Server-Session-Store |
| Rollen-/Mitgliedschafts-Beziehungen | `project_members`/`org_members` bzw. **OpenFGA-Relation-Tuples** | Zugriffs-Metadaten | Autorisierung | App-DB bzw. OpenFGA-DB |

**Data-Minimization-Befund (wichtig):** **OpenFGA speichert ausschließlich die pseudonyme
`usr-…`-ID** in den Relation-Tuples (`user:usr-… relation object:project-…`) — **keine
E-Mail, keinen Namen.** Der einzige direkte Identifikator (E-Mail) lebt nur in **einer**
Tabelle (`users`). Das ist die datensparsamste sinnvolle Aufteilung und sollte im
ReBAC-Schema (Backlog T2) so erhalten bleiben.

## 3. Data-Residency & Self-Hosting-Topologie (T1.1)

**Feststellung: Der Auth-Pfad ist bei Option A zu 100 % self-hosted betreibbar; es gibt
keinen zwingenden externen Managed-Call.** Alle drei datenführenden Bausteine laufen in
**eigener EU-Infrastruktur**:

1. Next.js-Server (next-auth in-process),
2. App-DB (`users`, `*_members`),
3. OpenFGA-Dienst + dessen DB.

→ Deploybar in einer EU-Region (z. B. Hetzner/IONOS/OVH DE-EU, oder EU-Region eines
Hyperscalers). Damit ist die EU-Hosting-Zusicherung (`eu_hosting_guarantee.md`) für den
Auth-Kontext strukturell erfüllbar — **keine Drittlandübermittlung** im Standardpfad.

**Ehrlicher Vorbehalt — der einzige Weg, wie ein Drittland/Prozessor doch entsteht:**
Wird ein **externer Social-/OAuth-IdP** (z. B. Google/Microsoft-Login) als next-auth-Provider
konfiguriert, verlässt der Auth-Handshake die EU-Infra und dieser IdP wird Empfänger/ggf.
Drittland. **Der DSGVO-saubere Standardpfad ist daher: E-Mail-/Passwortlos-Login ohne
externen Social-IdP** (oder später ein self-hosted IdP bei Option B). Diese Festlegung
gehört als bewusste Konfig-Vorgabe in die Umsetzung (Backlog T5).

## 4. AVV/DPA-Bedarf (T1.2)

| Beteiligter | Prozessor i. S. v. Art. 28? | AVV nötig? |
|---|---|---|
| **next-auth / Auth.js** (Bibliothek, in-process) | **Nein** — reine Software, kein Datenempfänger | nein |
| **OpenFGA** (self-hosted Dienst) | **Nein** — self-hosted, kein Datenempfänger | nein |
| **Hosting-Provider** (betreibt Server + DB + OpenFGA) | **Ja** — verarbeitet die Daten in unserem Auftrag | **Ja — AVV mit EU-Host** (`AVV_Template.md`, EU-Region) |
| **Externer OAuth-IdP** *(nur falls konfiguriert, s. §3)* | **Ja** — Empfänger der Login-Daten | Ja + ggf. Art.-44-Transfer — **im Standardpfad vermeiden** |

**Kernaussage:** Für die **Auth-Software selbst ist kein AVV nötig, weil self-hosted.**
Der einzige AVV-pflichtige Beteiligte ist der **Hosting-Provider** — der wird ohnehin für
den gesamten Studio-Betrieb gebraucht (nicht auth-spezifisch). Kein *zusätzlicher*
Auth-Vendor-AVV entsteht durch Option A.

## 5. Art.-30-Verarbeitungstätigkeit (Entwurf → in `data_processing_record.md` übernehmen)

| Feld | Wert (Entwurf) |
|---|---|
| Tätigkeit | Studio-Nutzerverwaltung & Zugriffskontrolle (AuthN/AuthZ) |
| Zweck | Zugangskontrolle + Betrieb der SaaS |
| Betroffene | Studio-Nutzer (Berater/Kundenmitarbeiter) |
| Datenkategorien | E-Mail, Anzeigename, pseudonyme ID, Rollen/Mitgliedschaften, Login-Zeitstempel |
| Rechtsgrundlage | `⚠️ LEGAL`: Art. 6(1)(b) Vertragserfüllung (SaaS-Nutzung) und/oder (f) berechtigtes Interesse (Zugangssicherheit) |
| Empfänger | keine (self-hosted); nur Hosting-Provider als Auftragsverarbeiter |
| Drittland | keines im Standardpfad (s. §3-Vorbehalt) |
| Löschung | `⚠️ LEGAL` + `retention_policy.md`: Nutzerdaten bei Account-Kündigung löschen; OpenFGA-Tuples des Nutzers mitentfernen |
| TOMs | EU-self-hosted, Transportverschlüsselung, JWT-Cookie `HttpOnly`/`Secure`, Zugriff via RBAC/ReBAC |

## 6. Ergebnis des Gates

✅ **T1 grün — die Umsetzung von Option A ist compliance-seitig freigegeben**, unter drei
verbindlichen Auflagen für die Bauphase:
1. **Standardpfad ohne externen Social-IdP** (E-Mail/Passwortlos) — sonst Drittland-Prüfung (§3).
2. **AVV mit EU-Hosting-Provider** liegt vor (nicht auth-spezifisch, aber Voraussetzung) (§4).
3. **OpenFGA hält nur pseudonyme IDs** — Data-Minimization im ReBAC-Schema (T2) wahren (§2).

## 7. Offene Punkte (an Legal / spätere Tasks)

- `⚠️ LEGAL`: finale Rechtsgrundlage Art. 6 (b vs. f) für die Nutzer-Verarbeitung festlegen.
- `⚠️ LEGAL`: Art.-30-Zeile (§5) in `data_processing_record.md` übernehmen und AVV mit dem
  konkreten Host abschließen (`AVV_Template.md`).
- **T5 (2026-07-15, Weg C umgesetzt):** Der Default-Pfad ist **verifiziert social-IdP-frei** — `auth/config.ts` verdrahtet GitHub nur bei gesetzten `GITHUB_ID/SECRET` (opt-in), der Demo-Credentials-Login ist dev-only. Policy als Code-Kommentar + `.env.example` festgehalten. **Ehrliche offene Lücke:** Produktion hat **noch keine eingebaute compliance-konforme Login-Methode** — heute wäre der einzige Prod-Login GitHub (Social-IdP, freizugeben) oder keiner. Die passwortlose **Magic-Link-Methode (T5-Ziel A)** ist der geplante Prod-Default und **aufgeschoben**, blockiert auf die Wahl eines **EU-E-Mail-Providers** (SMTP/Resend, DSGVO-konform). Ein Prod-Deploy ist erst nach A (oder einem freigegebenen IdP) zulässig.
- **Bauphase (T4/Retention):** Nutzer-Löschung muss die OpenFGA-Relation-Tuples des Nutzers mitlöschen (kein verwaistes AuthZ-Datum).
