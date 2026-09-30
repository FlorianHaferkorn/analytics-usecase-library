# Strang users — Nutzerbedürfnisse an Cockpit und Charts (Stand 30.09.2026)

30 Einträge in `interaction_users.yaml` (20 Primär-, 10 Sekundärquellen; 26 `from_source`, 4 `inferred`;
28 `default_on: true`). **Alle Primärseiten waren vom Egress-Proxy geblockt** (nngroup.com, arxiv.org,
tableau.com, ieeevis.org, barc.com, whu.edu, community.fabric.microsoft.com, ibcs.com u. a.); jeder
Eintrag trägt `zugang: search_index` und ist vor Test-Autorität am Original zu prüfen.

## Rangliste nach Belegstärke

### (a) Pro Chart
1. **Vergleich ungefragt** (PY/PL/FC) — Few Fehler Nr. 2, IBCS-Szenarien; users-003/-004.
2. **Zahlen hinter dem Chart als Tabelle** — Bartram et al. 2021 (Nutzer wollen die Daten „in die Hand
   nehmen“), Sharif 2021 (Screenreader: −61,48 % Genauigkeit, +210,96 % Zeit; Wunsch Tabelle/Text); users-005/-025.
3. **Excel-Export, der dem Visual entspricht** — Power-BI-Community (Matrix-Struktur und Formatierung gehen
   verloren), WHU: nur ca. 1/3 erzeugt den Bericht aus dem Dashboard; users-006/-007.
4. **Werte direkt beschriften, Tooltip nur ergänzend** — NN/g Tooltip Guidelines (sekundär), kein Hover auf
   Touch, EU-Leitfaden Direktbeschriftung; users-017/-018/-019.
5. **Aussagetitel** — SWD „Titel allein erzählen die Geschichte“, IBCS SAY; users-009.
6. **Rundung statt Scheingenauigkeit** — Few Fehler Nr. 3; users-020.

### (b) Pro Seite / Cockpit
1. **Auf einen Blick, ohne Klick, ein Bildschirm** — NN/g, Few-Definition; users-001/-002.
2. **Schnell** — BARC: langsame Abfragen häufigstes BI-Problem; NN/g 0,1/1/10 s; users-014/-015.
3. **Kommentar zu Abweichungen** — WHU: 80 % der Standardberichte kommentiert, nur 12 % mit
   Handlungsempfehlung, 8 Arbeitstage Erstellung, Controller mit Grafik am wenigsten zufrieden; users-008.
4. **Drill zum Detail ohne Experten** — Tory et al. 2021 (Abhängigkeit von Experten, Werkzeug-Flickwerk); users-022 (inferred).
5. **Aktive Filter sichtbar, Live-Filter nur < 1 s** — sekundär nach NN/g; users-016.
6. **Annotationen für Ereignisse** — 10/10 befragte Praktiker; users-024.
7. **Mobil lesbar** — Dresner 2012: 61 % kritisch/sehr wichtig (veraltet); users-026.
8. **Druck/PDF für die Sitzung** — nur abgeleitet aus WHU; users-030 (inferred).
9. **Abos/Alerts, Kommentare** — schwach belegt, `default_on: false`; users-023/-027.

### (c) Rund um die Daten
1. **Datenqualität sichtbar** — BARC Trend Monitor 2026: Rang 1, 7,9/10, n = 1.579; users-013.
2. **Prüfbarkeit / Vertrauen** — Data Guards (VIS 2024): Konsumenten brauchen Validierung, es fehlt ein Standard; users-012.
3. **Datenstand sichtbar** — Bach et al. Muster „Update Information“, wiederholte Power-BI-Anfragen; users-010.
4. **Quelle, Beschreibung, Disclaimer** — Bach et al. (144 Dashboards, 42 Muster, 8 Gruppen); users-011.
5. **Einheitliche KPI-Definitionen** — nur Praktikerquelle, keine Umfragezahl; users-028 (inferred). Deckt
   sich mit dem Golden Thread (`core/kpi_catalog/`).

## Lücken
- **Keine Stimmenzahlen** aus Power BI Ideas / Tableau Ideas (Seiten geblockt, Suche liefert keine Zahlen).
- **Persönliche Ansichten/Lesezeichen**: keine Nutzerevidenz gefunden, deshalb kein Eintrag.
- **Aktuelle Mobile-BI-Zahlen** (nach 2012) und eine Primärstudie zu Push/Alerts fehlen.
- **ICV / BARC Deutschland** zu Management-Reporting im Mittelstand nicht gefunden; WHU Controller Panel ist Ersatz.
- **„Warum hat es sich geändert?“** (automatische Erklärung) nur über Kommentar-/Annotationsbelege
  abgedeckt; keine Nutzerstudie zu Explain-Funktionen gelesen.
- Tooltip-vs.-Direktbeschriftung: keine kontrollierte Studie gefunden, nur Leitfäden.

## Widersprüche / Spannungen
- NN/g/Few (keine Interaktion, ein Bildschirm) vs. Tory/Bartram (Nutzer wollen Detail, Tabellen, Weiterverarbeitung):
  auflösbar durch Schichtung — Cockpit ohne Interaktion, jede Kennzahl mit Drillthrough und Tabellensicht.
- BARC-Prozentwerte zu BI-Problemen (18,1 % / 16,4 %) stammen aus einer älteren Befragung; Jahr ungeprüft.

## Offene Fragen
- Soll Datenqualität als eigenes Badge (users-012/-013) oder nur als Datenstand + Disclaimer umgesetzt werden?
- Wird eine druckfähige Seitenfassung (users-030) Standard, oder bleibt das paginierten Berichten vorbehalten?
- Zugang zu nngroup.com, arxiv.org, tableau.com, whu.edu freischalten, um die `search_index`-Einträge zu verifizieren?
