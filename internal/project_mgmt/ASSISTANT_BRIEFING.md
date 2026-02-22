# Daily briefing (Assistant Agent)

**Purpose:** So wenig wie möglich selbst tun: Einmal täglich den **Assistant Agent** um ein Briefing bitten; darin stehen Fokus, Bottlenecks und **genau die nächste Aktion** (Skript + Implement issue #N). Du führst nur noch das aus, was im Briefing steht.

**Rule:** [.cursor/rules/assistant-agent.mdc](../../.cursor/rules/assistant-agent.mdc)

---

## Ablauf (minimaler Aufwand)

### Morgens (oder zu Arbeitsbeginn)

1. **Optional, einmal pro Tag:** Projektstand aktualisieren:
   ```powershell
   .\tooling\project_mgmt\refresh_project_snapshot.ps1
   ```
   Schreibt [PROJECT_SNAPSHOT.md](PROJECT_SNAPSHOT.md) mit Backlog/Planned und „Recommended next“. Wenn du das weglässt, sagt dir der Assistant im Briefing ggf., dass du es einmal ausführen sollst.

2. **Briefing anfordern:** In einer Chat-Session mit dem **Assistant Agent** (Rule aktivieren oder Session mit Rule starten) sagen:
   - *"Daily Briefing"* oder *"Briefing"* oder *"Was steht an?"*

3. Der Assistant liefert:
   - Entscheidungen / Fokus heute
   - Bottlenecks / Risiken
   - **Heute abarbeiten:** eine konkrete Aufgabe (Issue #N) inkl. der exakten Anweisung:
     - `.\tooling\project_mgmt\start_next_task.ps1` ausführen
     - Im Implementer: **Implement issue #N**

### Wenn du mit der Aufgabe startest

4. Die zwei Schritte aus dem Briefing ausführen:
   - `.\tooling\project_mgmt\start_next_task.ps1` (setzt das Item auf In progress)
   - Implementer-Session öffnen, sagen: **Implement issue #N**

5. Danach läuft alles automatisch: PR öffnen → Status In review, PR-Summary-Kommentar, Merge → Status Done (siehe [PM_FLOW.md](PM_FLOW.md)).

---

## Was der Assistant liest

| Datei | Inhalt |
|-------|--------|
| **PROJECT_SNAPSHOT.md** | Aktueller Stand Backlog/Planned, „Recommended next“ (Issue #, Titel, Expert). Wird von `refresh_project_snapshot.ps1` geschrieben. |
| **BACKLOG_GRANULAR.md** | Fein zerlegtes Backlog nach Milestones/Areas. |
| **presentation_status_and_roadmap.md** | Optional: High-level Status und Roadmap. |

Der Assistant führt keine Skripte aus und ruft keine APIs auf; er liest nur diese Dateien und formatiert das Briefing.

---

## Kurzfassung

- **Einmal täglich:** Optional Snapshot refreshen, dann „Briefing“ vom Assistant anfordern.
- **Zweimal pro Aufgabe:** Skript ausführen + „Implement issue #N“ im Implementer sagen; Rest (Status, PR-Summary, Done) ist automatisch.
