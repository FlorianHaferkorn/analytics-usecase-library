# Projekt-Felder anlegen (bei Meldung „Project is missing required fields“)

**Wo:** GitHub → dein Repo → **Projects** → dein Projekt öffnen → **⋯** (oben rechts) → **Settings** → **Fields** (bzw. „Custom fields“ / „Felder“).

**Genau diese 4 Felder anlegen** (Typ: **Single select**, Namen und Optionen exakt so):

| Feldname   | Optionen (einzeln hinzufügen) |
|------------|-------------------------------|
| **Status** | `Backlog`, `Planned`, `In progress`, `In review`, `Done` |
| **Milestones** | `Project completion`, `Framework Package 1`, `Phase 2`, `Technical backlog` |
| **Area**   | `Framework`, `FabricPowerBI`, `Aurora`, `Tooling`, `Docs` |
| **Priority** | `P0`, `P1`, `P2` |

**Hinweis:** GitHub blockiert oft den Feldnamen „Milestone“. Dann **Milestones** verwenden – die Skripte unterstützen beides.

Optional (für Risiko/Status-Update):

| **Risk**   | `On track`, `At risk` |

Feldwerte (Status, Milestones, Area, Priority) im Project werden vom Sync aus dem Backlog ([granular_issues.json](../../tooling/project_mgmt/granular_issues.json)) gesetzt. Manuelle Änderungen in der Project-UI werden beim nächsten Sync überschrieben.

**Danach (Reihenfolge):**

1. **Duplikate finden:** Vom **Repo-Root** aus: `.\tooling\project_mgmt\list_project_duplicates.ps1` (Pfad erforderlich). Ausgabe: pro doppeltem Titel „KEEP #X“, „REMOVE #Y, #Z“.  
2. **Duplikate entfernen:** Vom Repo-Root: `.\tooling\project_mgmt\remove_project_duplicates.ps1` (entfernt alle Duplikate aus dem Projekt per API). Optional zuerst mit `-WhatIf` testen.  
3. **Felder setzen:** `.\tooling\project_mgmt\set_project_fields_only.ps1` – setzt Status/Milestones/Area/Priority auf alle verbleibenden Projekt-Items (liest Werte aus dem Issue-Body).
