# Production Quality Standard

Dieser Standard definiert den ersten maschinenlesbaren Produktionsvertrag fuer den Fabric/Power BI Report Generator.

Die technische Policy liegt in products/fabric/powerbi/tooling/production_quality.standard.json.

## Ziel

Ein Lauf gilt nur dann als produktionsreif erfolgreich, wenn folgende Gates gruen sind:

- Stage 1
- Fabric Checks
- Report Structure Check
- PBIP Validation
- pbi-tools compile (nur fuer pbi-tools-kompatible PbixProj-Layouts; PBIP-Split-Layouts werden ueber PBIP-Validation und Readiness abgesichert)
- Workspace Publish
- Post-Publish Smoke Test

Diese Gates werden jetzt zentral ueber tooling/pbi_validate_after_impl.ps1 aggregiert und koennen durch products/fabric/powerbi/tooling/invoke_production_supervisor.ps1 in einem kontrollierten Loop ausgefuehrt werden.

## Erster Implementierungsslice

Der aktuelle Stand fuehrt vier Dinge ein:

- Einen maschinenlesbaren Standard in products/fabric/powerbi/tooling/production_quality.standard.json
- Strukturierte Gate-Ergebnisse in tooling/pbi_validate_after_impl.ps1
- Einen Supervisor fuer wiederholbare Produktionslaeufe in products/fabric/powerbi/tooling/invoke_production_supervisor.ps1
- Einen kanonischen Publish-Adapter in products/fabric/powerbi/tooling/invoke_workspace_publish.ps1

## Supervisor-Verhalten

Der Supervisor arbeitet jetzt in drei Phasen:

- Validieren
- Fehler klassifizieren und erst deterministisch, dann optional per LLM fixen
- Bei gruenen Artefakten in den Workspace publishen und Smoke-Test auswerten

Deterministische Fixes werden fuer bekannte Fehlerklassen zuerst ausgefuehrt. Dazu gehoeren insbesondere TMDL-, PBIP- und Compile-/Readiness-Probleme. Erst wenn danach noch Fehler uebrig sind, wird optional ein begrenzter LLM-Fix-Versuch gestartet.

## Publish-Pfad

Der Publish erfolgt nicht mehr ueber das stubhafte orchestrator/deploy.ps1, sondern ueber den bestehenden Python/Fabric-CI-CD-Stack in products/fabric/powerbi/deployment/scripts/fabric_release.py. Der PowerShell-Adapter staged die aktuellen dist-Artefakte in eine release-kompatible Struktur und ruft dann das Release-Skript auf.

Ohne gueltige TENANT_ID-, CLIENT_ID- und CLIENT_SECRET-Umgebungsvariablen kann der Adapter optional nur als Dry-Run laufen. Ein Dry-Run erfuellt den Produktionsstandard bewusst nicht.

Fuer Umgebungen ohne verfügbare Fabric-Credentials kann der Supervisor temporaer mit AcceptDryRunPublish betrieben werden. Dann gilt ein erfolgreicher Dry-Run-Staging-Lauf als vorlaeufige Abnahme, wird aber im Resultat explizit als credentialless_dry_run markiert und ersetzt keinen echten Workspace-Publish.

## Nutzung

Use Case:

```powershell
.\products\fabric\powerbi\tooling\invoke_production_supervisor.ps1 -UseCase COM-001 -UseAuroraData
```

Use Case ohne Credentials, aber mit vorlaeufiger Dry-Run-Abnahme:

```powershell
.\products\fabric\powerbi\tooling\invoke_production_supervisor.ps1 -UseCase COM-001 -UseAuroraData -AcceptDryRunPublish
```

Domain:

```powershell
.\products\fabric\powerbi\tooling\invoke_production_supervisor.ps1 -Domain Commercial -UseAuroraData
```

Alle:

```powershell
.\products\fabric\powerbi\tooling\invoke_production_supervisor.ps1 -All -UseAuroraData
```

Nur Publish trocken pruefen:

```powershell
.\products\fabric\powerbi\tooling\invoke_workspace_publish.ps1 -Environment tst -DryRun
```
