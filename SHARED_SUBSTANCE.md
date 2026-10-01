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
> **Fortgeschrieben 30.09.2026 (Owner-Entscheidung E3):** Klasse B darf zwischen Meridian
> und ALUCA geteilt werden, wenn es die Qualität hebt — Heimat eindeutig, Spiegel mit PIN
> und Sensor. Die alte Regel „nie portiert" steht in §1, §2.2 und §5 als abgelöst markiert.
> **Fortgeschrieben 30.09.2026 (Visual-Stack, Meridian D-620, ALUCA A-31):** Visual Library,
> Auswahllogik Frage → Form, Farbsemantik/Kontrast und Markenableitung sind Klasse A mit je
> einer Heimat (§2.1). Bei Design-Tokens ist die Logik Klasse A, die Werte bleiben Klasse C (§2.3).

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
  **Klasse B · eigene IP.** Bleibt wo es ist. ~~Wird nie portiert.~~ *(abgelöst am
  30.09.2026: Teilen erlaubt, wenn es die Qualität hebt — Regel in §2.2)*
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
| `products/fabric/orchestrator/sandbox.py` — Sandbox-Lebenszyklus je Lauf (Workspace anlegen, deployen, löschen mit Rücklese-Guard und 404-Nachweis) | ALUCA (E4, 24.09.2026) | `POST`/`GET`/`DELETE /v1/workspaces`; Deploy über `fabric_release.py` (`fabric-cicd`). Baut auf `orchestrator.py` statt einen zweiten Fabric-Client zu führen |
| Visual Library: Idiome, Notationsprofile, Anti-Patterns, Realisierung je Ziel (PBIR, Deneb, Recharts, SVG-DAX, HTML, Fabric App) | ALUCA (30.09.2026) | Chart-Taxonomien (Munzner, FT Visual Vocabulary), IBCS Standards / ISO 24896, PBIR-/Vega-Lite-/Fabric-Visuals-Schemas. Die Engine (Emission, Validierung) bleibt davon getrennt |
| Auswahllogik Frage → purpose → Idiom (`index.yaml`, `resolve.py`) | ALUCA (30.09.2026) | Munzner „why before how“, FT Visual Vocabulary; Deny-Liste mit Quelle je Eintrag |
| Zonen-Vokabular der Page Templates: Zonen-Aufgabe (`task_taxonomy`) und Informationsblock → purpose (`index.yaml` `zone_vocabulary`, `resolve.choose_for_zone`) | ALUCA (30.09.2026, R5) | Munzner-Aufgabentaxonomie (2014); die Zweck-Liste ist die der Auswahllogik |
| Farbsemantik, IBCS-Szenariofarben, Kontrast- und Farbfehlsicht-Prüfung | ALUCA (30.09.2026) | WCAG 2.2 (1.4.3, 1.4.11), Machado-Simulation, CIEDE2000 |
| Markenableitung: Marken-Token-Schema → PBI-Theme, CSS-Variablen, Fabric-App-Theme | Meridian (30.09.2026) | Power-BI-Theme-Schema, DTCG 2025.10, Fabric-Apps-Theming (`useCssTheme`) |
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

**Regel bis 29.09.2026 — abgelöst am 30.09.2026:** Klasse B bleibt, wo sie ist, und wird
nie portiert.

**Regel ab 30.09.2026 (Owner-Entscheidung E3):** Wissen aus Klasse B darf zwischen Meridian
und ALUCA geteilt werden, wenn es die Qualität des anderen Repos hebt. Drei Bedingungen:

1. **Heimat eindeutig.** Jeder Baustein hat genau eine Quelle der Wahrheit — die Spalte
   „Repo" oben. Teilen gibt ihm keine zweite Heimat; Änderungen gehen zuerst in die Heimat.
2. **Spiegel mit PIN.** Geteilt wird per Spiegel nach §3 (Vendor-Teilbaum mit `PIN.json`,
   sha256 je Datei), nicht per Kopie ohne Pin.
3. **Sensor.** Jeder Spiegel hat einen Drift-Sensor mit den drei Ausgängen aus §3.

