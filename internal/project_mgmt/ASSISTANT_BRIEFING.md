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
     - Implementer-Session öffnen, sagen: **Start next task** (dann führt der Agent `start_next_task.ps1` aus, legt den Branch an und arbeitet die Aufgabe ab)
     - Oder manuell: `.\tooling\project_mgmt\start_next_task.ps1` ausführen, dann im Implementer: **Implement issue #N** (Agent legt den Branch an)

### Wenn du mit der Aufgabe startest

4. **Option A (empfohlen):** Implementer-Session öffnen, sagen: **Start next task**. Der Agent führt das Skript aus, erstellt den Branch und implementiert.
5. **Option B:** Zuerst `.\tooling\project_mgmt\start_next_task.ps1` ausführen (Endung **.ps1**, vom **Repo-Root**), dann Implementer öffnen und sagen: **Implement issue #N**. Der Agent erstellt den Branch und implementiert.

6. Danach läuft alles automatisch: PR öffnen → Status In review, PR-Summary-Kommentar, Merge → Status Done (siehe [PM_FLOW.md](PM_FLOW.md)). Optional: Nach dem Öffnen des PR eine Session mit [.cursor/rules/reviewer-agent.mdc](../../.cursor/rules/reviewer-agent.mdc) starten und **Review PR #N** sagen, um eine regelbasierte Prüfung zu erhalten.

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
- **Pro Aufgabe:** Im Implementer **„Start next task“** sagen (Agent führt Skript aus, erstellt Branch, implementiert, PR) – oder manuell Skript ausführen, dann „Implement issue #N“. Rest (Status, PR-Summary, Done) ist automatisch.
