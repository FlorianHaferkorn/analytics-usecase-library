# Geteilte Substanz vs. eigene IP — die Grenze zwischen Meridian/Freelancing und ALUCA

> **Status:** Doktrin · 2026-07-28 · liegt in **beiden** Repos unter demselben Pfad
> (`SHARED_SUBSTANCE.md`) mit **byte-identischem** Inhalt — prüfbar per Hash-Vergleich,
> deshalb ohne repo-spezifische Formulierung geschrieben.
> **Auftrag (Zitat):** „Ich will fast zwei identische Ansätze mit ihren eigenen kleinen
> Eigenheiten (Design, Zielkunden etc.)." — mit der Grenze: „**Was unterschiedlich
> bleiben muss ist die IP an sich. Common-Sense-Ansätze basierend auf offiziellen
> Quellen und Recherchen kann geteilt werden.**"
> **Vorgänger:** `SYNERGY_ALUCA_MERIDIAN.md` beschreibt den *Funktionsvergleich*.
> Dieses Dokument beantwortet die daraus offene Frage: **was davon darf rüber.**

---

## 1. Der Test (mechanisch, nicht nach Gefühl)

Für jedes Asset genau eine Frage:

> **Kann ich auf eine offizielle oder öffentliche Quelle zeigen, die dieses Asset
> im Kern nur *kodiert*?** (MS-Learn-Seite, REST-API-Referenz, ODCS-Spec, ein
> publizierter Standard, eine belegte Recherche.)

- **Ja** → **Klasse A · geteilte Substanz.** Der Wert liegt darin, dass es *korrekt*
  und *deterministisch* ist, nicht darin, dass *wir* es erfunden haben. Beide Repos
  bekommen es, byte-identisch, mit Paritäts-Sensor.
- **Nein — der Wert kommt aus eigener Markt-, Kunden- oder Framework-Wertung** →
  **Klasse B · eigene IP.** Bleibt wo es ist. Wird nie portiert.
- **Gleiche Fähigkeit, andere Ausprägung** (Benennung, Sprache, Design-Tokens,
  Zielkunde, CLI-Oberfläche) → **Klasse C · Eigenheit.** Bewusst in beiden Repos,
  bewusst verschieden.

Der Test ist absichtlich hart: Wenn niemand eine Quelle nennen kann, ist es keine
geteilte Substanz — auch wenn es sich „allgemein" anfühlt.

### Warum diese Grenze und keine andere

Eine falsche Payload-Form gegen die Fabric-REST-API ist in beiden Repos gleich
falsch. Die Korrektheit gehört keinem von beiden — sie gehört Microsoft. Sie zweimal
zu pflegen erzeugt nur zwei Stände, von denen einer still veraltet (genau der Fall,
der uns beim `domain`-Feld im Ingestion-IR passiert ist: Meridian gefixt, ALUCA
driftete, weil Parität nur repo-intern geprüft wurde).

Umgekehrt: Der Golden Thread, der KPI-Katalog, die Use-Case-Bracket, die
Zielkunden-Zuschnitte, das Design-System, die DOCX-Deliverables — dort liegt der
Grund, warum jemand das eine oder das andere kauft. Das zu vereinheitlichen würde
den Unterschied einebnen, den der Auftrag ausdrücklich erhalten will.

---

## 2. Klassifikation des tatsächlichen Bestands

Erhoben durch Datei-für-Datei-Vergleich beider Repos (nicht aus READMEs).

### 2.1 Klasse A — geteilte Substanz (gehört in beide Repos)

