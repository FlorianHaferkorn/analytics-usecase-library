# ADR-0029 — Strukturformen als zweite Familie der Visual Library

| Feld | Wert |
|---|---|
| Status | **Proposed** (12.11.2026); umgesetzt als Katalog, Auswahl und Tests, Annahme durch Florian Haferkorn offen |
| Entscheider | Florian Haferkorn |
| Kontext | Meridian Studio (Freelancing-Repo) zeigt Ontologie, Semantik, Business-Logik, Lineage und Verantwortung in 13 Beziehungsansichten mit je eigener, unbegründeter Form; Auftrag 12.11.2026: „wie wir die besten Darstellungen wählen können … ohne die Übersicht zu verlieren“ |
| Betrifft | `core/templates/page_templates/visual_library/strukturformen/` (Schema, Vokabular, Regeln, 13 Formen) · `core/templates/page_templates/visual_library/_anti_patterns.yaml` (8 Einträge) · `tooling/visual_library/strukturform.py` · `tooling/visual_library/strukturform_cases.json` · `tooling/visual_library/tests/test_strukturformen.py` · `tooling/visual_library/tests/test_data_fit.py` · `tooling/visual_library/package_skill.py` |
| Bezug | GOI §1 „Maschinenform vor Prosaform“, §3 „Anpassen vor Neubau“; ADR-0026 (Notationsprofil als zweite Achse) |

## 1. Kontext

Die Visual Library wählt zu einer Mengenfrage (Wert, Abweichung, Anteil) das Idiom und
realisiert es in vier Werkzeugspuren. Beziehungsfragen (Weg, Nachbarschaft, Wirkung,
Überblick über Strukturen) deckt sie nicht ab; `decomposition_tree` und `sankey` sind die
einzigen strukturnahen Idiome.

Gemessen am Studio-Bestand (12.11.2026, Aurora-Mandant, echte Builder- und Layoutfunktionen
über ein Node-Skript gezählt): 13 Beziehungsansichten, davon zeigen 5 dieselbe Kette KPI →
Ziel/Frage/Domäne; der Golden Thread rendert 37 Knoten auf 2550 x 374 px (7:1); die KPI-Kaskade
macht aus 15 KPIs mit 13 Wurzeln und 2 Kanten einen 2480 x 176 px breiten Streifen; der
Referenzgraph hat 143 Knoten und 251 Kanten in 14 Kantentypen, von denen keine Ansicht mehr als
einen Typ gezeichnet unterscheidet. Keine Ansicht beantwortet „Pfad von A nach B“ oder
„was hängt transitiv an X“.

Recherche 12.11.2026 in vier Feldern (Forschung, Produkte, OSS und GitHub, Business-Logik-Werkzeuge),
Ergebnis als 21 Regeln in `strukturformen/_regeln.yaml`, je mit Belegart:

| Belegart | Regeln |
|---|---|
| gemessen (Studie mit Zahl) | 7 |
| dokumentiert (Produkt-/Standarddoku, Methode, Fallstudie) | 11 |
| faustregel (Lehrbuch ohne Studie) | 1 |
| hergeleitet (eigene Einschätzung, Messung am Bestand) | 2 |

Die tragenden Befunde: Die Aufgabe entscheidet vor der Menge (Wegfrage: Node-Link in allen
Bedingungen vorn, Ghoniem 2004); Übersicht kommt aus Reduktion (Suche, Fokus, Zusammenklappen,
Bündelung mit Zähler), nicht aus dem Renderer; kein geprüftes Produkt zeigt den Gesamtgraphen als
Einstieg; 3D auf dem flachen Bildschirm ist durch keine gefundene Studie gedeckt (Vorteil nur mit
Stereo plus Kopfbewegung, Ware & Franck 1996); Kanten brauchen eine Bedeutungsklasse (DMN trennt
ausführbare von zuordnenden Anforderungen, Nørreklit 2000 kritisiert die Vermischung).

## 2. Optionen

