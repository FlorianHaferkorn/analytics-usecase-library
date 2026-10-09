# ADR-0026 — Reporting-Achsen: Notationsprofil × Nutzungskonzept

| Feld | Wert |
|---|---|
| Status | **Accepted** (09.10.2026) |
| Entscheider | Florian Haferkorn |
| Kontext | Konzept „Reporting-Profile“ im Freelancing-Repo (`docs/konzepte/2026-10-09_Konzept_Reporting-Profile.md`, Branch `runde/2026-10-09-reporting-konzepte`); Meridian D-720 (zwei Achsen, Standard), D-721 (Bewegung), D-641 (Titelkonvention) |
| Betrifft | `core/templates/page_templates/visual_library/_notation_profiles.yaml` · neu `_usage_concepts.yaml` · `tooling/visual_library/render.py` · `tooling/generator/schemas/usecase_bracket.schema.json` (`ux_layout_rules.usage_concept`) |
| Bezug | A-31 (Profilachse der Visual Library), Meridian D-635/D-638 (Profile und Cockpit-Varianten), D-719 (Branch, `visual_profile` trägt die Notation, `house_default` Standard) |

## 1. Kontext

Die Visual Library kennt eine zweite Achse neben dem Idiom: das Profil. Es ist entweder eine
Notation (`house_default`, `ibcs`, `print_safe`) oder ein Stil (`fluent`, `editorial`, `minimal`,
`story`). Florian will mehrere Reporting-Konzepte anbieten, IBCS soll eines davon sein. Die
vorgeschlagene Liste (IBCS, Narrativ, Monitoring, Explorativ, Editorial, Marke, Entscheidung)
mischte zwei Dinge: wie ein Chart gezeichnet wird und wie eine Seite gebaut und gelesen wird.
IBCS 2.0 trennt selbst Notation von Composition.

## 2. Entscheidung

1. **Zwei unabhängige Achsen.** Das Notationsprofil bleibt in `_notation_profiles.yaml`. Neu ist
   das Nutzungskonzept in `_usage_concepts.yaml`: `entscheidung` (Standard), `narrativ`, `monitoring`,
   `explorativ`. Jedes Konzept hat Seitenaufbau, Dichte, Interaktion, Quelle und die erlaubten
   Profile (Ausschlüsse als Liste, getestet).
2. **Bracket.** Ein Use Case kann sein Konzept in `ux_layout_rules.usage_concept` angeben
   (optional, Enum = Registry, getestet). Ohne Angabe gilt der Registry-Default oder die Wahl des
   Konsumenten (Meridian `reporting.json`, D-720).
3. **`editorial` folgt D-641.** Der Titel ist beschreibend, die Erkenntnis steht in der getrennten
   Kernaussage. Die Redaktionsquellen (BBC, Urban, ONS) setzen die Erkenntnis in die Headline. Hier
   wird bewusst abgewichen, weil ein statischer wertender Titel dem gefilterten Chart widersprechen
   kann (`tooling/reporting/title_policy.py`).
4. **Neues Stilprofil `monitoring`** (`kind: style`, `focus: status`). Datenmarken sind grau, nur
   Bewertungsbedingungen (Schwelle/Ziel verletzt) behalten die Statusfarbe. Das Profil ist als
   **Herleitung** gekennzeichnet (`basis: derivation`, `status: experimental`). Grundlage ist das
   High-Performance-HMI-Prinzip aus ANSI/ISA-101.01-2015, nur aus Sekundärquellen bekannt; die
   Norm ist nicht gelesen.
5. **`minimal` wird nicht angeboten** (`offered: false`). Es bleibt im Register, damit Renderer und
   Tests es abdecken, steht aber in keinem Nutzungskonzept. Die Quellen (Tufte, SWD) sind nur als
   Suchauszug belegt.

## 3. Begründung

- Ohne Feld ist eine Kombination nicht prüfbar. Mit dem Feld wird z. B. ein Leitstand im
  Story-Akzent ein Testbefund.
- Die Kombinationstabelle ist eine Herleitung aus den Konzeptregeln, nicht mit Lesern gemessen.
  Beispiele: Akzentprinzip gegen Alarmfarben schließt Monitoring × Story aus; Fluent hat keine
  Erzählgrammatik, also kein Narrativ × Fluent.
- `focus: status` nutzt `render.with_focus` mit `keep_conditions`, statt einen zweiten
  Graustufen-Mechanismus zu bauen (Tool-Reuse).

## 4. Folgen

- Tests: `tooling/visual_library/tests/test_usage_concepts.py` (Registry, Schema-Enum, Ausschlüsse,
  `minimal`, `editorial`, Monitoring-Herleitung, Status-Fokus mit Gegenprobe für `story`);
  `test_style_profiles_cite_the_corpus` lässt `derivation:`-Quellen nur bei `basis: derivation` zu.
- Keine Goldens geändert: Stilprofile werden nicht eingefroren, sondern gerendert und direkt geprüft.
- Offen und nicht in diesem ADR:
  - ob `title_contract` die Option `statement_title` verliert (D-641 nennt das als ALUCA-Folge);
  - die Meridian-Seite (Feld `usage_concept` in `reporting.json`, Cockpit-Default, Umstellung von
    Aurora/Stratus): Meridian BO-265 bis BO-267.
