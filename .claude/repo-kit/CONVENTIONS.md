# Kit-Konventionen — Nachschlagen, nicht Pflichtlektüre

<!-- Kit-Mechanik: wird von install.py --update-all überschrieben. Eigene Regeln gehören in CLAUDE.md. -->

Diese Datei lädt **nicht** beim Sessionstart. Sie beschreibt, wie das Kit gebaut ist, damit Claude
es bei Bedarf nachlesen kann — etwa beim Anlegen eines neuen Bereichs oder einer Entscheidung.
Vorlagen liegen neben dieser Datei unter `templates/`.

## Drift-Gate

`python3 scripts/check_index.py` prüft hart: jede Datei im Bereich ist im `_INDEX.md` gelistet,
jeder Pfad/Anker im Index zeigt auf ein echtes Ziel. Mit `--strict` (pre-commit/CI) zusätzlich:
kein ungefülltes `{{…}}` in `CLAUDE.md`, GOI, `.claude/rules/` und Indizes. Advisory: Staleness
(`last-reviewed` vs. `shelf-life-days`), Routing-Qualität, Größe des Startkontexts.

Durchsetzung: versionierter Hook `.githooks/pre-commit` (aktiv über `core.hooksPath`, den der
SessionStart-Hook in `.claude/settings.json` setzt), Stop-Hook nach Turns mit Änderungen, optional
CI (`install.py --ci`). Abschalten für eine Session: `REPO_KIT_HOOKS=0`.

## Wann welche Vorlage

- **`_MANIFEST.md` (Repo-Root):** für Pipeline-/Tool-Repos — Zweck, Datenfluss, Invarianten.
  Existiert eins, zuerst lesen.
- **ADR** (`docs/adr/NNNN-*.md`, Vorlage `_ADR.md`, Supersession-Kette in der Status-Zeile) ist
  fällig, wenn mindestens eines gilt: (a) teuer umkehrbar, (b) wirkt über ≥2 Bereiche/Repos,
  (c) ersetzt/erweitert ein bestehendes ADR, (d) ein Dritter wird das *Warum* brauchen. Sonst
  genügt eine Zeile in Ledger-Tabelle B. `/repo-kit:solution-review` prüft das vor dem Bauen.
- **`make check`:** `Makefile`-Vorlage ins Root (bzw. npm-`"check"`-Script) bündelt Gate + eigene
  Checks; der pre-commit-Hook nutzt es automatisch.
- **PII-/Geheimnis-Configs:** nur `*.example.<ext>` committen; für PII-Repos
  `scripts/check_redaction.py` als pre-commit einhängen.
- **`.gitattributes` (LF-Policy)** bei Cross-Machine/Cloud-Sync, danach `git add --renormalize .`.
- **Code-Navigation:** dateireiche Code-Bereiche bekommen ein `_INDEX.md` mit `owns: *.ts, *.sql`
  — dann hält das Gate auch die Code-Listung ehrlich. Modul-Granularität, keine Dateilisten.
- **Ein Register:** Doc-Listen leben nur im `_INDEX.md`, nie parallel in `CLAUDE.md`.

## Was in einen Index gehört — und was nicht

Nur, was der Code nicht verrät: Zweck eines Bereichs, welche Datei maßgeblich ist, was nicht
angefasst werden darf, welche Aufgabe wohin führt. Keine Inhaltsangaben, die Claude beim Öffnen
der Datei ohnehin sieht — Beschreibungen von lesbarem Code helfen nachweislich nicht
(docs/RESEARCH_2026-09.md im Kit).

Ledger-Tabelle B: Entscheidung **mit** Begründung und verworfener Alternative. Sackgassen gehören
dazu — sie sind das Wissen, das eine neue Session am teuersten wiederentdeckt.
