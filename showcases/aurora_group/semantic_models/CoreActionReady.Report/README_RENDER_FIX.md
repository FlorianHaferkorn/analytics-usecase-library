# Report Render Error: visualContainers undefined

## Symptom

Beim Öffnen des Reports erscheint: **"Fehler beim Rendern des Berichts"** mit JavaScript-Fehler:

`Cannot read properties of undefined (reading 'visualContainers')`  
(DesktopExplorationComponent.onExplorationActivated)

## Ursache

Die Report-UI erwartet pro Seite ein Objekt mit `visualContainers`. Diese Struktur baut Power BI nur zuverlässig auf, wenn die `definition/`-Seiten **von Desktop erzeugt und gespeichert** wurden. Manuell oder per Tool angelegte PBIR-Seiten führen bei der Deserialisierung oft zu fehlenden `visualContainers`.

## Aktueller Stand (Fix)

Die **gesamte** `definition/pages/`-Struktur wurde durch die **von Desktop erstellte** aus dem Sample-Report **Procurement_Wireframe_Theme** ersetzt. Damit ist die Exploration-Struktur identisch mit einem funktionierenden PBIR-Report.

- **Eine Seite:** `acace51fa4cc07dc3900` (Overview) mit 20 Visuals – ursprünglich Procurement-Inhalt.
- **Dataset:** Unverändert `definition.pbir` → `../CoreActionReady.SemanticModel` (Aurora).
- **Report/Theme:** Unverändert `definition/report.json` (Base-Theme CY25SU12, keine Procurement-spezifischen Filter).

**Erwartetes Verhalten:**

1. Report öffnet ohne Render-Fehler; du kannst **neue Seiten manuell anlegen** (Plus-Button).
2. Die erste Seite zeigt die Procurement-Visuals; Felder können fehlen oder leer sein, weil das Modell CoreActionReady (Aurora) ist. Du kannst die Seite umgestalten oder neue Seiten für COM001/COM002 anlegen und nach dem Speichern die gewünschten Visuals einrichten.

## Nächste Schritte

- **Neue Seite anlegen:** In Desktop „Seite hinzufügen“ nutzen, Report speichern – die neue Seite wird von Desktop korrekt in `definition/pages/` geschrieben.
- **Aurora-Seiten wiederherstellen:** Die früheren COM001/COM002-Seiten liegen in `showcases/aurora_group/reports/COM-001.Report/` und `COM-002.Report/` (definition/pages/). Nach dem Speichern neuer leerer Seiten in diesem Report kannst du Inhalte von dort übernehmen oder die neuen Seiten in Desktop mit den gewünschten Visuals bestücken.

## Referenz

- [Power BI Desktop project report folder (PBIR)](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report)
- Sample-Report: `showcases/sample_pbip_report/Procurement_Wireframe_Theme.Report/`