| Asset | Heimat heute | Offizielle Quelle, die es kodiert |
|---|---|---|
| `dataarch_engine/blueprint/provision_governance.py` — OneLake-Security-Rollen | Meridian | `PUT /v1/workspaces/{ws}/items/{id}/dataAccessRoles`; `DecisionRule.permission` = exakt zwei `PermissionScope` (Path + Action); UNION-Semantik der Rollen |
| `provision_monitoring.py` — Workspace-Failure-KQL + Kapazitäts-Throttling | Meridian | `ItemJobEventLogs`-Schema; Activator `backgroundRejectionThresholdPercentage` |
| `provision_lifecycle.py` — OPTIMIZE/VACUUM + BCDR-Runbook | Meridian | Delta-Lake-Wartung in Fabric; DR-Toggle-Grenzen |
| `provision_connectivity.py` — Managed Private Endpoints | Meridian | `POST /v1/workspaces/{ws}/managedPrivateEndpoints` |
| `provision_operability.py` — Metadaten-Vollständigkeit als Funktionsbedingung | Meridian | Data-Agent-DAX-Generierung nutzt ausschließlich Modell-Metadaten; ≤25 Tabellen/Quelle |
| `capacity_recommend.py` — SKU-Guardrails inkl. Direct Lake | Meridian | Per-SKU-Guardrails (`dl_mem_gb`, `rows_m`, `dq_conn`) |
| `admin_settings.py` — Tenant-Settings-Vorbedingungen | Meridian | Fabric-Admin-Portal-Tenant-Settings |
| `decision_proposals.py` — RLS/CLS/Retention/Endorsement-Vorbelegungen | Meridian | Jede Vorbelegung trägt ihre Quelle im Kommentar; die Heuristik selbst ist begründet, nicht geraten |
| `concepts.py` / `governance_concepts.py` / `odcs.py` — Konzept-Registries | beide (bereits gespiegelt) | ODCS-Spec; Medallion/Data-Vault als publizierte Muster |
| `architecture_blueprint.schema.json` + IR-Spec | beide (bereits gespiegelt) | eigenes Schema, aber Feld-für-Feld gegen offizielle Constraints belegt |
| `products/fabric/orchestrator/orchestrator.py` — MSAL + Fabric REST, idempotent, dry-run | ALUCA | Fabric-REST-v1-Referenz; MSAL Client-Credentials |
| `deployment/scripts/fabric_release.py` u. a. — fabric-cicd-Vollzug | ALUCA | `fabric-cicd`-Bibliothek (offiziell, Microsoft) |
| Sensitivity-Label-/Endorsement-Vollzug | ALUCA (heute defekt, s. §4) | Power-BI-Admin-API `informationprotection/setLabels`; Endorsement hat **keine** dokumentierte Write-API |

**Kern der Klasse A in einem Satz:** Meridian *kompiliert* die Architektur, ALUCA
*führt sie aus*. Beide Hälften sind reine Kodierung offizieller Verträge — und
deshalb gehören **beide Hälften in beide Repos**.

### 2.2 Klasse B — eigene IP (bleibt, wo sie ist)

| Asset | Repo | Warum nicht teilbar |
|---|---|---|
| `Strategie/`, `Kunden/`, `INTAKE.md` | Meridian | Markt-, Positionierungs- und Kundenwertung |
| `Brand/…Design System/`, `core/docx_branding.py`, DOCX-Generatoren | Meridian | Eigene Marke und Deliverable-Sprache |
| `named_profiles.py`, `profile_emission.py`, Blueprints 1–4 | Meridian | Eigene Produktisierung des Zielkunden-Zuschnitts |
| `sap_ontology/-standard_pack/-tmdl/-data_agent` | Meridian | Eigener SAP-Produktpack (die *Connector-Matrix* darin ist Klasse A, die Paketierung nicht) |
| `core/kpi_catalog/`, `core/action_codes/`, `core/usecases/`, `golden_20.yaml` | ALUCA | Golden Thread — das verkaufte Bedeutungsmodell |
| Use-Case-Bracket 3-30-300, Value-Driver | ALUCA | Eigene UX-/Wirkungs-Doktrin |
| `studio/` | ALUCA | Eigenes Produkt-Frontend |
| `compliance/` (DPIA/AVV/Art.-30) | ALUCA | Auf den DE-Beschaffungsmarkt zugeschnittene Ausarbeitung |

### 2.3 Klasse C — bewusste Eigenheiten (beide Repos, verschieden)

Benennung und Ordnerlayout (`core/dataarch_engine/` vs. `tooling/superversion/`),
Dokumentationssprache und -ton, Design-Tokens, CLI-Oberfläche, Zielkunden-Defaults,
Navigations-/Index-Doktrin. Diese Unterschiede werden **nicht** eingeebnet — sie
sind der Grund, warum es zwei Repos gibt und nicht eins.

