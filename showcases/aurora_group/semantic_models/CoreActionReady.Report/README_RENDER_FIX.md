# Report Render Error: visualContainers undefined

## Symptom

**"Fehler beim Rendern des Berichts"** mit:

`Cannot read properties of undefined (reading 'visualContainers')`  
(DesktopExplorationComponent.onExplorationActivated)

## Was bereits versucht wurde

- Nur Seiten durch Desktop-Sample (Procurement) ersetzt → Fehler bleibt
- **Komplette** `definition/` von Procurement übernommen (report.json, version.json, pages/) → Fehler kann weiterhin auftreten

Aurora-Report verwendet jetzt die **exakt gleiche** Definition wie der Sample-Report (ohne Custom-Theme), nur `definition.pbir` verweist auf `../CoreActionReady.SemanticModel`.

## Diagnose: Öffnet der Sample-Report?

Bitte testen:

1. Power BI Desktop **komplett schließen**.
2. **Procurement-Sample** öffnen:  
   `showcases/sample_pbip_report/Procurement_Wireframe_Theme.pbip`  
   (Doppelklick oder Datei > Öffnen)

- **Wenn Procurement ebenfalls den Render-Fehler zeigt:**  
  Wahrscheinlich Umgebung (Desktop-Version, PBIR-Preview, Pfad/Rechte).  
  Optionen: Desktop neu installieren/reparieren, anderes Verzeichnis (z. B. kurzer Pfad ohne Sonderzeichen), Preview-Feature „Store reports using enhanced metadata format (PBIR)“ prüfen.

- **Wenn Procurement ohne Fehler öffnet, Aurora (CoreActionReady.pbip) aber nicht:**  
  Dann hängt der Fehler mit der **Kombination Report + CoreActionReady-Semantic-Model** zusammen (z. B. andere Modellstruktur, Ladezeit, oder Bug beim Aufbau der Exploration bei diesem Dataset).  
  In dem Fall: Fehler an Microsoft melden (Frown), mit Hinweis:  
  „PBIR report opens when using Procurement_Wireframe_Theme.Report; same definition folder fails with visualContainers undefined when report references CoreActionReady.SemanticModel.“

## Aktueller Stand des Aurora-Reports

- **definition/** = Kopie von Procurement (report.json ohne Custom-Theme, version.json 2.0.0, pages/ unverändert).
- **definition.pbir** = `version: "4.0"`, `datasetReference: byPath "../CoreActionReady.SemanticModel"`.

Zum Testen: `showcases/aurora_group/semantic_models/CoreActionReady.pbip` erneut öffnen.

## Referenz

- [Power BI Desktop project report folder (PBIR)](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report)
- Sample: `showcases/sample_pbip_report/Procurement_Wireframe_Theme.pbip`
