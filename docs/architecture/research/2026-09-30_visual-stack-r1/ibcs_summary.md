# R1a IBCS — Zusammenfassung (Stand 30.09.2026)

## Quelle
- Aktuell: **IBCS Standards Version 2.0**, freigegeben am 11.06.2026 von der IBCS Association, am selben Tag wie **ISO 24896 "Notation for business reporting"**. 1.2 (Juli 2021) ist überholt.
- 2.0 gliedert neu in **Notation** (an ISO 24896 ausgerichtet) und **Composition** statt konzeptionell/perzeptuell/semantisch. PDF 160 Seiten, >180 Abbildungen, Hrsg. Hichert/Faisst; für Mitglieder kostenlos, sonst Kauf.
- Lizenz: **CC BY-SA 4.0** (ibcs.com/creative-commons-faq).

## Zugriffsgrenze (wichtig für die Belastbarkeit)
WebFetch auf ibcs.com, iso.org-Spiegel, Wikipedia und Archive wurde vom Egress-Proxy blockiert. Alle 34 Einträge
stützen sich auf **WebSearch-Auszüge von ibcs.com-Seiten** (Feld `evidence_access: search_index`). Die Zitate
sind also Suchindex-Wortlaut und nicht gegen das Original geprüft. Alle Quellen sind `primary` (ibcs.com), eine
Sekundärquelle wurde nicht gebraucht. Die 2.0-PDF und der ISO-Text wurden nicht eingesehen.

## Wichtigste Befunde
1. **Szenarien** (UN 3.2): AC solide dunkel, PY heller solide (nur im Vergleich), PL/BU umrandet und hohl, FC schraffiert. Hex-Werte nennt die Quelle nicht, die Szenarien sind also Füllmuster und Helligkeit, keine Farben.
2. **Rot und Grün nur für Varianzen**: grün = gut, rot = schlecht gegenüber einem Ziel, nicht nach Vorzeichen. Farbe dient sonst nur der Hervorhebung. Der Befund aus dem Vorentwurf („Rot für Nicht-Abweichungen“) ist damit direkt testbar (ibcs-012, ibcs-025).
3. **Achsen nicht abschneiden** (CH 1), **gleiche Skala für gleiche Einheit** (CH 4), bei Größenunterschieden **Skalierungsindikator** (x2/x4, grauer Hintergrund) statt Achsenschnitt.
4. **Messbare Geometrie** (UN 3.1): Säule/Balken = 2/3 der Kategoriebreite für Basismaße, 1/3 für Ratios, Linien für Ratios halb so dick. Zeit horizontal, Struktur vertikal, Periodentyp über die Kategoriebreite (UN 3.3).
5. **Direktbeschriftung statt Legende** (Pflichtnotation laut Arbeitsgruppe 1.2); Werteachse und Gitternetz vermeiden; Varianzen absolut als Balken, relativ als **Pins**; positive Varianzlabels mit „+“.

## Zertifizierung und Marke
- Offizielle Zertifizierung gibt es nur für **Software** (IBCS Certified Charts/Tables: 5 Chart-Templates, davon C12 und C13 Pflicht, dazu 4 Table-Templates; nicht bestanden, wenn >30 % der Funktionen fehlen; Siegel an die Version gebunden, maximal 24 Monate bei kleinen Änderungen) und für **Personen**. Eine Zertifizierung einzelner Reports wurde **nicht gefunden**.
- Terms of use: Logos nur mit Zertifizierung, Lizenz oder schriftlicher Zustimmung. Kein Produktname mit IBCS. Nicht nahelegen, dass etwas „certified/authorized“ ist (Beispiel „powered by IBCS“).
- Folgerung (eigene Ableitung): Unsere Library darf intern ein Profil `ibcs` haben. In Kundentexten nicht „IBCS-konform/zertifiziert“ schreiben, sondern neutral („folgt der IBCS-Notation“). Rechtlich ist das nicht geprüft.

## Charttypen (Mapping in ibcs-030)
Säulen-Zeitreihe → column_time · Linie → line · gestapelte Fläche → area_stacked · Scatter → scatter · Small Multiples → small_multiples · Varianzbalken → deviation_bar · horizontaler Wasserfall → waterfall_buildup · NEU: variance_pin, waterfall_vertical_calc, multi_tier_column/bar, multi_tier_waterfall_variance, bubble, table_ibcs_variance, table_variance_bars_pins. Deny-Liste (EX 2): Torte, Tacho, Radar, Spaghetti, Ampel; Ausnahmen: Torte auf Karte, Ampel für Ja/Nein.

## Widersprüche zwischen Auszügen
- SIMPLIFY-Nummerierung: einmal „SI 1 Avoid clutter“, sonst SI 1 Avoid unnecessary components … SI 5 Avoid distracting details. Die zweite Fassung ist übernommen, `confidence: inferred`.
- „UN 3.3“: ein Auszug nennt Varianzen, die Zertifizierungs-PDF nennt „Unify time periods“. Die PDF gilt.
- Mehrere Belege stammen aus 1.1/1.2-Material (v1.1-Auszug, Arbeitsgruppen-PDFs 2018). Ob sie in 2.0 unverändert gelten, ist nicht geprüft.

## Lücken / offene Fragen
- **Die Regelnummerierung von 2.0** (Notation/Composition) wurde nicht gesehen. Die IDs SA/ST/EX/SI/CO/CH/UN stammen aus der SUCCESS-Struktur. Nur ST 1–5 ist ausdrücklich als 2.0-Composition belegt.
- Unterregel-IDs für Varianzen (UN 4.x) sowie Hervorhebungs- und Skalierungsindikatoren (UN 5.x) wurden nicht gesehen, nur die Bereichsebene.
- Nicht belegt sind: Farbwerte (Hex) für AC/PY und für Rot/Grün, das Breitenverhältnis Jahr/Monat, Abstände, Schriftgrößen, CO 4/CO 5, die Chart-Templates C02–C05.
- ISO-24896-Klauselnummern fehlen (Norm kostenpflichtig). Für einen belastbaren Test-Katalog: die 2.0-PDF beschaffen (Mitgliedschaft) und `evidence` am Original nachziehen.
- Beobachtung am Rand: Die Softwareliste von ibcs.com führt einen Eintrag „Microsoft Fabric Planning“. Den Zertifikatsstatus haben wir nicht geprüft.
