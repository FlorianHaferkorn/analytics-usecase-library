# Gespiegelte Meridian-Emitter (Meridian → ALUCA)

> **Nicht hier editieren.** Byte-identischer Spiegel. Eine lokale Änderung meldet der
> Sensor als Doktrin-Bruch (hart, auch ohne `--strict`), und `load_emitters()` verweigert
> den Dienst mit `VendorUnavailable`.

## Was hier liegt und warum

Nach [`SHARED_SUBSTANCE.md`](../../../../SHARED_SUBSTANCE.md) ist das **Klasse A**: reine
Kodierung offizieller Verträge (OneLake-Security-REST, `ItemJobEventLogs`-Schema,
Delta-Wartung, Managed-Private-Endpoint-Payload, SKU-Guardrails, Tenant-Settings). Der
Wert liegt in der Korrektheit, nicht in der Erfindung — deshalb gehört das in beide Repos,
mit **einer** Heimat. Heimat ist Meridian (`core/dataarch_engine/blueprint`), ALUCA
spiegelt.

### Betrieb — die Belange, mit denen der Spiegel angefangen hat

| Modul | Was es kodiert |
|---|---|
| `provision_governance.py` | OneLake-Security-Rollen (`dataAccessRoles`), RLS/OLS-TMDL, Access-Layer-Entscheidung |
| `provision_monitoring.py` | Workspace-Failure-KQL, Kapazitäts-Throttling-Alert, Pipeline-Benachrichtigungen |
| `provision_lifecycle.py` | `OPTIMIZE`/`VACUUM RETAIN`, Retention-Policy, BCDR-Runbook |
| `provision_connectivity.py` | Managed Private Endpoints |
| `provision_external_sharing.py` | External Data Share per Fabric-REST (Anlage, Einladung, Annahme), gesperrter Vertrag bis `status=approved` (seit 24.09.2026, Meridian #425) |
| `provision_operability.py` | Metadaten-Vollständigkeit als Funktionsbedingung, Betriebs-Runbook |
| `capacity_recommend.py` | SKU-Guardrails inkl. Direct Lake |
| `admin_settings.py` | Tenant-Settings-Vorbedingungen |
| `decision_proposals.py` | Vorbelegte Entscheidungen (RLS/CLS/Retention/Endorsement/Lakehouse-Schemas/…) |
| `naming.py` | Namenskonvention (Abhängigkeit von `provision_lifecycle`) |
| `source_schema.py` | `INFORMATION_SCHEMA`-Introspektion (ANSI + Dialekt-Abweichungen), OpenAPI-Lesung |
| `provision_source_schema.py` | Zwei-Phasen-Emission: erst die Frage an die Quelle, dann deren Antwort als Vertrag |

### Vollzug — dazugekommen am 26.08.2026

Bis dahin spiegelte ALUCA die Betriebs-Belange und emittierte im Übrigen nur die Topologie:
**39 Artefakte** gegen dieselbe Fixture, gegen die Meridian die vollständige Kette lieferte.
Alles hier ist von einem Hersteller festgelegte Form — `fab`-Aufrufe, fabric-cicd, der
`microsoft/fabric`-Terraform-Provider, Variable Libraries, Copy jobs, Notebooks, Pipelines,
TMDL-Kulturdateien, MetricFlow. Eine zweite Fassung davon wäre in beiden Repos gleich
falsch, also wird sie geteilt statt nachgebaut.

Gemessen nach der Aufnahme, dieselbe Fixture: **fabric 39 → 99** (104 mit beantworteter
Quell-Introspektion), **databricks 16** und **snowflake 4** — beide konnten vorher nicht
laufen (siehe „Ein Nebenbefund" unten).

| Modul | Was es kodiert |
|---|---|
| `provision_apply.py` | Ausführungsplan über die vierzehn Aktionsklassen, MCP-Anbindung |
| `provision_prereq.py` | Vorbedingungen des Zielstacks vor dem ersten Aufruf |
| `provision_gates.py` | Tore zwischen den Aufbauschritten |
| `provision_fabric.py` | die `fab`-Kommandofolge |
| `provision_cicd.py` · `provision_fabric_cicd.py` · `provision_databricks_cicd.py` | Deployment-Pipelines je Stack |
| `provision_terraform.py` | `microsoft/fabric`-Provider-Konfiguration |
| `provision_varlib.py` | Variable Libraries samt Wertesätzen je Stage |
| `provision_ingestion.py` | Copy jobs (nur für Quellen mit `access_mode: copy`) |
| `provision_transforms.py` · `provision_notebooks.py` | Transformationen und Notebooks je Stack |
| `provision_orchestration.py` | Pipelines/Zeitpläne |
| `provision_lineage.py` | Herkunftsnachweis |
| `provision_dq.py` | Eingangs-Datenqualität aus beantworteter Introspektion |
| `provision_chargeback.py` | Kostenzuordnung je Domäne |
| `provision_metricflow.py` | dbt Semantic Layer (stackneutral, trägt deshalb kein `stack`-Argument) |
| `provision_translations.py` | TMDL-Kulturdateien |
| `governance_strategy.py` | Governance-Strategie; **emittiert heute null Dateien**, weil ALUCAs IR keinen `governance`-Abschnitt trägt. Mitgespiegelt, weil `provision_apply` `LIFECYCLE_STAGES` daraus liest |
| `direct_lake_guardrails.py` | Direct-Lake-Grenzen |
| `fabric_schedule.py` · `stack_capabilities.py` · `sql_validate.py` | Zeitpläne, Stack-Fähigkeiten, DDL-Prüfung im Zieldialekt (`sqlglot` fehlt hier → ausgewiesener Soft-Skip) |

Die Menge ist **gemessen, nicht gegriffen**: transitive Hülle über die Importe der
Kandidaten, aufgelöst gegen `core.dataarch_engine.blueprint`. Sie schließt ohne Import
außerhalb des Pakets und ohne Meridians eigenen Deriver (`blueprint.py`) — den zu spiegeln
hieße, ALUCA einen zweiten Deriver neben `architecture_blueprint.py` zu geben. Der Test
`test_the_mirror_closes_without_reaching_outside_its_package` hält die Hülle messbar.

### Nicht im Spiegel

| Datei | Warum |
|---|---|
| `PIN.json` | sha256-Manifest über die 34 Module — **abgeleitet**, nicht die Entscheidung |
| `_MIRROR.md` | diese Datei — ALUCA-eigen, **nicht** Teil des Spiegels |

**Was** gespiegelt wird, entscheidet `MIRRORED_FILES` in
[`scripts/check_dataarch_mirror.py`](../../../../scripts/check_dataarch_mirror.py); das PIN
trägt nur die Hashes dazu. Die Reihenfolge ist wichtig: stünde die Liste im PIN, ließe sich
kein Modul aufnehmen — das verlangte eine PIN-Änderung von Hand, und genau die fängt das
Integritäts-Gate (zu Recht) als Doktrin-Bruch ab. `--write` läuft deshalb **vor** dem Gate:
es ist die Operation, die Integrität wiederherstellt.

## Wie ALUCA sie benutzt

Über [`tooling/superversion/_dataarch_vendor.py`](../../_dataarch_vendor.py):

```python
from tooling.superversion._dataarch_vendor import load_emitters
api = load_emitters()          # prüft vorher die Integrität gegen PIN.json
api["emit_governance"](blueprint)
```

`arch_targets/fabric.py` komponiert diese Artefakte über seine eigene Topologie-Ebene;
fehlt der Spiegel, entfällt die Ebene **sichtbar** (Hinweis im Runbook) statt still durch
eine halbrichtige Eigenimplementierung ersetzt zu werden.

**Die Import-Brücke.** Die Module importieren einander absolut als
`core.dataarch_engine.blueprint.…` (Meridian-Idiom, 123× im Quell-Repo — hier umzuschreiben
würde den Spiegel nicht mehr byte-identisch und die Hash-Prüfung wertlos machen). ALUCA
benutzt `core` aber selbst als Namespace-Paket. Der Loader hängt deshalb einen
`sys.meta_path`-Finder ein, der **ausschließlich** `core.dataarch_engine` und
`core.dataarch_engine.blueprint` beantwortet; alles andere — insbesondere `core` und
`core.brand` — fällt unverändert durch die reguläre Auflösung.

**Zwei Namen kommen nicht aus dem Spiegel.** Beide gehören derselben Fehlerklasse an: ein
Import im Funktionsrumpf ist beim Spiegeln unsichtbar und fällt erst beim Aufruf auf.

| Name | Wer ihn lazy importiert | Was untergeschoben wird |
|---|---|---|
| `…blueprint.odcs` | `source_schema.from_information_schema` | ALUCAs eigener ODCS-Writer (`tooling/superversion/odcs.py`) — ein zweiter, vendorter wäre das Doppel-Silo |
| `core.pbi_engine.parsers.tmdl_parser` | `provision_governance.model_roles` | die drei Rollenklassen aus dem Canonical-Core-Vendor (`vendor/meridian`), faul aufgelöst |

Die zweite Ausprägung ist am 26.08.2026 gefunden worden — **an Bestand, nicht an
Neuzugang**: `provision_governance` war lange gespiegelt, `emit_governance` lief, und
`model_roles` warf in ALUCA `ModuleNotFoundError: No module named 'core.pbi_engine'`. Die
erste Hüllen-Messung hat es übersehen, weil sie nur die neuen Kandidaten abtastete. Die
Brücke registriert **nur den Blattnamen**; `core.pbi_engine` entsteht nicht, ALUCAs
`core`-Namespace bleibt unberührt (Test: `test_the_bridge_does_not_create_a_core_pbi_engine_package`).
`model_roles` steht bewusst **nicht** in `PUBLIC_API`: ALUCA schreibt sein Semantikmodell
mit dem eigenen Generator, und eine zugesagte Funktion, die niemand ruft, ist ein
Versprechen ohne Halter.

**Ein Nebenbefund, gemessen 26.08.2026.** `--stack databricks` und `--stack snowflake`
standen seit jeher als Auswahl im CLI und scheiterten bei **jedem** Lauf mit
`does not accept: source_schema_results`: der Aufrufer reichte die leere Vorgabe
bedingungslos durch, und `arch_targets.render` weist eine Option zurück, die ein Ziel nicht
annimmt — zu Recht, denn sie stillschweigend fallen zu lassen sähe aus wie erfüllt. Behoben
in `architecture_blueprint_cli.run`; die 16 bzw. 4 Artefakte oben sind die erste Messung
überhaupt.

### Preis — dazugekommen am 03.09.2026 (ADR-0019 N-3)

| Modul | Was es kodiert |
|---|---|
| `preis_kanon.py` | Rechenkern des Preis-Kanons: Stunden je Satzklasse, Selbstkosten, Preis = Selbstkosten × (1 + r) × (1 + m), Rundung, Festpreis, Lieferzeit-Band (Meridian D-356) |

Der Kern ist die einzige Datei dieses Spiegels, die **nicht** aus `core/dataarch_engine/blueprint`
kommt — sie liegt in Meridian unter `core/preis_kanon.py`. Seit dieser Aufnahme darf ein Eintrag
in `MIRRORED_FILES` deshalb seinen Quellpfad selbst nennen; der PIN trägt für solche Dateien ein
`source`-Feld, alle anderen bleiben am Vorgabepfad `source_path`.

**Abweichung zu ADR-0019, benannt statt geglättet (Belegpflicht R5).** Das ADR nennt in §2.4 und
§5 N-3 `staffing.py` als den zu spiegelnden Rechenkern. Gemessen am 03.09.2026 auf genau dem Weg,
den `write_vendor` fährt — Datei kopieren, unter Meridians Modulnamen laden:

```
products/sales_proposal/staffing.py: ImportError: cannot import name 'preis_kanon' from 'core'
core/preis_kanon.py:                 lädt
```

`staffing.py` ist die Engagement-Schicht und zieht `core.preis_kanon` sowie
`products.governance_framework.delivery` nach; beide Pakete gibt es hier nicht, und ein Spiegel,
der Importe umschreibt, ist kein byte-identischer Spiegel mehr. Meridian sagt es in derselben
Datei selbst: „gespiegelt nach ALUCA wird der Kern, diese Schicht bleibt das Angebotsprodukt
dieses Repos." Die Entscheidung aus §2.4 — ein Rechenkern, nicht zwei — bleibt unberührt; nur die
Datei heißt anders.

Was ALUCA daraus **nicht** nutzt und warum, steht in `_dataarch_vendor.PUBLIC_API`: `pruefe_kanon`
erzwingt den Mandanten `freelancing` (dortiges D-357) und wäre hier per Konstruktion rot; die
MD-Renderer hängen an einem Repo-Pfad, der im Spiegel ins Leere zeigt. ALUCAs eigene Regeln und
das Laden aus `$PREIS_KANON_MANDANTEN_DIR` stehen in
[`../../preis_kanon_mandant.py`](../../preis_kanon_mandant.py).

## Änderungen

Immer **zuerst in Meridian**, dann spiegeln:

```bash
# 1. in Meridian ändern + dort testen
# 2. in ALUCA neu spiegeln (bewusst manuell)
MERIDIAN_ROOT=../Freelancing python scripts/check_dataarch_mirror.py --write
# 3. prüfen — --fetch holt vorher origin im Meridian-Checkout
python scripts/check_dataarch_mirror.py --fetch --strict
```

`scripts/check_dataarch_mirror.py` prüft beides: die Vertragsfläche der handgespiegelten
Registries (Konzepte/Governance/ODCS) **und** die Datei-Hashes dieses Teilbaums. Lokale
Integrität läuft immer, auch ohne Meridian-Checkout; der Upstream-Diff ist advisory,
`--strict` fürs Release-Gate. Gegenstück in Meridian: `scripts/check_aluca_mirror.py`.

**Seit D-341 (27.08.2026) sagt der Sensor auch, worauf er sich stützt.** Er vergleicht gegen
einen Arbeitsbaum, nicht gegen `origin`; steht der still, sehen beide Seiten deckungsgleich
aus, weil beide alt sind. Die Erfolgszeile trägt deshalb HEAD, Rückstand gegen den
Upstream-Ref, unsaubere Arbeitskopie und das Alter von `.git/FETCH_HEAD` mit. Geholt wird nie
von selbst — `--fetch` ist die ausdrückliche Handlung, wie `--write` beim Spiegeln.

Drei Ausgänge statt zwei, weil ein Aufrufer die zwei roten Zustände unterscheiden können muss:

| Exit | Bedeutung |
|---|---|
| 0 | verglichen, deckungsgleich |
| 1 | Drift (oder lokal editierter Vendor-Baum) |
| 2 | **konnte nicht vergleichen** — kein Meridian-Checkout, oder unsichere Frische unter `--strict` |

`--skip-freshness` bewertet die Frische nicht. Es gehört zu genau einem Aufrufer: Meridians
Sensor delegiert die Gegenrichtung hierher, und dort *ist* das Gegenüber Meridian selbst — sein
unversionierter Arbeitsstand ist der Gegenstand des Vergleichs und kein Grund, an ihm zu
zweifeln.
