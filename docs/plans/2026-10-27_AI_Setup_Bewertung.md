---
status: empfehlung
datum: 2026-10-27
scope: Entwicklungswerkzeuge fuer Reportqualitaet; getrennt von visuellen Referenzen
---

# AI-Setup: Nutzen der neuen Inputs

**Kein pauschales Skillpaket installieren.** Vorrang haben die vorhandene Renderstrecke,
semantische Gegenproben und die Verbindung zum bestehenden E2E-Framework. Neue Tools
werden nur bei nachgewiesenem Mehrwert für diesen Ablauf übernommen.

Die 17 Setup-/Workflow-Screenshots liegen separat unter
`.local/report-quality/ai-setup-inputs/2026-10-27/`. Sie sind keine visuellen Qualitätsreferenzen.
Die übrigen fünf Bilder der ursprünglichen Inputserie zeigen tatsächliche Web-/Dashboardentwürfe
und bleiben als visuelle Referenzen in der Galerie. Keine Installation in dieser Runde.

## Bewertung am bestehenden Setup

| Input / Primärquelle | Brauchen wir das? | Konkrete Empfehlung und Trade-off |
|---|---|---|
| [Playwright CLI](https://github.com/microsoft/playwright/blob/main/docs/src/getting-started-cli.md) | Fähigkeit ja, zusätzliche CLI optional | Vorhandene Playwright-Strecke weiterverwenden. CLI nur als Bedienungs-Pilot für Agenten; keine zweite Testsuite. Screenshots, Traces und Assertions bringen Nutzen, bloße Navigation nicht. |
| [Impeccable](https://github.com/pbakaus/impeccable) | Selektive Prüfmuster sinnvoll | `critique`, `audit`, `harden`, `layout`, `typeset`, `clarify` gegen vorhandene Rubrik abgleichen. Globale Font-/Farbverbote, zusätzliche PRODUCT-/DESIGN-SoTs und Installer-Hooks nicht ungeprüft übernehmen. Apache-2.0. |
| [Taste Skill](https://github.com/Leonxlnx/taste-skill) | Kein weiterer globaler Standard nötig | Art-Direction und echte Browserprüfung als Muster. Hoher Overlap mit Impeccable und vorhandenem Reportdesign. [v2 experimentell](https://www.tasteskill.dev/docs); Motion-/Dual-Mode-Defaults sind keine BI-Regeln. MIT. |
| [transitions.dev](https://github.com/JakubAntalik/transitions.dev) | Vorerst keine Installation nötig | Motion-Tokens und Zustandsübergänge für Web gezielt adaptieren; native PBIR profitiert kaum. Tools und Rezept-/Skill-Nutzungsbedingungen unterscheiden; keine fremde Bibliothek weiterverteilen. |
| [GSAP Skills](https://github.com/greensock/gsap-skills) | Nur bei einem begründeten GSAP-Baustein | Offizielle API-/Cleanup-/Performance-Anleitung dann laden. Für Filter- oder Ladezustände reicht meist CSS. Skill- und Runtime-Lizenz getrennt betrachten. |
| [React Bits](https://github.com/DavidHDev/react-bits) | Für analytische Reports derzeit nicht nötig | Kein zusätzlicher Animationsstack für dekorative Effekte. Einzelkomponenten nur bei konkretem Bedarf prüfen. MIT plus Commons Clause, nicht uneingeschränkt MIT. |
| [Open Generative AI](https://github.com/Anil-matcha/Open-Generative-AI) | Nicht nötig; Identität UNKLAR | Falls dieses Projekt gemeint ist: Mediengenerierung, kein Reportvalidator; Fähigkeit bereits vorhanden. Generierte Dashboardbilder ersetzen keine echten Render- oder Wertnachweise. Screenshot allein identifiziert das gemeinte Repo nicht sicher. |
| [Strix](https://github.com/usestrix/strix) | Separater Security-Bedarf | Für später öffentlich exponierte Web-Apps prüfen; nicht als Reportqualitätswerkzeug einbauen. Vorhandene Securityskills zuerst nutzen. Apache-2.0. |
| [Book to Skill](https://github.com/virgiliojr94/book-to-skill) | Begrenzter Pilot kann sinnvoll sein | Eigene Reportleitfäden als on-demand Referenz aufbereiten; Quellenstellen, Versionen und Konfliktregeln erhalten. Extraktion liefert Vorschläge, keine neue Regelautorität. Konverterlizenz MIT deckt nicht die Ausgangsbücher. |
| [No AI Slop](https://github.com/petergyang/no-ai-slop) | Prüfmuster sinnvoll, eigener globaler Skill unnötig | Bestehende Schreibstil-/Narrative-Prüfung um konkrete Muster ergänzen. KPI-Namen, Werte und Einheiten müssen erhalten bleiben; keine Behauptung über die Urheberschaft eines Texts ableiten. MIT. |
| [Open Notebook](https://github.com/lfnovo/open-notebook) | Aktuell nicht nötig | Zusätzliche Researchplattform mit Betriebsaufwand. Erst bei belegter Lücke in umfangreicher Quellensuche pilotieren; Repo-/Ledger-Autorität bleibt bestehen. MIT. |
| Animation aus Daten, Audio, SaaS-Intros, kinetische Titel | Keine Setupvoraussetzung | Für Reportproduktion kein Pflichtbaustein. Bei einem Story-/Präsentationsziel gezielt prüfen; Bewegung muss Informationsgewinn haben und statische/reduzierte Ausgabe erlauben. Die Social-Media-Leistungsbehauptungen sind nicht verifiziert. |

## Bestehende Anschlusspunkte

- `tooling/visual_library/acceptance/render_recharts.mjs` verwendet bereits Playwright.
- `tooling/visual_library/acceptance/render_acceptance.py` hält echte Rasterisierung
  und Desktopabnahme auseinander.
- `products/fabric/powerbi/docs/references/desktop-bridge-screenshot-workflow.md`
  beschreibt die bestehende native Bildstrecke.
- `tooling/report_quality/llm_backend.py` ist der Anschluss für tatsächliche
  multimodale Evidenz; zusätzliche Designskills beheben seine Text-only-Grenze nicht.

## Empfehlung für die Übernahme

1. Vorhandene Render-/Werteprüfung schließen, bevor weitere Skills installiert werden.
2. Impeccable- und No-AI-Slop-Muster auf Lücken unserer vorhandenen Prüfungen reduzieren.
3. Höchstens einen kontrollierten Webpilot mit Impeccable **oder** Taste durchführen,
   optional mit Playwright CLI; gleiche Daten, Aufgabe und Referenzbilder wie beim Bestand.
4. Übernahme nur bei nachgewiesenem besseren Ergebnis oder weniger Nacharbeit;
   keine zweite Rubrik, keine zweite KPI-Autorität, kein zweiter E2E-Orchestrator.

Die identifizierten Repos wurden als Primärquellen geprüft. Die Zuordnung eines
Social-Media-Screenshots zu einem gleichnamigen Projekt ist bei Open Generative AI
ausdrücklich offen. Keine Toolinstallation oder neue globale Setupregel beschlossen.
