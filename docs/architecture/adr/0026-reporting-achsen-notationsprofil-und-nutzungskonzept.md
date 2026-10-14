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

## 6. Nachtrag 09.10.2026: im Monitoring Farbe nur bei verletzter Bedingung, nach Richtung

**Entscheidung Florian 09.10.2026.** Vorzeichen-Färbung gilt im Profil `monitoring` nicht. Gefärbt wird nur, was
eine Bedingung in der Richtung der Kennzahl verletzt (`polarity` 1 = höher ist besser, -1 = niedriger ist besser);
eine gute Abweichung bleibt grau.

- **Anlass:** `with_focus(keep_conditions=True)` behielt jede Farbbedingung. Sechs Idiome färben im
  house_default-Template nach dem Vorzeichen (`deviation_bar`, `variance_pin`, `multi_tier_column` zweimal,
  `waterfall_pvm`, `waterfall_variance`: `< 0`) oder nach der Lage zum Ziel ohne Richtung (`lollipop`:
  `< target_val`). Bei einer Kennzahl „niedriger ist besser“ wurde damit eine gute Abweichung rot.
- **Form (Maschinenform):** optionales Feld `status_breach` je Idiom (`_schema.yaml`): je Bedingung der Test des
  Templates (`when`) und der Test, der ihn im Monitoring ersetzt (`breach`, mit `{{polarity}}`).
  `render.with_status_breach` tauscht die Tests, bevor `with_focus` das übrige grau setzt; `polarity_of` liest
  `polarity`, sonst `direction`, sonst 1. Andere Profile sind unberührt (Goldens unverändert).
- **Tests** (`tooling/visual_library/tests/test_usage_concepts.py`): jede Farbbedingung jedes Idioms im Monitoring
  hängt von der Richtung ab (`test_monitoring_colours_only_by_direction`, mit Gegenprobe: unter `house_default`
  färben die sechs weiter nach dem Vorzeichen); `deviation_bar` gute Abweichung grau, schlechte rot, für beide
  Richtungen; `lollipop` unter dem Ziel grau bei „niedriger ist besser“. Gegenprobe gemessen: ohne den Tausch fallen
  drei der Tests.
- **Nicht geändert:** Serienfarben mit Legende (`area_stacked`, `bar_stacked`, `donut`, `stacked_100`) bleiben wie in
  §2 Nr. 4 (Feldskala, `with_focus` lässt sie); ob das Monitoring sie ebenfalls grau setzt, ist nicht entschieden.
  `bar_ranking` färbte schon nach Richtung und Ziel.
