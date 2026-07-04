# Navigations-Philosophie — warum dieses Repo so aufgebaut ist

Für Menschen **und** Agenten. Wer das verinnerlicht hat, arbeitet im Repo
token-effizient und ohne Nacharbeit.

## Problem, das es löst

Ein wachsendes Repo wird für einen Agenten (begrenztes Kontextfenster) und für
Menschen (begrenzte Aufmerksamkeit) schnell unnavigierbar. Zwei Failure-Modes:
- **Volltext-Scan**: der Agent liest halbe Ordner, um „den Überblick" zu kriegen →
  Token-Verschwendung, Fokusverlust, teure Halluzinationen über veralteten Stand.
- **Status-Drift**: offene Fragen/Entscheidungen liegen verstreut in Notizen →
  derselbe Punkt wird zweimal geklärt, Entschiedenes erneut gefragt.

## Drei Prinzipien

### 1. Navigieren statt scannen — `_INDEX.md` als L0
Jeder navigierbare Bereich hat **genau ein** `_INDEX.md`. Es ist der **einzige
Pflicht-Erstkontakt** und enthält eine **„lies-wenn"-Tabelle**: *„Deine Aufgabe ist
X → lies Doc A → Doc B; NICHT nötig: Rest."* Der Agent liest **L0 + ein Detail**,
nicht den Ordner. Regel: *ein L0 → ein-Detail-Pfad genügt für die meisten Aufgaben*.

### 2. Schichten + Ableitungsrichtung
Wo ein Bereich geschichtet ist (Strategie, Architektur, Roadmap), gilt L0→L4:
```
L0 Navigation → L1 Zielbild/Modell → L2 Detail → L3 Delivery → L4 Roadmap (DoD)
```
**Ableitung immer abwärts**: L4 leitet aus L1–L3 ab, nie umgekehrt. Das verhindert,
dass der Plan das Zielbild diktiert.

### 3. Ledger als Single Source of Truth
Pro Entität (Kunde/Projekt/Modul) ein `_INDEX.md`-Ledger:
- **Tabelle A** = offene Punkte / Datenmapping, je Zeile mit *Status · Quelle/Beleg ·
  Offene Frage · Owner · Antwort+Datum*.
- **Tabelle B** = getroffene Entscheidungen mit Begründung + Datum.
- **Regel: im selben Arbeitsschritt abhaken.** Wer einen Punkt klärt, trägt die
  Antwort sofort in A ein; wer entscheidet, in B. Themen-Notizen sind nur **Belege** —
  ihr offen/erledigt-Stand lebt ausschließlich im Ledger.
- **Fakten mit Beleg** (Feldname, Datei, Datum), nie ungeprüfte Annahmen.
- **Abgrenzung zu Auto-Memory:** Claude Codes eigenes Auto-Memory (`~/.claude/projects/.../memory/`)
  ist maschinenlokal und nicht git-tracked — es ergänzt den Ledger (Pointer, persönliche
  Arbeitspräferenzen), ersetzt ihn aber nicht. Bei Widerspruch gewinnt der Ledger.

Ergebnis: kein Re-Derive, keine Doppelfragen, kein veralteter Status.

## Das Drift-Gate (warum es hart ist)

„A stale wiki is worse than no wiki." `check_index.py` erzwingt deshalb maschinell:
1. **Vollständigkeit (hart)** — jede Datei im Bereich ist im `_INDEX.md` gelistet.
   Der Index darf nicht hinter dem Ordner herhinken.
2. **Pfad/Anker (hart)** — jeder konkrete Pfad/Anker im Index zeigt auf ein echtes Ziel.
3. **Staleness (advisory)** — `last-reviewed` + `shelf-life-days` im Frontmatter;
   überfällige Indizes werden gewarnt (nicht geblockt).

Ins `make check` / pre-commit / CI einhängen — dann kann der Index nicht still verrotten.

## Wie ein Agent das Repo betritt (Lese-Reihenfolge)

1. `GOI_DOKTRIN.md` (wie wird gearbeitet) → `CLAUDE.md` (Projekt-Regeln + Routing).
2. Aufgabentyp bestimmen → passenden Bereich `_INDEX.md` öffnen → „lies-wenn"-Zeile
   folgen → genau die 1–2 verlinkten Detail-Docs lesen.
3. Bei Entitäts-Arbeit: zuerst das Entitäts-Ledger lesen (was ist schon entschieden?).
4. Beim Abschluss: Ledger im selben Schritt nachziehen, Index-Gate grün halten.

Mehr Disziplin, weniger Tokens, kein Status-Chaos — das ist der ganze Trick.

## Wirkungsnachweis (ehrlich: nicht sauber gemessen)

Der Fable-5-Review (2026-07-04, `CUT_PLAN_v3.2.md`) hat explizit offengelassen, ob sich der
Gesamt-Prozessumfang (~2.400 LOC Mechanik für einen Solo-Betrieb über ~7 Repos) amortisiert —
weder Prior Art noch eine eigene Messung belegen das. Eine saubere Vorher/Nachher-Messung
(Sessions-Stichprobe über 2 Wochen, mit/ohne Index-Routing, gelesene Dateien/Tokens pro Task)
ist **nicht** durchgeführt worden — das würde echte, über Zeit verteilte Arbeitssessions in
mehreren Repos brauchen, keine einzelne Sitzung.

Ein anekdotischer, nicht belastbarer Datenpunkt aus der Praxis: beim Aufbau von
`powerbi-theme/tools/_INDEX.md` (14 Python-Module) genügte das „lies-wenn"-Routing, um bei
Folgeaufgaben gezielt 1-2 Dateien zu lesen statt den ganzen `tools/`-Ordner zu scannen — aber
ein einzelnes Beispiel ist kein Beweis, nur eine Beobachtung. **Die Annahme bleibt Annahme**,
bis eine echte Messung existiert oder das Kit aufgrund gegenteiliger Erfahrung verschlankt wird.