| Option | Form | Vorteil | Nachteil |
|---|---|---|---|
| (a) Status quo | jede Ansicht wählt ihre Form selbst | keine Arbeit | Formwahl bleibt Prosa im Code, nicht prüfbar; Doppelungen bleiben |
| (b) Strukturformen als Idiome mit vier Werkzeugspuren | `<id>.yaml` neben den Idiomen | ein Katalog | Power-BI-Spuren sind für Graphen meist `applicable: false`; das Idiom-Schema würde zur Hülle |
| (c) Zweite Familie im selben Ordner, eigenes Schema, gemeinsamer Anti-Pattern-Katalog | `strukturformen/` mit Auswahlvertrag statt Werkzeugspuren | Regeln und Anti-Patterns geteilt, Auswahl testbar, Idiom-Tests unberührt | zweites Schema in der Bibliothek |
| (d) Eigener Katalog im Studio (Freelancing) | Meridian-intern | nah an der Nutzung | zwei Bibliotheken für denselben Zweck (GOI §3), ALUCA-Studio ginge leer aus |

## 3. Entscheidung (vorgeschlagen)

Option (c). Eine Strukturform ist ein Feldsatz (`strukturformen/_schema.yaml`): Strukturtypen,
primäre und sekundäre Fragen, Menge vor Reduktion, Voraussetzungen an die Daten (Masse, Zyklen,
Wurzeln, Start und Ziel), Vorrang mit begründender Regel, gleichzeitig unterscheidbare
Kantenklassen, Reduktions- und Interaktionsmuster, Technik, Textalternative, Regeln,
Anti-Patterns, optionaler Verweis auf ein Idiom (`icicle` → `decomposition_tree`,
`mengenfluss` → `sankey`).

Kantenklassen als Pflichtvokabular: `rechnet`, `beeinflusst`, `erfordert`, `zugeordnet`,
`verantwortet`, `beziehung`, je mit Darstellung (Strich, Richtung, Glyphe); der Test verlangt,
dass keine zwei Klassen gleich aussehen. Richtung als verjüngte Kante (Holten & van Wijk 2009).

`strukturform.waehle(struktur, frage, knoten, daten)` liefert die passenden Formen in fester
Reihenfolge (primäre Frage vor sekundärer, dann Vorrang, dann ID) und meldet
`filter_kantenklasse`, wenn die Daten mehr Kantenklassen tragen, als die Form unterscheidet.
Jedes der 42 Paare Struktur x Frage hat eine Form oder steht mit Grund in `ungedeckt` (9 Paare).

3D (`raum_3d`) ist nur für die räumliche Struktur zugelassen (physische Architektur) und bleibt
`experimental`; ein Test hält WebGL aus allen anderen Formen heraus.

## 4. Folgen

- Gemessen: `tooling/visual_library/tests/` 577 grün, 6 übersprungen (vorher auf `origin/main`
  59111e11: 1 rot, `test_package_skill` suchte `skills/visual-library/SKILL.md`, das 2550a314
  entfernt hatte; mit dieser Änderung korrigiert).
- Die 20 eingefrorenen Fälle kommen aus dem Studio-Bestand; sie empfehlen u. a. für die
  KPI-Kaskade die eingerückte Liste und für die Ontologie-Nachbarschaft den Ego-Graphen vor der
  Matrix. Das Studio übernimmt den Katalog über den bestehenden ALUCA-Spiegel
  (`scripts/check_aluca_mirror.py` im Freelancing-Repo), wenn diese ADR angenommen ist.
- Die Zuordnung der 14 Studio-Kantentypen auf die 6 Kantenklassen ist Studio-Sache und steht
  dort als eigener Eintrag.

## 5. Bewusst nicht entschieden

- Layout-Bibliothek (dagre, d3-dag, ELK, React Flow): offen; React Flow ist die einzige OSS mit
  dokumentierter Barrierefreiheit, berührt aber die Studio-Entscheidungen zu eigenen Layouts.
- Menschliche Doku (`render_docs.py`) für die Strukturformen: folgt nach Annahme.
- `strukturform.py` liegt nicht im Skill-Bündel (`package_skill.py` kopiert nur die YAML).
- Schwellen `menge.max` sind teils hergeleitet (Produktgrenzen Grafana 200, Lightdash unter 30);
  eine eigene Lesbarkeitsmessung bei 150 Knoten mit 14 Kantentypen steht aus.
