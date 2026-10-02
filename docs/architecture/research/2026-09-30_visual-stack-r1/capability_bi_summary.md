# Strang capability_bi: Plattformfähigkeiten jenseits des Visuals (Stand 30.09.2026)

73 Einträge in `capability_bi.yaml`: 61 über Microsoft-Learn-MCP gelesen, 12 Wettbewerber nur Suchauszug
(help.tableau.com, docs.cloud.google.com, help.qlik.com, learning.sap.com per Egress gesperrt, `evidence: null`).
25 `must_have_for_parity: true`. `pbi_status`: 43 native, 19 fabric_feature, 4 premium, 7 absent.
`cockpit_build`: 34 build_backend, 15 build_shell, 14 configure, 9 none, 1 not_possible. `user_value`,
`must_have_for_parity` und `cockpit_build` sind eigene Einschätzung. Visual-Interaktionen stehen in `interaction_pbi.yaml`.

## Paritätsbaseline je Bereich (Must-haves)

| Bereich | Must-have (IDs) | Power BI heute | Fabric-App-Cockpit |
|---|---|---|---|
| Verteilung | Abo mit PDF/PPTX (001), dynamisch je Empfänger (002), Paginated (005), PDF-Export (008), Teams (009), App/Org App (012, 013), Teilen-Links (016) | nativ, Anhang ab Premium/PPU | Org App bindet die App ein (configure); Abo, Export, Mail = eigener Backend-Job |
| Alarm/Ziele | Activator (019), Scorecards mit Check-ins (020), Statusregeln/Folgen (021) | Activator braucht Fabric-Kapazität; Scorecard-Hierarchien seit 15.04.2026 weg | Activator auf dieselben Daten konfigurieren; Zieldialog und Historie selbst bauen |
| Zeit | Kalender-TI (024), klassische TI (025), Periodenumschalter (026) | Kalender-TI in Vorschau | liegt im Semantic Model, Cockpit liefert nur den Umschalter |
| Zustand/Sprache | Zustand serialisieren (029), Format-Locale (031), UI-Sprache (033) | nativ | Zustandsspeicher in der App-DB, Intl-Formatierung im Client |
| Self-Service | Analyze in Excel (039) | nativ, Build-Recht, 2 GB | Link auf das Modell (configure) |
| Vertrauen | Endorsement (042), Sensitivity Label (043), Aktualität (044) | nativ, Label schützt nur Exporte | Metadaten per API anzeigen, Label auf eigene Exporte = offen |
| Leistung | Direct Lake on OneLake (054), Seitenlast (057) | Fabric | Modellseitig gratis, Seitenlast ist Designregel |
| Barrierefreiheit | Tab-Reihenfolge, 4.5:1 (061) | nativ, Autorenpflicht | selbst bauen |
| Navigation | Theme, Menü, Landing je Audience (073) | Org App | configure |

## Gratis vs. selbst bauen

- **Gratis in einer Org App (013, 073):** Verteilung, Audiences, Theme/Navigation, Read-and-Execute-Rechte; Org App in Teams (Fabric App darin ungeprüft).
- **Gratis über das Semantic Model:** Time Intelligence (024-026), Direct Lake (054/055), RLS, M365-Copilot (040),
  Analyze in Excel (039), Explore (038), Verified Answers (036) für Copilot außerhalb des Cockpits.
- **Selbst bauen (Backend):** Abos, PDF/PPTX-Export, dynamische Abos, Favoriten/Views, Nutzungsmetriken, Ziele;
  `exportToFile` (007) und Query Caching (056) gelten nur für Power-BI-Berichte.
- **Nicht in der Fabric App:** PowerPoint-Add-in (010) nimmt nur Power-BI-Berichte (Ableitung). Alternative: je
  Cockpit ein Zwillingsbericht/Paginated Report in derselben Org App für Abo, Druck, PowerPoint, Excel.

## Besser als Power BI (Ideen für das Cockpit)

1. Metrik als Objekt mit Vergleichszeitraum und günstiger Richtung (Tableau Pulse, 027) plus Follower-Digest (063).
2. Bedingte Zustellung "nur wenn Ergebnis/geändert" (Looker, 064): Abo wird Alarm.
3. Qualitätswarnung, die bis ins Dashboard erbt (Tableau, 048); PBI zeigt DQ nur in Purview (047).
4. Kommentar am Datenwert mit Zuweisung und Status (SAC 053, Fabric IQ Plan 052) statt am Visual (pbi-039).
5. Geteilte, benannte Leseransichten als Standard (Tableau Custom Views, 030).
6. Bursting mit Seiten-Repeatern/Triggern (Pyramid 069) und nach Datenberechtigung (SAC 068).
7. Hinweise als Daten in allen Berichten (Translytical-Muster, 023) - im Cockpit mit eigener SQL-DB naheliegend.

## Lücken und Grenzen der Baseline

- Scorecard-Hierarchien/Heatmap entfernt (022); Scorecards stehen nicht in der Org-App-Inhaltsliste (013, Ableitung).
- Q&A endet Februar 2027 (037); Copilot braucht Kapazität, ist offiziell nicht mehrsprachig (034) und in
  Germany North nicht verfügbar (035). Für den DE-Mittelstand ist Copilot kein Paritätskriterium.
- Lineage nur ab Contributor (045): Konsumenten sehen keine Herkunft im Bericht.
- Dashboards/Scorecards ohne Zeitstempel (044); Berichtslayout-Texte nicht übersetzbar (032).

## Widersprüche und offene Punkte

- Report-Abo-Anhang: 20 Seiten und unter 25 MB (001); Paginated-Abo nennt nur 25 MB (006); exportToFile 250 MB (007).
- Lizenz für dynamische Abos (002) nicht genannt; "After Data Refresh" nur indirekt belegt; "10 Sheets je Qlik-Abo"
  (067) nur aus Suchauszug.
- Offen (Ableitung, kein Beleg): Fabric App als Teams-Tab/SharePoint-Web-Part (009, 011)? Gleiche DAX-Grenzen (060)?

Bewusst nicht gemacht: Visual-Kommentare, Visual-Alarm, Bookmarks, persistente Filter, Personalize, Slicer, Mobil-
Layout (in interaction_pbi); Metric Sets (keine Learn-Seite gefunden); Publish to web/Embed für Kunden (kein
Cockpit-Szenario). Keine Commits (Vorgabe).