---

## 3. Mechanismus — wie Klasse A ehrlich bleibt

Kein neuer Apparat. Es gibt bereits zwei etablierte Verfahren im Haus, und Klasse A
nutzt genau die (Tool-Reuse-Pflicht):

1. **Vendoring mit Integritäts-Manifest** — der Empfänger legt die Dateien unter
   einem `vendor/`-Teilbaum ab, dazu `PIN.json` mit sha256 je Datei. Lokale
   Abweichung schlägt beim Laden fehl (`VendorUnavailable`), statt still zu driften.
   Vorbild: `tooling/superversion/vendor/meridian` + `_meridian_vendor.py` (ALUCA).
2. **Drift-Sensor über die Vertragsfläche** — `check_dataarch_mirror.py` vergleicht
   die *öffentlichen* Zusagen beider Seiten und meldet Abweichung. Doktrin
   unverändert: **meldet Drift, bumpt nie.** Advisory (Exit 0), `--strict` im
   Release-Gate.

**Richtung:** Klasse A hat pro Asset genau **eine Quelle der Wahrheit** — das Repo,
in dem es entstanden ist (Spalte „Heimat heute"). Das andere Repo spiegelt.
Änderungen gehen immer zuerst in die Heimat, dann in den Spiegel. Zwei
gleichberechtigte Stände sind ausdrücklich nicht das Ziel — das war der Zustand,
der die Drift erzeugt hat.

**Grenze zur Kundenlaufzeit** (unverändert aus dem Official-First-Prinzip): Geteilt
wird die eigene Entwicklungs-/CI-Pipeline. Deliverables beim Kunden bleiben
tool-freie Dateien (JSON/TMDL/PBIR/DOCX).

---

## 4. Was diese Doktrin sofort auslöst

Aus der Klassifikation folgen konkrete, belegte Arbeitspakete:

1. **ALUCA-Vollzug hat zwei harte Defekte** (beide Klasse A, beide von der
   offiziellen Quelle widerlegt — Details und Fixes in den jeweiligen Modulen):
   - `POST workspaces/{ws}/governanceLabels` existiert nicht. Sensitivity Labels
     laufen über die Power-BI-**Admin**-API `informationprotection/setLabels`,
     artefakt- statt workspace-bezogen, `Tenant.ReadWrite.All`, 25 Requests/Stunde,
     2000 Artefakte pro Request. Für **Endorsement** gibt es *keine* dokumentierte
     Write-API — der ehrliche Weg ist ein ausgewiesener manueller Schritt, kein
     erfundener Endpunkt.
   - `deploy.ps1` ruft `fabric_release.py` mit `--workspace_id`, `--domain_filter`
     und `--dry_run` auf; keines davon kennt dessen `argparse` → Exit 2. Zusätzlich
     setzt `deploy.ps1` `AZURE_*`-Credentials, während `fabric_release.py`
     `TENANT_ID`/`CLIENT_ID`/`CLIENT_SECRET` liest.
2. **Meridian fehlt die Vollzugshälfte** — der Orchestrator ist Klasse A und gehört
   auch nach Meridian.
3. **ALUCA fehlt die Kompilierhälfte** — die offiziell belegten Emitter aus §2.1
   gehören auch nach ALUCA.

---

## 5. Für neue Arbeit

Vor jedem neuen Modul, jeder neuen Regel, jedem neuen Emitter: **erst klassifizieren.**

- Klasse A → in der Heimat bauen, Spiegel im selben Arbeitsschritt nachziehen,
  Sensor grün halten. Nicht „später spiegeln" — genau daraus entsteht Drift.
- Klasse B → im eigenen Repo bauen, nicht anbieten.
- Klasse C → in beiden bauen, bewusst unterschiedlich, ohne Paritätsanspruch.

Wer eine Klasse-A-Zusage ändert, ohne den Spiegel nachzuziehen, hinterlässt genau
den Zustand, den dieses Dokument abschafft.
