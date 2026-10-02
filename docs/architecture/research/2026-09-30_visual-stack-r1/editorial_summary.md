# R1b Redaktionelle Datenvisualisierung: Zusammenfassung

56 Einträge in `editorial.yaml` (idiom 15, style 16, token 9, layout 9, selection_logic 6, interaction 1).
Jede Quelle hat eine URL. Zitate wurden per Skript normalisiert gegen die geladenen Texte geprüft (FT-PDF,
Urban-HTML, bbplot-R, Plot-Docs, Reuters-npm-Docs, ai2html.js). Einträge mit Suchindex-Vermerk haben `evidence: null`.

## Zugriffslage (wichtig für die Belastbarkeit)
- **Direkt gelesen (Primärquelle):** FT Visual Vocabulary (PDF-Poster und README über GitHub), Urban Institute
  Style Guide (index.html über GitHub raw), BBC bbplot und R-Cookbook, UK Analysis Function afcharts, Observable-Plot-Docs,
  Reuters graphics-components (npm, llm-docs), NYT ai2html.js.
- **Egress-blockiert, nur Suchindex-Auszug:** ONS Service Manual, Datawrapper Blog/Academy, storytellingwithdata,
  edwardtufte.com, Economist Medium. Diese Einträge sind im `description` markiert und vor Übernahme gegenzulesen.
- **Gar nicht belegbar:** Economist-Chart-Styleguide 2017 (PDF blockiert, auch Spiegel). Die in Sekundärquellen
  genannten Werte (#e3120b, Rechteck 40x10 px, Gitter #b7c6cf) sind **nicht** übernommen. Eintrag 054 steht auf `inferred`.

## Wichtigste Erkenntnisse
1. **Auswahllogik ist zweistufig und zweckbasiert.** FT: erst die wichtigste Datenbeziehung wählen (9 Kategorien), dann
   den Typ. ONS gruppiert Chart-Typen ebenso nach Zweck. Urban hat je Familie „When to use“ und prüft vorher, ob Text
   reicht (2 bis 3 Werte). Das passt direkt auf `purposes` → Idiom-Kandidaten. Es fehlt ein Purpose für Raum (Spatial)
   und für Ranking als eigenständige Absicht (heute in `compare_categories` enthalten).
2. **Aussagetitel sind Konsens:** BBC (kurze Feststellung + beschreibender Untertitel), ONS (Headline + statistischer
   Untertitel mit Messgröße, Geografie, Zeitraum), Urban (Hauptaussage, Qualifier in den Untertitel), SWD (Takeaway-Titel).
   Daraus folgt ein Feldpaar `headline` (Erkenntnis) + `subtitle` (Messgröße/Raum/Zeit).
3. **Direktbeschriftung mit messbaren Schwellen:** Urban ≤3 Serien, Datenlabels <10 Säulen; ONS ≥4 ähnliche Linien →
   Small Multiples; Urban ≤3 bis 4 Linien; Plot: nur Anfang/Ende beschriften, bei Überlappung filtern.
4. **Highlight-Grau:** Datawrapper („Grau ist die wichtigste Farbe“), Urban (Gelb/Magenta nur für Highlight, Referenz als
   dunklere Abstufung), FT Ranking („highlight the points of interest“).
5. **Gitter nach Achsentyp** (ONS) und **nur horizontale Hauptgitter** (BBC #cbcbcb, afcharts #d9d9d9) plus betonte
   Nulllinie (BBC #333333, size 1).
6. **Mobile:** ONS 3 bis 6 Gitterlinien, keine umbrechenden Texte; Datawrapper nummeriert Annotationen und verschiebt sie
   unter den Chart, Direktlabels werden Legende; NYT ai2html gestaltet je Breakpoint ein eigenes Artboard; FT Vertical timeline.
7. **Unsicherheit/Spannen:** FT Fan chart, Plot-Band (y1/y2), Datawrapper Range/Arrow plot, Plot Difference mark.

## Widersprüche zwischen Quellen
- **Gitter bei direkt beschrifteten Balken:** Urban: unter 10 Balken Gitter und y-Achse weglassen. ONS: Balken behalten
  Gitter auch mit Direktlabels. → Das sollte ein Stil-Pack-Parameter sein, keine globale Regel.
- **Nullbasis bei Linien:** Urban: y-Achse „should always* start at zero“ auch für Linie und Scatter. ONS: Linie und
  Scatter dürfen gekappt werden (mit 1/4 bis 1/3 Abstand). FT: Nullpflicht nur für Bar/Column, Lollipop „preferable“.
- **Legendenposition:** Urban und BBC oben, afcharts standardmäßig rechts.
- **Achsentitel:** BBC entfernt sie ganz; Urban setzt sie horizontal über das oberste Label; afcharts horizontal oben.
- **FT README vs. Poster:** Die README listet weniger Typen als das PDF. Maßgeblich ist das Poster.

## Lücken
- Economist-Parameter (Primärquelle blockiert). NYT und Reuters haben keinen öffentlichen Chart-Styleguide mit
  Zahlen; belegt sind nur Werkzeug-Konventionen (ai2html, GraphicBlock, Legend-Modi).
- ONS-Farbpalette (Hexwerte) nicht gefunden. ONS-Seiten zu Unsicherheit und Annotationen nicht lesbar.
- Datawrapper-Parameter (Schriftgrößen, Abstände) nicht belegt; nur Prinzipien.
- Zahlentypografie (Tabellenziffern, Rechtsbündigkeit) ist in keiner Primärquelle mit Zahl belegt. Urban nennt nur
  „$1M statt $1,000,000“ und zweistellige Jahre (nicht als eigener Eintrag aufgenommen).
- Tufte (Range frame, Data-Ink) und SWD nur über Suchindex; die Buchquellen sind nicht online lesbar.

## Offene Fragen
- Soll `ranking` ein eigener Purpose werden (FT trennt Ranking von Magnitude)?
- Soll Spatial ganz ausgeschlossen bleiben? Power BI, HTML und Vega-Lite könnten Choropleth und Tile-Map.
- Vor Übernahme der ONS- und Datawrapper-Werte: Zugriff über einen freigeschalteten Egress oder manuelles Gegenlesen.
