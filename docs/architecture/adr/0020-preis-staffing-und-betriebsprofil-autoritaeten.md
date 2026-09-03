# ADR-0020 — Preis, Staffing und Betriebsprofil: eine Autorität je Schicht

| Feld | Wert |
|---|---|
| Status | **Proposed** (03.09.2026) |
| Entscheider | Florian Haferkorn |
| Kontext | Zwei am selben Tag entstandene Heimaten für Nagarro-Rollen, -Sätze und -Kapazität: ADR-0019 (Accepted, gemergt am 03.09.2026 mit PR #467) und der WB-002-Austauschvertrag `consulting-operating-profile/1.0.0` |
| Betrifft | `tooling/generator/schemas/consulting_operating_profile.schema.json` · `core/engagement_profiles/nagarro_consulting.yaml` · künftig `tooling/superversion/preis_kanon_schema.yaml` und der gespiegelte `staffing.py` |
| Bezug | ADR-0019 **dieses Repos** (Preis- und Staffing-Modell) · ADR-0005 (Meridian-Vendoring, Contract-Mirror) · Workbench-Backlog WB-002/WB-009 |

> **Namenshinweis:** Es gibt zwei ADR-0019. Dieses Dokument meint durchgehend das ADR-0019
> dieses Repos. Meridians gleichnummeriertes ADR-0019 („kein Schätzmodul", §2.4 dort) ist ein
> anderes Dokument; ADR-0019 hier verweist in §4 ausdrücklich darauf.

## 1. Kontext

Am 03.09.2026 sind in diesem Repo zwei Entwürfe für dieselbe Sache entstanden, ohne
voneinander zu wissen.

**ADR-0019** (Accepted, Flo, 03.09.2026) legt den Preis-Kanon fest: Satzklasse = Rolle ×
Standort, Kostenband je Klasse, Beteiligung je Rolle und Paket, Zielmarge und Risikozuschlag
in der Mandantendatei. Werte liegen nie im Repo, sondern hinter `PREIS_KANON_MANDANTEN_DIR`.
Der Rechenkern `staffing.py` entsteht einmal in Meridian und kommt als gespiegeltes Modul
hierher. §2.4 ist ausdrücklich: kein zweiter Kalkulator in ALUCA.

**WB-002** hat parallel `consulting_operating_profile.schema.json` und
`core/engagement_profiles/nagarro_consulting.yaml` angelegt, byte-identisch gespiegelt nach
Freelancing (`Test-OperatingProfileContractParity.ps1`, SHA256 `61dd1e9f…b16477`).

Gemessen am 03.09.2026, Feld für Feld:

| Thema | ADR-0019 | Operating Profile |
|---|---|---|
| Rollen | Rolle × Standort als Satzklasse | `staffing.required_roles` |
| Preislogik | Kostenband, Beteiligung in %, r, m | `commercial.pricing_model`, `hourly_rates`, `currency` |
| Kapazität | Verfügbarkeit je Rolle aus Mandantendatei | `delivery.weekly_capacity_hours`, `planning_utilization_pct`, `parallelization_policy` |
| Werte-Sperre | `<satz>`-Platzhalter, Test gegen numerische Sätze | `customer_price_values_in_profile: false`, `hourly_rates: []` |
| Rechenkern | gespiegelter `staffing.py` | keiner benannt; WB-009 plant einen Adapter |

ADR-0019 hat vor dem Schreiben gemessen: „Gibt es hier ein Preis- oder Angebotsmodul? **Nein.**"
Der Befund war zum Messzeitpunkt korrekt und trotzdem unvollständig — die Profildateien sind
untracked und tauchen in keinem `grep` über den Commit-Stand auf. Das ist keine Nachlässigkeit,
sondern eine Eigenschaft von untracked Arbeit: sie ist für jeden anderen Strang unsichtbar.

Zwei Autoritäten für dieselben Felder driften. Nicht sofort, sondern beim ersten Angebot, das
aus der einen Quelle rechnet, während die andere etwas anderes behauptet.

## 2. Entscheidung

1. **Zwei Schichten, zwei Autoritäten, keine Überlappung.**
   - Der **Austauschvertrag** `consulting-operating-profile/1.0.0` beantwortet genau eine Frage:
     *welches Betriebsmodell gilt und welche Grenzen zieht es*. Ein-Person gegen Team, serielle
     Lieferung gegen Ressourcenplan, wo Kundendaten liegen dürfen, ob Werte im Repo stehen
     dürfen. Er ist organisationsneutral und bleibt byte-identisch mit Freelancing gespiegelt.
   - Der **Preis-Kanon** aus ADR-0019 beantwortet die andere: *was kostet es und wer liefert*.
     Sätze, Kostenbänder, Beteiligung, Zielmarge, Risikozuschlag, Lieferzeitbänder. Er wird
     nicht gespiegelt, ist nicht neutral, und seine Werte liegen außerhalb jedes Repos.
2. **Das Profil trägt keine Zahl, sondern einen Zeiger.** `commercial.hourly_rates` bleibt in
   `nagarro_consulting.yaml` leer, `customer_price_values_in_profile` bleibt `false`, und
   `commercial.authority_path` benennt ab jetzt den Preis-Kanon statt einer Prosa-Umschreibung.
   Damit ist das leere Feld kein Loch, sondern eine Zuständigkeitsaussage.
3. **Kapazität: Politik im Profil, Zahlen im Kanon.** `parallelization_policy` gehört ins Profil,
   weil sie das Betriebsmodell beschreibt und der Spiegel sie braucht. `weekly_capacity_hours`
   und `planning_utilization_pct` bleiben in diesem Repo `null` und kommen zur Laufzeit aus der
   Mandantendatei. In Freelancing dürfen dieselben Felder gesetzt sein, weil dort der Kanon im
   Repo liegt und genau eine Person beschreibt.
4. **Kein zweiter Kalkulator, auch nicht über das Profil.** WB-009 baut keinen Nagarro-Rechner.
   Es baut einen Adapter, der `staffing.py` aufruft und dessen Ergebnis an Angebot, Arbeitspakete
   und Rollenbedarf reicht. ADR-0019 §2.4 bleibt unangetastet.
5. **Der Arbeitstag gehört dem Kanon, nicht dem Profil.** ADR-0019 §7 führt „Stunden im Kern,
   8 h je Tag als Kanon-Größe" ausdrücklich als `ANNAHME, ungeprueft`. `nagarro_consulting.yaml`
   setzt dieselbe Größe heute als `delivery.workday_hours: 8` — ohne diese Kennzeichnung. Das ist
   dieselbe Zahl an zwei Orten, davon einer als offen markiert. Sie gehört in die Mandantendatei.
   Bis der Kanon steht, bleibt der Wert im Profil stehen und trägt einen Kommentar, der ihn als
   den offenen Punkt aus ADR-0019 §7 ausweist; mit dem Kanon wird er auf `null` gesetzt wie
   `weekly_capacity_hours` und `planning_utilization_pct`.
6. **Vorrang bei Widerspruch: ADR-0019 vor Manifest.** `repository-bootstrap.manifest.json` führt
   `authoritative: false` und ist ein Ausführungs-Handoff, keine Entscheidungsquelle. Wo das
   Manifest etwas anderes nahelegt, wird das Manifest nachgezogen, nicht das ADR.

## 3. Optionen erwogen

| Option | Inhalt | Warum nicht |
|---|---|---|
| Profil trägt auch die Sätze | `hourly_rates` in `nagarro_consulting.yaml` füllen | Verletzt ADR-0019 §2.3 und macht den byte-identischen Spiegel zum Preis-Leck nach Freelancing |
| Kanon ersetzt das Profil | Nur `preis_kanon_schema.yaml`, Profil streichen | Der neutrale Austauschvertrag verschwindet; Freelancing und ALUCA haben keine gemeinsame Semantik mehr und das Parity-Gate hat nichts mehr zu prüfen |
| Beides in eine Datei | Ein YAML mit Betriebsmodell und Sätzen | Eine Datei mit zwei Vertraulichkeitsklassen; die spiegelbare Hälfte zieht die nicht spiegelbare mit |
| Status quo | Beide parallel weiterführen | Genau die Drift, die dieses ADR auslöst — zwei Wahrheiten über Rollen, Kapazität und Preislogik |

## 4. Konsequenzen

- `nagarro_consulting.yaml` ändert genau ein Feld: `commercial.authority_path` zeigt auf den
  Preis-Kanon. Das JSON-Schema bleibt unverändert, der Spiegel bleibt byte-identisch, das
  Parity-Gate bleibt grün. Kein Versions-Bump auf 1.1.0 nötig.
- Bis `staffing.py` in Meridian existiert und gespiegelt ist, rechnet dieses Repo keinen Preis.
  Jede Zahl in diesem Kontext bleibt `ANNAHME, ungeprueft`.
- WB-009 im Workbench-Manifest wird von „commercial adapter" auf „Adapter auf den gespiegelten
  Rechenkern" präzisiert. Das ist eine Präzisierung, keine Scope-Erweiterung.
- Freelancing bleibt unberührt. Sein Solo-Kanon (D-198, 130/150 EUR/h) liegt weiter im eigenen
  Repo und wird von diesem ADR nicht angefasst.
- Wer ein Angebot ohne gesetztes `PREIS_KANON_MANDANTEN_DIR` erzeugen will, bekommt keinen Preis
  mit Platzhalter, sondern einen Abbruch. Das ist ADR-0019 §4 und gilt hier unverändert.

## 5. Verifikation

| Prüfung | Erwartung |
|---|---|
| `Test-OperatingProfileContractParity.ps1` (HTF-Workbench) | `Status: PARITY`, Schema unverändert |
| `python -m pytest tooling/tests/test_consulting_operating_profile.py -q` | grün, `hourly_rates` leer, `customer_price_values_in_profile: false` |
| `grep -nE "[0-9]+(\.[0-9]+)? ?EUR" core/engagement_profiles/*.yaml` | keine Zeile |
| `workday_hours` im Profil | trägt bis zum Kanon einen Verweis auf ADR-0019 §7, danach `null` |
| ADR-0019 N-4 nach Umsetzung dort | kein numerischer Satz im Kanon-Schema |
| `python scripts/check_index.py --strict` | 0 harte Befunde |

## 6. Offene Punkte

- **Formale Annahme durch Flo.** Bis dahin ist dieses ADR `Proposed` und keine Entscheidung.
- **Reihenfolge: erledigt.** PR #467 ist am 03.09.2026 gemergt; ADR-0019 liegt auf `main` und
  dieses ADR wurde gegen den gemergten Text gegengelesen, nicht gegen eine Branch-Kopie.
- **Doppelte Ledger-ID A-14** in `../_INDEX.md` §3: die Workbench-Zeile (01.09.2026) und die
  ADR-0019-Zeile (03.09.2026) tragen beide `A-14`. Ein Punkt, den zwei Zeilen adressieren, ist
  über seine ID nicht auffindbar. Dieses ADR läuft deshalb unter `A-15`. Die Doublette selbst
  ist nicht Gegenstand dieses ADR und wird separat bereinigt.
- **`authority_path` als Freitext oder Enum.** Vorschlag: Freitext belassen. Ein Enum wäre eine
  Schema-Änderung und damit ein Spiegel-Bump auf 1.1.0 für einen Gewinn, der heute nicht
  gemessen ist. `ANNAHME, ungeprueft`.
- **Ob der Verzeichnisname `PREIS_KANON_MANDANTEN_DIR` in beiden Repos gleich heißt.** Offen aus
  ADR-0019 §7 und hier nicht entschieden.
