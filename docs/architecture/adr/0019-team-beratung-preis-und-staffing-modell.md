# ADR-0019 — Team-Beratung: Preis- und Staffing-Modell (Rollen × Kostenband × Standort)

| Feld | Wert |
|---|---|
| Status | **Accepted** (03.09.2026, Flo: „ja ich nehme ADR-0053 und ADR-0019 an"; Meridian D-358; Proposed am selben Tag) |
| Entscheider | Florian Haferkorn |
| Kontext | Flos Vorgabe vom 03.09.2026: „Freelancing sollte auf ein 1 Personen Consulting ausgelegt sein, preislich usw. analytics-usecase-library als Nagarro Consulting." · Freelancing/Meridian D-352, D-355, D-356, **D-357** · Plan 0008 (dort) Stufe D |
| Betrifft | `tooling/superversion/` (Engagement-Achse: `engagement_guide.py`, `answers.py`, `open_questions.py`, `capacity.py`) · `tooling/superversion/preis_kanon_schema.yaml`, `preis_kanon_mandant.py` und der gespiegelte Rechenkern `vendor/meridian_dataarch/preis_kanon.py` (**nicht** `staffing.py`, siehe §5) |
| Bezug | ADR-0005 (Meridian-Vendoring, Contract-Mirror) · ADR-0014 (Org-Schicht, G5) · `PRODUCT_PLAN.md` „Team/multi-tenant/RBAC (G5)" |

## 1. Kontext

Der Preis-Kanon ist im Freelancing-Repo seit D-352 (02.09.2026) mandantenfähig geplant: ein
Mandant `freelancing` mit einer Rolle und Werten im Repo, ein Mandant `nagarro` mit mehreren
Rollen, Kostenbändern und Standorten, dessen Werte außerhalb jedes Repos liegen. D-355 hat dazu
die Beteiligung je Rolle und Paket als Prozentwert festgelegt, D-356 die Kalkulation:

```
Selbstkosten(Paket, Umfang) = Σ_k (Grundaufwand_k + Σ_t Aufwand_k,t × Menge_t) × Kostensatz_k
Preis(Paket, Umfang)        = Selbstkosten × (1 + r) × (1 + m)
```

Beide Mandanten lagen bis zum 03.09.2026 im selben Repo, in derselben Datei. Flos Vorgabe vom
03.09.2026 bindet den Mandanten an das Repo: Freelancing ist das Ein-Personen-Geschäft, ALUCA
das Team-Modell.

Gemessen in diesem Repo am 03.09.2026, bevor etwas geschrieben wurde:

| Frage | Befund | Methode |
|---|---|---|
| Gibt es hier ein Preis- oder Angebotsmodul? | **Nein.** Treffer für `preis`, `ratecard`, `rate_card` nur in `capacity.py` (Fabric-SKU-Floor, ein anderes Thema) und in den DAX-/SQL-Synthesizern | `grep -ril` über `tooling/superversion`, `core`, `docs` |
| Gibt es die Engagement-Achse, an die ein Preis andocken kann? | **Ja.** `engagement_guide.py` (Termine, Fragen, Torbedingungen), `answers.py` (Antworten zurück in die Eingaben), `open_questions.py`; siehe `tooling/superversion/_INDEX.md` Zeilen zu Klasse C | Index gelesen, Dateien vorhanden |
| Wo steht Nagarro heute im Repo? | Nur als Skalierungsbedenken: `PRODUCT_PLAN.md` „Team/multi-tenant/RBAC (G5) — the Nagarro-scale concern; customer-operable-solo first". Das ist RBAC im Studio, kein Preismodell | `grep -rn Nagarro` |
| Wo zieht Freelancing seine Grenze? | `Strategie/ICP_und_Positionierung.md` dort: „Enterprise (>1.000 MA) → Nagarro-Territorium, zu komplex für Einzelperson" | Datei gelesen |

Ein Repo, das ein Schema für ein Geschäft trägt, das es laut eigener ICP nicht führt, pflegt
totes Schema. Und die beiden Geschäfte unterscheiden sich nicht in einem Parameter, sondern in
der Kapazitätslogik: eine Person liefert Pakete nacheinander, ein Team liefert sie parallel.

## 2. Entscheidung

1. **Der Mandant hängt am Repo.** Dieses Repo trägt das Team-Modell (`nagarro`). Das
   Freelancing-Repo kennt ab D-357 genau einen Mandanten und eine Person.
2. **Struktur des Team-Modells.** Satzklasse k = Rolle × Standort (onshore, nearshore, offshore).
   Kostensatz_k = Kostenband je Rolle und Standort. Beteiligung je Rolle und Paket als
   Prozentwert (Freelancing D-355, Punkt 2). Die Formel aus D-356 bleibt unverändert; Personentage,
   die daraus entstehen, sind Kanon-Tage mit Herkunft (Paket, Rolle, Beteiligung) und dürfen im
   Angebot stehen. Zielmarge m und Risikozuschlag r stehen in der Mandantendatei.
3. **Werte nie im Repo.** Nagarro-Ratecards und Kostenbänder sind Nagarro-Daten und folgen
   derselben Regel wie Kundenmaterial: es liegt an der Nagarro-Ablage. Das Repo trägt
   das Schema mit `<satz>`-Platzhaltern und lädt Werte aus `PREIS_KANON_MANDANTEN_DIR`. Ein Test
   scheitert, sobald das Repo-Schema einen numerischen Satz trägt.
4. **Der Rechenkern wird einmal gebaut, nicht zweimal.** Er entsteht in Meridian
   (Plan 0008 D-2) und kommt hierher als gespiegeltes Modul über den bestehenden Weg
   (`MIRRORED_FILES`, `_dataarch_vendor.py`, `check_dataarch_mirror`, ADR-0005). Die
   Mandantendatei ist die einzige Eingabe, die sich je Repo unterscheidet. Kein zweiter
   Kalkulator in ALUCA (Tool-Reuse-Pflicht). *Welche Datei der Kern ist, stand hier bis zum
   03.09.2026 als `staffing.py`; die Umsetzung hat das gemessen korrigiert — §5, Zeile N-3.*
5. **Kapazität ist Team-Kapazität.** Pakete dürfen parallel laufen; der Kalender (Meridian E-1)
   rechnet hier mit Verfügbarkeit je Rolle aus der Mandantendatei, nicht mit der
   Ein-Personen-Sequenz des Freelancing-Repos.
6. **Abgrenzung zu G5.** ADR-0014 und `PRODUCT_PLAN.md` G5 betreffen Multi-Org und RBAC im
   Studio. Dieses ADR betrifft Preis und Staffing. Zwei Achsen; G5 bleibt zurückgestellt, wie
   dort notiert. Die Abweichung wird benannt, nicht geglättet: „Nagarro-scale" meinte bisher
   Mandantenfähigkeit der Software, ab jetzt zusätzlich das Geschäftsmodell der Beratung.

## 3. Optionen erwogen

| Option | Inhalt | Warum nicht |
|---|---|---|
| Beide Mandanten in Freelancing (Stand D-352 bis 03.09.2026) | `nagarro` als Schema mit Platzhaltern neben `freelancing` | Freelancing trägt ein Schema für ein Geschäft, das seine ICP ausschließt; die Kapazitätslogik ist eine andere, nicht nur ein anderer Satz |
| Ein gemeinsames Preis-Repo | Kanon-Schema in ein drittes Repo, beide lesen es | Drittes Repo für eine Datei; die Spiegel-Disziplin aus ADR-0005 deckt den Bedarf bereits |
| Nagarro-Werte einchecken | Ratecard als YAML im Repo | Fremddaten in einem privaten Repo, das nicht Nagarro gehört; dieselbe Regel wie für Kundenmaterial |
| Eigener Kalkulator in ALUCA | zweite Implementierung der D-356-Formel | Zwei Rechenkerne driften; Tool-Reuse-Pflicht, Official-First des eigenen Kerns |

## 4. Konsequenzen

- Das Freelancing-Repo verliert den `nagarro`-Block (D-357 dort). Was dieses ADR beschreibt,
  war bis zum 03.09.2026 als Ergänzung in ADR-0053 (Freelancing) geführt und steht dort jetzt
  als verschoben, nicht gelöscht.
- Angebote aus diesem Repo rechnen erst mit gesetztem `PREIS_KANON_MANDANTEN_DIR`. Ohne
  Verzeichnis meldet der Loader „Mandant nagarro: keine Werte geladen" und rechnet nicht mit
  Platzhaltern.
- Personentage erscheinen in Angeboten dieses Repos, jede Zahl mit Herkunft. Das ist kein Bruch
  mit Meridians ADR-0019 §2.4 („kein Schätzmodul"): die Tage sind Kanon-Lieferzeit ×
  Kanon-Beteiligung, keine Schätzung je Kunde.
- Bis das Schema steht, ist jede Zahl in diesem Kontext `ANNAHME, ungeprueft`.
- Der Spiegel-Sensor (`scripts/check_dataarch_mirror.py`) bekommt ein weiteres Modul, sobald
  `staffing.py` in Meridian existiert; bis dahin ändert sich an der Vendor-Fläche nichts.

## 5. Umsetzung (Aufgaben, in diesem Schritt kein Code)

| # | Wo | Was | Abhängig von |
|---|---|---|---|
| N-1 | `tooling/superversion/preis_kanon_schema.yaml` | Schema: Rollen × Standort × Kostenband, Beteiligung je Rolle und Paket, r, m, Lieferzeit-Bänder je Paket; nur `<satz>`-Platzhalter | Meridian D-1 (Schema-Form, damit beide Repos dieselbe Datei lesen) |
| N-2 | Loader neben dem Schema | liest `PREIS_KANON_MANDANTEN_DIR`; ohne Verzeichnis die Meldung oben, kein Rechnen mit Platzhaltern | N-1 |
| N-3 | `scripts/check_dataarch_mirror.py`, `_dataarch_vendor.py` | **Erledigt 03.09.2026:** `core/preis_kanon.py` in `MIRRORED_FILES` und `PUBLIC_API`, Sensor deckungsgleich (35 Dateien). **Nicht `staffing.py`** — siehe die Abweichung unter der Tabelle | Meridian D-2 |
| N-4 | Test neben N-1 | Gate: kein numerischer Satz im Repo-Schema; Angebot ohne Verzeichnis bricht ab | N-1 |
| N-5 | Engagement-Kalender | Verfügbarkeit je Rolle statt Ein-Personen-Sequenz | Meridian E-1, N-1 |

**Abweichung zu §2.4 und N-3, benannt statt geglättet (Belegpflicht R5).** Das ADR nannte
`staffing.py` als den zu spiegelnden Rechenkern. Meridians Umsetzung hat ihn woanders abgelegt,
und das ist gemessen, nicht vermutet — auf genau dem Weg, den `write_vendor` fährt (Datei
kopieren, unter Meridians Modulnamen laden), am 03.09.2026:

```
products/sales_proposal/staffing.py: ImportError: cannot import name 'preis_kanon' from 'core'
core/preis_kanon.py:                 lädt
```

`staffing.py` ist die Engagement-Schicht über dem Kern und zieht `core.preis_kanon` sowie
`products.governance_framework.delivery` nach; beide Pakete gibt es hier nicht, und ein Spiegel,
der Importe umschreibt, ist kein byte-identischer Spiegel mehr. Meridian schreibt es in derselben
Datei: „gespiegelt nach ALUCA wird der Kern, diese Schicht bleibt das Angebotsprodukt dieses
Repos." Die Entscheidung aus §2.4 bleibt damit unangetastet — ein Rechenkern, nicht zwei. Nur die
Datei heißt anders.

Zwei Folgen, beide umgesetzt:

* `MIRRORED_FILES` konnte bis dahin nur aus **einem** Meridian-Verzeichnis lesen
  (`core/dataarch_engine/blueprint`). Ein Eintrag darf seit dem 03.09.2026 sein `(Quellpfad,
  Zielname)` selbst nennen; im PIN trägt eine solche Datei ein `source`-Feld, alle anderen bleiben
  am Vorgabepfad, damit `source_path` eine echte Aussage bleibt.
* `pruefe_kanon()` steht **nicht** in `PUBLIC_API`: die Funktion erzwingt genau einen Mandanten
  `freelancing` (dortiges D-357) und wäre hier per Konstruktion rot. ALUCAs Regeln stehen in
  `preis_kanon_mandant.pruefe_mandant()`, die Formel-Regeln bleiben die des Kerns.

## 6. Verifikation (gemessen 03.09.2026)

| Zusage | Messung | Ergebnis |
|---|---|---|
| Kein Satz im Repo-Schema | `grep -nE "[0-9]+(\.[0-9]+)? ?€" tooling/superversion/preis_kanon_schema.yaml` | keine Zeile |
| dasselbe, zweite Methode | `test_das_repo_schema_traegt_keinen_satz` — semantisch über die satztragenden Felder statt über die Textsuche | keine Zahl |
| Kein Rechnen ohne Werte | `python3 tooling/superversion/preis_kanon_mandant.py check` ohne `$PREIS_KANON_MANDANTEN_DIR` | rc **2**, „KONNTE NICHT PRUEFEN" — nicht rc 0 |
| Rechnen mit Werten außerhalb des Repos | Mandant in Nagarro-Form (2 Rollen × 2 Standorte) in `tmp_path`; Kern aus dem Spiegel | 8 h + 20 h → 1620 € Selbstkosten → 2227,50 € → gerundet 2250 €, von Hand gegengerechnet |
| Personentage tragen ihre Herkunft | `personentage(m, "A1")` | Band 10–15 AT × 40 % = 4,0–6,0 AT, Herkunft nennt Paket, Band, Status und Beteiligung |
| Team statt Sequenz | `kapazitaetspruefung(m, [A1, A2])` | Fenster **15 AT parallel** gegen 23 AT seriell; zu wenig Köpfe erzeugt einen Vermerk, keine gebogene Zahl |
| Spiegel deckungsgleich | `python3 scripts/check_dataarch_mirror.py` nach `--write` | rc 0, 35 Dateien (vorher 34) |
| Bereichsindex | `python scripts/check_index.py --strict` | 0 harte Befunde |
| Testfläche | `tooling/superversion/tests/test_preis_kanon_mandant.py` · `test_dataarch_vendor.py` · `tooling/tests/test_dataarch_mirror_sensor.py` | 21 · 28 · 25 Tests grün |

## 7. Offen (Ledger in `../_INDEX.md` §3, Punkt A-16)

- Formale Annahme dieses ADR durch Flo: **erledigt 03.09.2026** (Accepted, Meridian D-358).
- Tages- oder Stundensatz in der Mandantendatei: **entschieden durch die Umsetzung, anders als
  vorgeschlagen.** Der Vorschlag war „Stunden im Kern, 8 h je Tag als Kanon-Größe". Umgesetzt ist
  die erste Hälfte — der Kern rechnet in Stunden —, die zweite entfällt: Personentage entstehen
  aus dem Lieferzeit-Band in Arbeitstagen × Beteiligung (`personentage()`), nicht aus Stunden
  geteilt durch acht. Damit gibt es keine Umrechnungskonstante, die stillschweigend falsch sein
  kann, und jede Tageszahl trägt Paket, Band und Beteiligung als Herkunft. Die Stunden je Tag
  stehen weiterhin in der Mandantendatei, aber als **Verfügbarkeit** je Rolle (`verfuegbarkeit`),
  nicht als Umrechner.
- Ob der Verzeichnisname `PREIS_KANON_MANDANTEN_DIR` in beiden Repos gleich heißt: **erledigt
  03.09.2026 wie vorgeschlagen** — derselbe Name, eine Ablage bedient beide.
- **Neu und offen:** Der Kalender (Start- und Enddatum je Paket) liegt in Meridians
  `work_items.kalender()` und ist **nicht** gespiegelt. Gemessen: das Modul zieht lazy
  `core.engagement_scope`, `beraterleitfaden`, `open_points` und `provision_day2` nach — vier
  weitere Module, davon drei Engagement-Produkte, die laut §2.4 in Meridian bleiben. ALUCA hat
  damit die **Verfügbarkeit je Rolle** und die Parallelitätsaussage, nicht die Terminierung. Ob
  der Kalender gespiegelt oder hier entlang der eigenen Achse geschnitten wird (Klasse C, wie
  `engagement_guide.py` gegenüber `beraterleitfaden.py`), ist eine eigene Entscheidung und keine
  Restarbeit an N-5.
