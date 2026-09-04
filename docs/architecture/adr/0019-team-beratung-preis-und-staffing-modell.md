# ADR-0019 — Team-Beratung: Preis- und Staffing-Modell (Rollen × Kostenband × Standort)

| Feld | Wert |
|---|---|
| Status | **Accepted** (03.09.2026, Flo: „ja ich nehme ADR-0053 und ADR-0019 an"; Meridian D-358; Proposed am selben Tag) |
| Entscheider | Florian Haferkorn |
| Kontext | Flos Vorgabe vom 03.09.2026: „Freelancing sollte auf ein 1 Personen Consulting ausgelegt sein, preislich usw. analytics-usecase-library als Nagarro Consulting." · Freelancing/Meridian D-352, D-355, D-356, **D-357** · Plan 0008 (dort) Stufe D |
| Betrifft | `tooling/superversion/` (Engagement-Achse: `engagement_guide.py`, `answers.py`, `open_questions.py`, `capacity.py`) · künftig `tooling/superversion/preis_kanon_schema.yaml` und der gespiegelte Rechenkern `staffing.py` |
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
4. **Der Rechenkern wird einmal gebaut, nicht zweimal.** `staffing.py` entsteht in Meridian
   (Plan 0008 D-2) und kommt hierher als gespiegeltes Modul über den bestehenden Weg
   (`MIRRORED_FILES`, `_dataarch_vendor.py`, `check_dataarch_mirror`, ADR-0005). Die
   Mandantendatei ist die einzige Eingabe, die sich je Repo unterscheidet. Kein zweiter
   Kalkulator in ALUCA (Tool-Reuse-Pflicht).
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
| N-3 | `scripts/check_dataarch_mirror.py`, `_dataarch_vendor.py` | `staffing.py` in `MIRRORED_FILES` und `PUBLIC_API`; Sensor deckungsgleich | Meridian D-2 |
| N-4 | Test neben N-1 | Gate: kein numerischer Satz im Repo-Schema; Angebot ohne Verzeichnis bricht ab | N-1 |
| N-5 | Engagement-Kalender | Verfügbarkeit je Rolle statt Ein-Personen-Sequenz | Meridian E-1, N-1 |

## 6. Verifikation

- `grep -nE "[0-9]+(\.[0-9]+)? ?€" tooling/superversion/preis_kanon_schema.yaml` findet keine Zeile.
- Angebot aus einem Engagement ohne `PREIS_KANON_MANDANTEN_DIR`: Abbruch mit der Meldung aus
  §4, kein Preis mit Platzhalter.
- Angebot mit einer Test-Mandantendatei außerhalb des Repos: jede Tageszahl im Text trägt
  Paket, Rolle und Beteiligung als Herkunft; Start als Bedingung, Laufzeit als Band.
- `python3 scripts/check_dataarch_mirror.py` grün, nachdem `staffing.py` gespiegelt ist.
- `python scripts/check_index.py --strict` grün (dieses ADR ist im Bereichsindex gelistet).

## 7. Offen (Ledger in `../_INDEX.md` §3, Punkt A-16)

- Formale Annahme dieses ADR durch Flo: **erledigt 03.09.2026** (Accepted, Meridian D-358).
- Tages- oder Stundensatz in der Mandantendatei: Nagarro rechnet Tage, D-356 rechnet Stunden.
  Vorschlag: Stunden im Kern, 8 h je Tag als Kanon-Größe (`ANNAHME, ungeprueft`).
- Ob der Verzeichnisname `PREIS_KANON_MANDANTEN_DIR` in beiden Repos gleich heißt oder ALUCA
  einen eigenen führt. Vorschlag: gleich, damit eine Ablage beide bedient.
