# Preview v1 — Archived

Diese Dateien waren die erste Preview-Schicht der Page Templates (statisches HTML mit inline-px-Styling).

**Archiviert:** 2026-04-24
**Ersetzt durch:** `core/templates/page_templates/preview/` (v2 — Vite + TypeScript + React, token-basiertes Grid-System, vollständig skalierbar).

Gründe fuer den Ersatz:
- Hart-codierte Pixel-Werte (fontSize, padding, Canvas-Grösse)
- Density-Toggle rein dekorativ, ohne Effekt
- Keine Responsive-Behandlung, kein Reflow bei anderer Canvas-Groesse
- Kein Build-Step, keine CI-Checks, keine Typ-Sicherheit
- Doppelte Positions-API (slotPos + absolute inline px)

Siehe `core/templates/page_templates/preview/README.md` fuer das neue System.
