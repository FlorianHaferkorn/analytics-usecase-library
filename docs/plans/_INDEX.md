---
last-reviewed: 2026-11-12
shelf-life-days: 90
---
# Pläne und Konzepte — Zentraler Anlaufpunkt (_INDEX)

> Konzepte, Umsetzungspläne, Reviews und Runbooks der großen Initiativen (Superversion,
> Report-Qualität, Layout-System, agentische Schleife). Sie lagen bis 29.09.2026 im
> Repo-Wurzelordner. Zuerst diese Datei, dann gezielt **ein** Dokument — die Pläne sind
> lang (bis ~2.000 Zeilen). Entscheidungen leben in den ADRs
> (`../architecture/_INDEX.md`), nicht hier; ein Plan-Ledger (Tasks abhaken) steht im
> jeweiligen Umsetzungsplan selbst.

| Feld | Wert |
|---|---|
| Stand | 2026-11-12 |
| Rolle | L0-Navigation für Pläne, Konzepte und Reviews |
| Nicht hier | `../../SYNERGY_ALUCA_MERIDIAN.md` bleibt im Wurzelordner (byte-gleiche Kopie im Freelancing-Repo) |
| Archiviert (12.11.2026) | `PRODUCT_PLAN.md`, `SUPERVERSION_ZIELBILD_REVIEW.md`, `UMSETZUNGSPLAN_SUPERVERSION.md` (Superversion-Bauplan, abgeschlossen) und `RESEARCH_INTERACTIVE_HTML_RENDERER.md` liegen als historischer Stand unter `../../_archiv/docs/plans/`; ADRs und Code-Kommentare verweisen dorthin |

## 1. „Lies-wenn"-Routing

| Deine Aufgabe ist … | Lies | NICHT nötig |
|---|---|---|
| Warum und wohin bei Report-Qualität (Boutique-Niveau, Craft-Core, Content-Grounding) | `KONZEPT_REPORT_QUALITAET.md` | archivierte Superversion-Pläne |
| Report-Exzellenz-Task (R-Serie) umsetzen oder abhaken | `UMSETZUNGSPLAN_REPORT_EXZELLENZ.md` → bei Bedarf `KONZEPT_REPORT_QUALITAET.md` | archivierte Superversion-Pläne |
| Layout-System, Absicht-statt-Visual, Konnektoren und Validator-Fehlerklassen | `KONZEPT_LAYOUT_SYSTEM.md` (lang — über die Überschriften springen) | archivierte Superversion-Pläne |
| Renderer-gebundene Prüfungen auf einem Windows-/Fabric-Rechner abarbeiten (K6/K7) | `RENDER_GATED_RUNBOOK.md` | archivierte Superversion-Pläne |
| Agentische Schleife S0–S7 (Sandbox, Tenant-Lauf, Bildprüfung) planen oder fortsetzen | `UMSETZUNGSPLAN_AGENTIC_LOOP.md` → Skill `../agent/skills/run-agentic-loop.md` | KONZEPT_LAYOUT_SYSTEM |

## 2. Dokument-Register (vollständig — Drift-Gate erzwingt das)

| Doc | Zweck | Lies-wenn |
|---|---|---|
| `KONZEPT_REPORT_QUALITAET.md` | Konzept-Ebene Report-Qualität: Zielhöhe, Architektur, Cuts K1–K7 | Eine Report-Qualitätsentscheidung begründen |
| `UMSETZUNGSPLAN_REPORT_EXZELLENZ.md` | Fahrplan Report-Exzellenz: R-Serie, Cuts C1 ff., Ledger (§6) | Einen R-Task umsetzen oder dessen Befund (z. B. R2.3-Fund) nachlesen |
| `KONZEPT_LAYOUT_SYSTEM.md` | Tool-übergreifendes Layout-System, Layout-Systeme als Plugin, Validator-Fehlerklassen (§21) | Layout-/Visual-Vokabular ändern oder einen Layout-Validator-Fehler einordnen |
| `RENDER_GATED_RUNBOOK.md` | Checkliste für die Prüfungen, die Renderer, offizielle CLI oder Bild-Judge brauchen | Auf einem Windows-/Fabric-Rechner die offenen K6/K7-Prüfungen fahren |
| `UMSETZUNGSPLAN_AGENTIC_LOOP.md` | Agentische Report-Entwicklung als deterministische Schleife: Arbeitspakete AP-1 ff. | Sandbox-, Tenant- oder Bildprüfungs-Arbeit an der Schleife aufnehmen |
