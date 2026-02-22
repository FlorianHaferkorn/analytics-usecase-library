# Was du bereitstellen musst, damit ich das Projekt voll einrichten kann

Damit das Einrichtungsskript **alles** erledigen kann (granulare Issues anlegen, dem Project zuordnen, Felder setzen), brauche ich von dir **zwei Dinge**:

---

## 1. GitHub Token (mit Berechtigungen)

- **Scope:** `repo` (für Issues, Milestones, Labels) und **`project`** (für „Issue zum Project hinzufügen“ und Feldwerte setzen).
- **Wo anlegen:** GitHub → Settings → Developer settings → Personal access tokens → Generate new token (classic). Scopes: `repo`, `project` anhaken.

**Token nicht ständig eintippen:** Einmal eine Datei **`.env`** im **Repo-Root** anlegen (siehe `tooling/project_mgmt/.env.example`). Die Skripte laden sie automatisch; `.env` steht in `.gitignore` und wird nicht committed.

```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PROJECT_NUMBER=2
PROJECT_SCOPE=user
PROJECT_OWNER=FlorianHaferkorn
```

Alternativ: Umgebungsvariablen pro Session setzen oder [GitHub CLI](https://cli.github.com/) `gh auth login` (Token wird dann vom Skript genutzt).

---

## 2. Projekt-Nummer, Scope und Felder (dein bereits angelegtes Project)

- **User-Projekt** (z. B. `https://github.com/users/FlorianHaferkorn/projects/2`):  
  Dann **Projekt-Nummer 2** und **User-Scope** setzen:
  ```powershell
  $env:PROJECT_NUMBER = "2"
  $env:PROJECT_SCOPE = "user"
  $env:PROJECT_OWNER = "FlorianHaferkorn"
  ```
- **Repository-Projekt** (z. B. `.../analytics-usecase-library/projects/1`):  
  Dann nur `PROJECT_NUMBER = "1"` (Standard), `PROJECT_SCOPE` weglassen.
- **Felder:** Das Skript `set_project_fields_only.ps1` legt fehlende Felder (Status, Milestone, Area, Priority, Risk) per API automatisch an – du musst sie **nicht** manuell im Project anlegen. Optionen wie in [PROJECT_FIELDS_AND_LABELS.md](PROJECT_FIELDS_AND_LABELS.md).
- **Wie übergeben:** Beim Ausführen des Skripts als Umgebungsvariable, z. B.:
  ```powershell
  $env:PROJECT_NUMBER = "1"
  ```
  Wenn du nichts setzt, wird standardmäßig `1` verwendet.

---

## Ausführung (einmalig)

Aus dem Repo-Root (z. B. `c:\Users\florianhaferkorn\VSCode\analytics-usecase-library`):

**PowerShell (ohne Python):** Wenn `.env` im Repo-Root existiert, reicht:

```powershell
.\tooling\project_mgmt\setup_project_full.ps1
```

Ohne `.env` zuerst die Variablen setzen:

```powershell
$env:GITHUB_TOKEN = "ghp_dein_token"
$env:PROJECT_NUMBER = "2"
$env:PROJECT_SCOPE = "user"
$env:PROJECT_OWNER = "FlorianHaferkorn"
.\tooling\project_mgmt\setup_project_full.ps1
```

**Alternativ mit Python** (falls installiert): `python tooling/project_mgmt/setup_project_full.py`

Das Skript wird dann:

- Milestones anlegen (falls fehlend): Project completion, Phase 2, Technical backlog  
- Labels anlegen (falls fehlend): epic, bug, blocker  
- **Granulare Issues** anlegen (viele kleine Tasks, siehe [BACKLOG_GRANULAR.md](BACKLOG_GRANULAR.md))  
- Jede Issue **dem Project hinzufügen**  
- Für jede Karte im Project die Felder setzen: **Status** = Backlog, **Milestone**, **Area**, **Priority** (und ggf. **Risk** = On track)

**Optional:** Repo explizit setzen, falls abweichend:

```powershell
$env:GITHUB_REPOSITORY = "FlorianHaferkorn/analytics-usecase-library"
```

**Nur Feldwerte setzen** (z. B. nach manuell angelegten Feldern oder bei neuem Lauf):

```powershell
.\tooling\project_mgmt\set_project_fields_only.ps1
```

(Gleiche Umgebung wie oben – oder `.env` nutzen.)

---

## Kurz: Was ich brauche

| Was            | Wo/Wie |
|----------------|--------|
| **Token**      | `repo` + `project`; als `GITHUB_TOKEN` (oder nach `gh auth login`) |
| **Projekt-Nr.**| Aus Project-URL; als `PROJECT_NUMBER` (Default: 1) |

Danach reicht ein Lauf von `setup_project_full.py`, um das Projekt vollständig einzurichten (granulare Ziele + alles im Board mit gesetzten Feldern).
