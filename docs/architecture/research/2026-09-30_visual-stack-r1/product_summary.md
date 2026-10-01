# R1c Produkt-Dashboards und Design-Systeme — Zusammenfassung (30.09.2026)

51 Einträge in `product.yaml`, davon 49 aus gelesenen Primärdateien (Quellcode oder Doku im
GitHub-Repo des Systems bzw. Microsoft Learn/Apple), 2 nur als Suchauszug (`retrieval: search_excerpt`).

## Wichtigste Erkenntnisse
- **Der „moderne“ Look ist im Code messbar, nicht nur im Adjektiv:** Karte = 1-px-Rahmen +
  kaum sichtbarer Schatten (shadcn `shadow-sm`, Tremor `shadow-xs`), Radius 8–14 px, 24 px Innenabstand,
  Chart ohne vertikale Gitterlinien, Tooltip als Mini-Karte mit tabular-nums, Sparklines ohne Achsen/Tooltip.
- **Fluent unterscheidet sich im Mechanismus:** Karte `filled` trägt Schatten (shadow4, Hover shadow8)
  und *keinen* sichtbaren Rahmen; Radien klein (4–8 px); Padding 12 px; Zahlenschrift Bahnschrift
  (`fontFamilyNumeric`). Power BI hat Fluent 2 als Basisthema (GA der modernen Defaults: August 2026).
- **Dunkelmodus ist eine eigene Palette, kein Invertieren:** shadcn tauscht alle fünf Chart-Farbtöne;
  Carbon invertiert nur sequenzielle Skalen; Fluent-Semantik hat eigene Dunkelwerte.
- **Farbanzahl stark verschieden:** shadcn 5, Tremor 9, Carbon 14 (plus gruppierte 1–5er), Fluent 40.
  Für Cockpits relevant: Carbons *gruppierte* Paletten bei bekannter Kategorienzahl.
- **Interaktion:** Hover dimmt Nicht-Fokus auf 30 % (Carbon Legende, Tremor Linien — unabhängig
  übereinstimmend); Power BI: Cross-Filter/-Highlight als Default, Drill standardmäßig ohne Wirkung auf
  andere Visuals; Vercel: Filterzustand in die URL.
- **Motion:** Fluent 50–500 ms, normal 200 ms; Carbon Transitions 300 ms/Hover 100 ms; Tremor schaltet
  Datenanimation ganz ab; Material 3 nutzt Federn statt Dauern. Office-Leitlinie: Achsen vor Daten animieren.
- **Lade-/Leerzustände:** Skeleton erst nach 150–300 ms, mind. 300–500 ms sichtbar, layoutgleich (Vercel);
  shadcn liefert eine eigene `Empty`-Komponente (Icon, Titel, Text, Aktion).

## Widersprüche zwischen Quellen
- Legendenposition: Carbon unten, Office/Fluent oben links, Tremor rechts.
- Rahmen vs. Schatten: shadcn/Tremor Rahmen-primär, Fluent Schatten-primär (outline-Variante ohne Schatten).
- Kontrastmodell: Vercel/Radix APCA (Lc 60/90), Power BI WCAG 2.1 4.5:1. Für Kundenabnahme gilt WCAG.
- Linien: Power BI Fluent 2 glättet Linien standardmäßig; Carbon verbietet Interpolation über Lücken —
  Glättung verfälscht Zwischenwerte (eigene Folgerung, `inferred`, nicht in einer Quelle so formuliert).

## Lücken (nicht belegt, bewusst nicht erfunden)
- **Egress-Sperren:** ui.shadcn.com, tremor.so, vercel.com/geist, carbondesignsystem.com,
  fluent2.microsoft.design, m3.material.io/material.io, atlassian.design, lightningdesignsystem.com,
  radix-ui.com, docs.stripe.com, linear.app, jsdelivr/unpkg. Umgangen über GitHub-Quellen, wo vorhanden.
- **Vercel Geist:** Materials/Typography-Seiten nicht lesbar; nur Web Interface Guidelines (Vercel Labs).
  Der verbreitete „shadow-as-border“-Wert stammt aus Drittquellen und ist nicht aufgenommen.
- **Fluent 2 Charts-Leitlinien** (fluent2.microsoft.design) und die **Hex-Werte der Power-BI-Fluent-2-Palette**
  fehlen; Fluent-Chart-Dunkelwerte für color1–5 nicht im Quelltext gefunden.
- **Material 3 Datavis:** keine M3-Datavis-Seite erreichbar; M2-Leitlinie gesperrt. Nur Motion-Token.
- **Salesforce SLDS, Stripe, Atlassian-Tokenwerte:** nicht abrufbar; Atlassian und Linear nur Suchauszug.
- **Carbon-Hexwerte:** nur die ersten vier aus Suchauszug (#6929c4, #1192e8, #005d5d, #9f1853).
- **Dribbble/Behance:** nicht ausgewertet — keine Primärquelle; auf Wunsch als Sekundärrunde.
- Bento-Grids: keine Primärquelle nennt Bento-Regeln; nur shadcn 1→2→4 Spalten mit Container-Queries.

## Offene Fragen
- Soll `fluent` WCAG 4.5:1 und `modern_product` zusätzlich APCA prüfen, oder beide nur WCAG?
- Fluent-2-Datenfarben der Power-BI-Basis beschaffen (Theme-Export aus Desktop 08/2026) statt raten?
- Freigabe für Proxy-Allowlist (shadcn/tremor/geist/carbon/fluent2) für eine zweite Runde?
