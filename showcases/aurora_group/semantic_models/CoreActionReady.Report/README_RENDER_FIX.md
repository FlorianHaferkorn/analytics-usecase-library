# Report Render Error: visualContainers undefined

## Symptom

Beim Öffnen des Reports erscheint: **"Fehler beim Rendern des Berichts"** mit JavaScript-Fehler:

`Cannot read properties of undefined (reading 'visualContainers')`  
(DesktopExplorationComponent.onExplorationActivated)

## Ursache

Der Report wurde nicht von Power BI Desktop als PBIR gespeichert, sondern die `definition/`-Ordnerstruktur wurde manuell/automatisiert angelegt. Beim Aktivieren der Report-Ansicht erwartet die Desktop-UI pro Seite ein Objekt mit der Eigenschaft `visualContainers`. Die interne Deserialisierung baut diese Struktur offenbar nicht zuverlässig aus der Ordnerstruktur, wenn der Report nie von Desktop geschrieben wurde.

## Aktueller Stand (Test)

Der Report wurde auf **eine Seite** reduziert und die Seite verwendet eine **Desktop-typische 20-Zeichen-ID** (`acace51fa4cc07dc3900`) wie im offiziellen Sample-Report. Damit wird getestet, ob die Exploration-Komponente mit dieser Namensform stabil rendert.

- **Eine Seite:** `definition/pages/acace51fa4cc07dc3900/` (Inhalt = ehemals COM001 Overview)
- **pages.json:** `pageOrder` und `activePageName` = `acace51fa4cc07dc3900`
- Die weiteren Seiten (Page_COM001_Detail, Page_COM002_Overview, Page_COM002_Detail) wurden vorübergehend entfernt.

Falls der Report so ohne Fehler öffnet, können die anderen Seiten schrittweise mit je eigener 20-Zeichen-ID wieder ergänzt werden. Falls der Fehler bleibt, siehe Workaround unten.

## Workaround (falls Fehler weiterhin auftritt)

1. **Neuen Report von Desktop erzeugen lassen**
   - Power BI Desktop öffnen, PBIR-Preview aktiviert lassen.
   - Neues Projekt (PBIP) anlegen oder ein bestehendes leeres Report-Verzeichnis mit `definition.pbir` (Version 4.0, Verweis auf Semantic Model) verwenden.
   - **Eine** leere Seite anlegen (Name egal), Report einmal **Speichern**.
   - Dadurch schreibt Desktop die `definition/`-Struktur in dem Format, das es beim Öffnen erwartet.

2. **Inhalte übernehmen**
   - Die von Desktop erzeugten Inhalte unter `definition/pages/` durch die gewünschten Seiten ersetzen (z. B. die bestehenden Page_COM001_Overview, Page_COM001_Detail, … inkl. `page.json` und `visuals/`).
   - `definition/pages/pages.json` anpassen (`pageOrder`, `activePageName`).
   - Report erneut in Desktop öffnen und prüfen; bei Bedarf erneut speichern.

3. **Alternativ**
   - Fehler an Microsoft melden (Frown/Feedback mit Kontext: PBIR mit manuell erstellter `definition/`, mehrere Seiten → beim Aktivieren der Report-Ansicht ist `visualContainers` undefined).

## Referenz

- [Power BI Desktop project report folder (PBIR)](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report)
- PBIR-Namensregel: Ordnername/`name` = Wortzeichen (Buchstaben, Ziffern, Unterstriche) oder Bindestriche; max. 50 Zeichen für Seitennamen.
