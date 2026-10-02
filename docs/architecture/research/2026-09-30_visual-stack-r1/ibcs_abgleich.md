# Abgleich alter IBCS-Katalog (R1, 34 Einträge) gegen das Original

Quelle: IBCS Standards Version 2.0, IBCS Association 2026, CC BY-SA 4.0. Neuer Katalog: `ibcs_v2.yaml`
(105 Regeln der Ebene 2 plus 4 Meta-Einträge). Ergebnis: 4 bestätigt, 27 korrigiert, 2 nicht_im_original, 1 ersetzt_durch.

| Alt-ID | Ergebnis | Neu | Kern der Abweichung |
|---|---|---|---|
| ibcs-001 | korrigiert | meta-version | Freigabedatum 11.06.2026 und „Editoren“ nicht im Original; 169 PDF-Seiten, nicht 160 |
| ibcs-002 | bestaetigt | meta-version | CC BY-SA 4.0 (S. ii, iv) |
| ibcs-003 | korrigiert | meta-iso24896 | ISO-Ausrichtung betrifft SIMPLIFY, UNIFY und CHECK; UNIFY folgt ISO Clause 4 |
| ibcs-004 | korrigiert | meta-success | Konformitätssatz „seven rules“ fehlt in 2.0; Zweiteilung Notation/Composition |
| ibcs-005 | korrigiert | SA 3.2 | Position der Botschaft regelt UN 2.1 als Organisationsstandard, nicht als Pflicht |
| ibcs-006 | bestaetigt | meta-success | ST 1–ST 5 wortgleich |
| ibcs-007 | korrigiert | meta-success | EX 1 = „Use appropriate visuals“ |
| ibcs-008 | korrigiert | meta-success | SI 1 = „Avoid unnecessary elements“ |
| ibcs-009 | korrigiert | meta-success | CO 1 „Use small elements“, CO 4/CO 5 ergänzt; CH 2 „…visual components“ |
| ibcs-010 | korrigiert | meta-success | UN 2 „Unify text elements“, UN 5 „Unify markers“ |
| ibcs-011 | korrigiert | UN 3.2 | AC „solid dark (e.g. dark gray)“, „black“ entfällt; FC umrandet und schraffiert; Stapelregel |
| ibcs-012 | korrigiert | UN 4.1 | neutral = blau; hellgrün/dunkelrot; S/W- und CVD-Ersatz; keine Farbcodes |
| ibcs-013 | bestaetigt | UN 3.1 | 2/3 bzw. 1/3 Kategoriebreite, dünne Linie = 50 % |
| ibcs-014 | korrigiert | UN 3.3 + UN 3.4 | aufgeteilt; Ausnahme Intervall-/Kardinalskalen |
| ibcs-015 | korrigiert | CH 1.1 | Ausnahme indexierte Daten, Kategorie-Labels an 100-%-Linie |
| ibcs-016 | korrigiert | CH 4.1 | + CO 5.1, CO 4.2; „Chart Templates 07/11/13“ nicht im Original |
| ibcs-017 | ersetzt_durch | UN 5.2 | x2/x4 mit grauem Grund fehlt; Skalenbänder hell (z. B. hellblau), Ausreißer-Dreiecke (UN 5.3) |
| ibcs-018 | korrigiert | UN 4.1 | Regel-ID UN 4.1 statt EX 4; Pinkopf = Minuend; Zeitreihe = senkrechte Pins |
| ibcs-019 | bestaetigt | EX 4.1 | wortgleich |
| ibcs-020 | korrigiert | EX 2.1–2.5 | Ring und Trichter ergänzt; Ausnahmen je Charttyp präzisiert |
| ibcs-021 | korrigiert | UN 2.2 | drei Titelzeilen wer/was/wann; Kennzahl fett, Einheit normal; rein beschreibend |
| ibcs-022 | korrigiert | UN 2.3 | externe Legende nur „if possible“ vermeiden; bei zwei Werteachsen zulässig |
| ibcs-023 | korrigiert | UN 2.3 | „Zertifizierungskriterien“ nicht im Original; Balken rechts/links, Segmente mittig |
| ibcs-024 | korrigiert | SI 3.1 | Gitternetz zulässig bei vielen Reihen und Small Multiples |
| ibcs-025 | korrigiert | SI 2.2 | Farbe für jede analytische Bedeutung, nicht „nur Hervorhebung“ |
| ibcs-026 | korrigiert | UN 5.1 | Ellipse blau; Differenz/Trend grün-rot-blau; Referenz-Pfeilspitzen; Referenzen paarweise |
| ibcs-027 | korrigiert | EX 1.2 | 12 Spaltentypen, Zeilentypen, Lücken B1/B2, „davon“-Zeilen, 4 Tabellentypen |
| ibcs-028 | korrigiert | UN 1.2 | max. 3/4 Ziffern; -123 oder (123); „+“ nur bei Varianzen; Einheit in Titelzeile 2 |
| ibcs-029 | korrigiert | EX 1.1 | Regel-ID EX 1.1 statt EX 5; vier Wasserfalltypen; „max 25“ nicht im Original |
| ibcs-030 | nicht_im_original | – | Templates C01–C13/T01–T04 kommen nicht vor |
| ibcs-031 | korrigiert | CO 4.2 | + CO 4.1 Overlay, CO 4.3 Extended; Tier oben (Zeit) bzw. rechts (Struktur) |
| ibcs-032 | nicht_im_original | – | Software-Zertifizierung (5 Templates, 30 %, 24 Monate) fehlt |
| ibcs-033 | korrigiert | meta-version | nur Markenhinweis (S. ii) belegt; Logo-Regeln nicht im Original |
| ibcs-034 | korrigiert | meta-zertifizierung | nur Training „Certified Analyst/Professional“ (S. 168) |