Die Spalte „Warum nicht teilbar" bleibt als Begründung der Herkunft stehen: sie sagt, wo
der Wert entstanden ist, nicht mehr, dass er das Repo nie verlässt.

### 2.3 Klasse C — bewusste Eigenheiten (beide Repos, verschieden)

Benennung und Ordnerlayout (`core/dataarch_engine/` vs. `tooling/superversion/`),
Dokumentationssprache und -ton, Design-Token-**Werte** (eigene Marke, Kunden-Tokens),
CLI-Oberfläche, Zielkunden-Defaults, Navigations-/Index-Doktrin, Page-Template-**Dateien** (Geometrie
und Familien: Meridian TPL-001…006 für App und HTML, ALUCA T1–T4 im 12×12-Raster für PBIR). *(Klargestellt am 30.09.2026:
die Token-**Logik** — Ableitung, Rollen, Kontrastregeln, Notationen — ist Klasse A, §2.1; ebenso das
Zonen-Vokabular, auf das beide Template-Sätze abbilden.)* Diese Unterschiede werden **nicht** eingeebnet — sie
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

**Was ein Sensor über sich selbst sagen muss (D-341, 27.08.2026).** Ein Spiegel-Sensor
vergleicht gegen einen *Arbeitsbaum*, nicht gegen `origin`. Steht der still, sehen beide
Seiten deckungsgleich aus — weil beide alt sind. Genau in diesem Fenster lag der
`platform.sizing`-Vorfall. Beide Sensoren messen deshalb die Herkunft ihres Gegenübers
(HEAD, Rückstand gegen den Upstream-Ref, unsaubere Arbeitskopie, Alter von
`.git/FETCH_HEAD`) und tragen sie in der Erfolgszeile mit, statt Deckungsgleichheit
unqualifiziert zu behaupten. Geholt wird nie von selbst — `--fetch` macht das Holen zur
ausdrücklichen Handlung, wie `--write` das Spiegeln.

Und beide unterscheiden **drei** Ausgänge statt zwei. Gemessen 27.08.2026: ohne
Gegen-Checkout endeten beide unter `--strict` mit **rc=0**, das Release-Gate bestand also
genau dann, wenn nichts geprüft worden war — dieselbe Klasse wie ein Tor, das „nichts
gefunden" nicht von „nicht gelaufen" unterscheidet.

| Exit | Bedeutung |
|---|---|
| 0 | verglichen, deckungsgleich |
| 1 | Drift (oder lokal editierter Vendor-Baum) |
| 2 | **konnte nicht vergleichen** — kein Gegen-Checkout, oder unsichere Frische unter `--strict` |

Ein Aufrufer, der beide roten Zustände in eine Zahl faltet, kann sie nicht lesen: der
delegierte Rückwärts-Aufruf meldete „GEGENRICHTUNG gedriftet", während die zitierte Ausgabe
darunter wörtlich „in sync" sagte.

