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

| Modul | Was es kodiert |
|---|---|
| `provision_governance.py` | OneLake-Security-Rollen (`dataAccessRoles`), RLS/OLS-TMDL, Access-Layer-Entscheidung |
| `provision_monitoring.py` | Workspace-Failure-KQL, Kapazitäts-Throttling-Alert, Pipeline-Benachrichtigungen |
| `provision_lifecycle.py` | `OPTIMIZE`/`VACUUM RETAIN`, Retention-Policy, BCDR-Runbook |
| `provision_connectivity.py` | Managed Private Endpoints |
| `provision_operability.py` | Metadaten-Vollständigkeit als Funktionsbedingung, Betriebs-Runbook |
| `capacity_recommend.py` | SKU-Guardrails inkl. Direct Lake |
| `admin_settings.py` | Tenant-Settings-Vorbedingungen |
| `decision_proposals.py` | Vorbelegte Entscheidungen (RLS/CLS/Retention/Endorsement/…) |
| `naming.py` | Namenskonvention (Abhängigkeit von `provision_lifecycle`) |
| `PIN.json` | sha256-Manifest über die neun Module |
| `_MIRROR.md` | diese Datei — ALUCA-eigen, **nicht** Teil des Spiegels |

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

## Änderungen

Immer **zuerst in Meridian**, dann spiegeln:

```bash
# 1. in Meridian ändern + dort testen
# 2. in ALUCA neu spiegeln (bewusst manuell)
MERIDIAN_ROOT=../Freelancing python scripts/check_dataarch_mirror.py --write
# 3. prüfen
python scripts/check_dataarch_mirror.py --strict
```

`scripts/check_dataarch_mirror.py` prüft beides: die Vertragsfläche der handgespiegelten
Registries (Konzepte/Governance/ODCS) **und** die Datei-Hashes dieses Teilbaums. Lokale
Integrität läuft immer, auch ohne Meridian-Checkout; der Upstream-Diff ist advisory,
`--strict` fürs Release-Gate. Gegenstück in Meridian: `scripts/check_aluca_mirror.py`.