## Wichtigste inhaltliche Korrekturen

1. Regel-IDs: Varianzbalken und Pins stehen in UN 4.1 (nicht EX 4), Wasserfälle in EX 1.1 (nicht EX 5); Gruppentitel UN 2, UN 5, SI 1, EX 1, CO 1, CH 2 anders benannt.
2. Varianzfarben (UN 4.1, S. 52): drei Stufen gut/schlecht/neutral = hellgrün/dunkelrot/blau; ohne Farbe dunkel-/mittel-/hellgrau; bei Farbsehschwäche Grün → Blaugrün. Exakte Codes schreibt IBCS ausdrücklich nicht vor.
3. Szenarien (UN 3.2, S. 44–45): AC solid dunkel, PY heller solid nur im Szenariovergleich, PL/BU umrandet, FC umrandet und schraffiert (Streifen in AC-Farbe). Keine Hex- oder Graustufenwerte.
4. Varianz-Semantik doppelt kodiert (UN 4.1, S. 52–55): Füllung = Minuend (AC solid, FC schraffiert, PL umrandet), Achse = Referenz (PY solid hell, PL/BU Doppellinie).
5. Skalierung (UN 5.2, CH 4.3): Skalenbänder hell (z. B. hellblau) in gleicher Höhe, typisch Zehnerpotenz; die alte x2/x4-Logik stammt nicht aus 2.0.
6. Titel (UN 2.2, S. 29–31): drei Zeilen wer/was/wann, Kennzahl fett, Einheit normal, „&“ vs. „and“ bei Szenarien, „..“ für Spannen, keine Wertung im Titel.
7. Legenden (UN 2.3): Direktbeschriftung bevorzugt, aber kein Verbot; Positionen je Charttyp festgelegt; nur horizontale Schrift.
8. Abgelehnte Charts (EX 2): Torte und Ring (Ausnahme Karte, max. 2–3 Werte), Tacho (Ausnahme Echtzeit, alle 3 Kriterien), Radar (Ausnahme Kreisbedeutung), Trichter, Spaghetti (>3–4 Linien), Ampel (Ausnahme binär/Compliance).

## Lücken für einen automatischen Test

- Keine Farb-, Grau- oder Pixelwerte: Linienstärke, Pinbreite, Pinkopfgröße, Schraffurwinkel/-abstand, Rahmenstärke, Schriftgrößen, Ränder, Lücken B1/B2/C, Kategoriebreite je Periodentyp (Abb. UN 3.3-3 nur konzeptionell). Das Profil muss diese als eigene Token festlegen; Tests prüfen dann Relationen (AC dunkler als PY, Ratio-Breite = 1/2 absolute Breite).
- Bewertung gut/schlecht braucht ein Datenfeld je KPI (Polarität); Messgrößentypen verschiebt das Original auf ein späteres Release (UN 3.1).
- Ohne Notation im Original: Flächen-, Boxplot- und Streu-/Blasendiagramme, Bereinigungsanalysen (UN 4.4), Selektion (UN 4.3), Lupenmarker (CH 4.5).
- Schwellen fehlen: „kleine Werte“ (SI 5.1), „viele Datenpunkte“ (SI 5.3), Schriftgröße (CO 1.1).
- 32 von 105 Regeln sind nicht automatisierbar (vor allem SAY, STRUCTURE und Teile von EXPRESS/CONDENSE). Weitere 2 sind nur heuristisch per Text prüfbar.
- Vega-Lite-Grenzen: Schraffur (FC) braucht SVG-`pattern`; Doppellinien-Achse (PL-Referenz), Szenario-Dreiecke, Ausreißer-Dreiecke und Pinköpfe als eigene Layer.
- Textauszug verliert Sonderzeichen (Durchschnittszeichen, Tilde in UN 4.2/4.3); vor dem Profilbau an den Abbildungen S. 56–58 prüfen.

## Widersprüche im Original

- UN 2.4 und UN 5.1 verweisen auf „SA 4.4 Name sources and link annotations“; das Inhaltsverzeichnis trennt SA 4.4 und SA 4.5.
- EX 1.2 (S. 117) verweist auf „UN 2.3 Unify time periods…“; gemeint ist UN 3.3. SA 3.2 nennt UN 2.1 „Unify messages“.
- Legende gestapelter Balken: UN 2.3 „Center legends of stacked bar charts above the top bar“, EX 1.1 „above the top stacked bar or below the bottom stacked bar“.
- Begriff: „horizontal pin chart“ (Zeitreihe) enthält senkrechte Pins, „vertical pin chart“ waagerechte.
