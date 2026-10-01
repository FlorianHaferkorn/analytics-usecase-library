# Signale: Fabric- und Power-BI-Neuerungen, die ALUCA betreffen

`deklaration.yaml` nennt die ALUCA-Artefakte, ihre Themen, Pfade und Klasse. `vorgaenge.yaml`
führt je Signal und Artefakt einen Vorgang durch den Lifecycle (triage → bewerten → entschieden
→ in_umsetzung → verifiziert → ausgerollt, oder nicht_relevant / geschlossen). Das Register mit
Signalen, Themen und Lifecycle-Regeln liegt im Freelancing-Repo unter `research/signale/` (D-623).

| Aufgabe | Befehl (aus einem Freelancing-Checkout daneben) |
|---|---|
| Was betrifft eine ALUCA-Datei? | `python3 scripts/signale.py suche --deklaration ../analytics-usecase-library/signale/deklaration.yaml --pfad products/fabric/powerbi/dist/x` |
| Neue Signale ableiten | `python3 scripts/signale.py vorgaenge ../analytics-usecase-library/signale/deklaration.yaml --fortschreiben` |
| Form prüfen | `make check-signale-aluca` (Ausgang 2 ohne ALUCA-Checkout) |

Statuswechsel: `status` setzen und eine Zeile an `verlauf` anhängen; ältere Zeilen nie ändern.
Ein Commit, der einen Vorgang erledigt, nennt die Signal-ID.