**Richtung:** Klasse A hat pro Asset genau **eine Quelle der Wahrheit** — das Repo,
in dem es entstanden ist (Spalte „Heimat heute"). Das andere Repo spiegelt.
Änderungen gehen immer zuerst in die Heimat, dann in den Spiegel. Zwei
gleichberechtigte Stände sind ausdrücklich nicht das Ziel — das war der Zustand,
der die Drift erzeugt hat.

**Grenze zur Kundenlaufzeit** (unverändert aus dem Official-First-Prinzip): Geteilt
wird die eigene Entwicklungs-/CI-Pipeline. Deliverables beim Kunden bleiben
tool-freie Dateien (JSON/TMDL/PBIR/DOCX).

---

## 4. Was diese Doktrin sofort ausgelöst hat

Die drei Arbeitspakete, die hier ursprünglich (28.07.2026) als offen standen, sind
erledigt. Nachgemessen am 26.08.2026, jedes einzeln:

1. **ALUCA-Vollzug, zwei harte Defekte — behoben.**
   - `POST workspaces/{ws}/governanceLabels` ist ersetzt durch die Power-BI-**Admin**-API
     `admin/informationprotection/setLabels` (artefakt- statt workspace-bezogen,
     `Tenant.ReadWrite.All`, 25 Requests/Stunde, 2000 Artefakte pro Request); Tests prüfen
     den Aufrufpfad. Für **Endorsement** gibt es weiterhin *keine* dokumentierte Write-API
     — das bleibt ein ausgewiesener manueller Schritt und kein erfundener Endpunkt.
   - `fabric_release.py` nimmt `--workspace_id`, `--domain_filter` und `--dry_run` an und
     liest sowohl `AZURE_*` als auch die blanken `TENANT_ID`/`CLIENT_ID`/`CLIENT_SECRET`.
2. **Meridians Vollzugshälfte — vorhanden** als `vendor/aluca/orchestrator.py`.
3. **ALUCAs Kompilierhälfte — geschlossen.** Der Spiegel führt 34 Dateien statt 13. Die
   Menge ist die transitive Hülle über die Importe der Kandidaten, nicht eine Auswahl nach
   Gefühl; sie schließt ohne Import außerhalb des Pakets und **ohne** Meridians eigenen
   Deriver (`blueprint.py`) — den zu spiegeln hieße, ALUCA einen zweiten Deriver zu geben.

   Gemessen gegen dieselbe Fixture (ein Domain, ein Gold-Produkt, zwei Quellen):

   | Stack | vorher | nachher |
   |---|---|---|
   | fabric | 39 | 99 (104 mit beantworteter Quell-Introspektion) |
   | databricks | konnte nicht laufen | 16 |
   | snowflake | konnte nicht laufen | 4 |

   „Konnte nicht laufen" ist wörtlich: der CLI-Aufrufer reichte `source_schema_results`
   bedingungslos durch, und beide Ziele nehmen die Option nicht an — jeder Lauf endete mit
   `does not accept: source_schema_results`, obwohl beide als Auswahl angeboten waren.

**Was der Vollzug über die Doktrin selbst gelehrt hat.** Zwei Befunde, die keiner
Aufgabenliste entstammen, sondern der Messung:

- **Ein lazy Import ist beim Spiegeln unsichtbar.** `provision_governance.model_roles()`
  importiert erst im Funktionsrumpf `core.pbi_engine.parsers.tmdl_parser`; in ALUCA war das
  ein `ModuleNotFoundError`, während jeder Modulimport und `emit_governance` grün blieben.
  Der Fund kam aus dem **Bestand**, nicht aus dem Neuzugang — die erste Hüllen-Messung
  tastete nur die Kandidaten ab. Es ist die zweite Ausprägung derselben Klasse nach `odcs`.
  Beide sind heute vom selben Test abgedeckt, und die erlaubten Ausnahmen liest der Test aus
  dem Loader, statt sie nachzutippen.
- **Ein Emitter ohne Eingabe ist kein Fehler, aber er darf nicht wie Erfolg aussehen.** Vier
  der gespiegelten Emitter liefern gegen diese Fixture null Dateien (keine Copy-Quelle,
  keine Kulturliste, kein `governance`-Abschnitt, keine beantwortete Introspektion). Der
  Lauf nennt sie namentlich samt fehlender Eingabe, im Runbook der Lieferung. Ein Tor, das
  „nichts gefunden" nicht von „nicht gelaufen" unterscheiden kann, misst beides als Erfolg.

---

## 5. Für neue Arbeit

Vor jedem neuen Modul, jeder neuen Regel, jedem neuen Emitter: **erst klassifizieren.**

- Klasse A → in der Heimat bauen, Spiegel im selben Arbeitsschritt nachziehen,
  Sensor grün halten. Nicht „später spiegeln" — genau daraus entsteht Drift.
- Klasse B → im eigenen Repo bauen. ~~Nicht anbieten.~~ *(abgelöst am 30.09.2026)* Hebt
  es die Qualität im anderen Repo, dort als Spiegel mit PIN und Sensor einziehen (§2.2).
- Klasse C → in beiden bauen, bewusst unterschiedlich, ohne Paritätsanspruch.

Wer eine Klasse-A-Zusage ändert, ohne den Spiegel nachzuziehen, hinterlässt genau
den Zustand, den dieses Dokument abschafft.
