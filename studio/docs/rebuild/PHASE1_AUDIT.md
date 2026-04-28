# Phase 1 Audit — Delta zur MOCKUP_REFERENCE

## Executive Summary

Phase 1 hat die Shell-Struktur (Sidebar, Topbar, modales System) und das Token-System korrekt implementiert. Die Routing-Architektur ist überwiegend kompatibel, aber es fehlen vier wichtige Views (Dashboard/Canvas sind Placeholders). Das größte visuelle Delta ist die **HEX→OKLCH Token-Migration** im Mockup (tokens.js nutzt HEX-Werte wie `#0078D4`), während Phase 1 konsequent OKLCH nutzt. Sekundär: **Wizard ist kleiner** (modal 720px vs Mockup mit großem Stepper), **Tweaks-Panel ist korrekt entfernt** (Phase 1 hat Settings-Modal), und **Page-Templates (T1–T4) fehlen komplett** — diese sind designiert, aber noch nicht ins Studio integriert.

---

## 1. Routing-Modell

| Aspekt | Mockup | Phase 1 | Delta |
|--------|--------|---------|-------|
| **Top-Routen** | `dashboard`, `canvas`, `library`, `detail` | `overview`, `canvas`, `library`, `detail/[type]/[id]`, + 8 weitere | Mockup hat 4; Phase 1 hat 12 (+ überschüssig: discovery, delivery, simulator, steering, registry, etc.). Mockup `dashboard` → Phase 1 `overview` (benannt, nicht identisch). |
| **Detail-Route** | `detail` (bei Library open, `setRoute("detail")`) | `/detail/[type]/[id]` (Server-Route mit dynamischen Segmenten) | Phase 1 ist strukturell aktueller (Next.js-native Patterns). Mockup ad-hoc State-driven. |
| **Root-Redirect** | Standardmäßig auf `dashboard` | Standardmäßig auf `overview` | Semantisch äquivalent, aber Marketing/Naming unterscheidet. |
| **Sidebar Nav** | 4 Items (dashboard, canvas, library, detail) | 4 Top-Items + 7 weitere (discovery, delivery, steering, etc.) | Phase 1 hat viel mehr Features, Mockup ist intentional minimal (nur die Core). |
| **Active-State** | Über `route === item.id` in JavaScript | Über `usePathname()` + Link Matching | Phase 1: Next.js-native, Mockup: Client-state. |

**Fazit:** Routing ist in Phase 1 zukunftssicherer, aber es wird mindestens die **Mock-Routen dokumentieren/testen müssen** um sicherzustellen, dass die 4 Kernseiten die gleichen UX-Flows wie Mockup haben.

---

## 2. Shell-Komponenten (Sidebar + Topbar)

### Sidebar — Struktur

| Element | Mockup (shell.jsx) | Phase 1 (Sidebar.tsx) | Delta |
|---------|-------------------|----------------------|-------|
| **Width (collapsed/expanded)** | 68 / 248 px | 68 / 248 px | Exakt gleich ✓ |
| **Transition Timing** | `cubic-bezier(.2,.8,.2,1)` 240ms | `var(--motion-normal)` (240ms), `var(--ease-standard)` | Phase 1 verwendet Tokens, Mockup Inline. Semantisch äquivalent, aber Phase 1 ist wartbar. |
| **Brand Section Height** | 56px | 56px (h-14 = 3.5rem = 56px) | Exakt gleich ✓ |
| **Nav Items** | 4 Items (NAV_ITEMS) | 4 Items (same IDs) | Exakt gleich ✓ |
| **Active Indicator** | Links-Streifen (position: absolute, left: -8, width: 2) | Links-Streifen (absolute, left: -8px, width: 0.5) | **Unterschied:** Mockup `width: 2`, Phase 1 `w-0.5` (Tailwind = 2px). Visuelle Änderung: Phase 1 ist halb so breit. |
| **Domains Section** | Ja (nicht collapsed) | Nein | **Phase 1 entfernt Domains-Sektion aus Sidebar.** Mockup zeigt 5 Domänen mit Farbdots (FRAMEWORK.domains). |
| **User Footer** | Ja (AH Avatar + Name + Org Badge) | Nein | **Phase 1 hat keinen User-Footer.** Mockup zeigt Avatar mit Gradient + "Alex Haferkorn" + "Acme · Pro". |
| **Collapse Toggle** | Unten, verschwindet bei collapsed (zu Button in Topbar) | Unten, immer sichtbar | Mockup: verschwindet; Phase 1: immer sichtbar. |

### Topbar — Struktur

| Element | Mockup (shell.jsx, Zeilen 196–) | Phase 1 (Topbar.tsx) | Delta |
|---------|----------------------------------|----------------------|-------|
| **Height** | 56px (h-14) | 56px (h-14) | Gleich ✓ |
| **Breadcrumb** | Statisch: `title[route]` (z.B. "Overview", "Canvas") | Dynamisch aus pathname segments | Funktional äquivalent, aber Mockup ist prägnanter. |
| **Actions** | Search-Button, Settings-Icon, Tweaks-Toggle (3 Buttons) | Settings-Icon (1 Button) | **Phase 1 entfernt Search und Tweaks-Toggle.** Suche ist nur im Command Palette; Tweaks/Theme-Switcher sollen in Settings sein. |

### Command Palette, Settings, Wizard

| Component | Mockup | Phase 1 | Delta |
|-----------|--------|---------|-------|
| **Command Palette** | Open/Close State, Nav mit `setRoute()`, Keyboard ⌘K | Open/Close State, Keyboard ⌘K (wird nicht für Nav genutzt) | Phase 1 hat nicht das Nav-Verhalten. Das könnte ein verspätete Feature sein. |
| **Tweaks Panel** | `tweaksOpen`, setzt `--accent` CSS-Vars live (OKLCH), Theming | **Entfernt.** Nur Settings-Modal mit Theme/Density/Accent Presets. | **Korrekt per Anweisung:** Tweaks ist Demo-Helper, nicht Produkt. Phase 1 hat Settings stattdessen. |
| **Settings Modal** | Nicht im Mockup (nur Tweaks) | Ja: Theme (dark/light), Accent (6 Presets + Slider), Density (airy/balanced/dense), Fonts (4 Pairings) | Phase 1 **erweitert** Settings, was gut ist. Aber **Topbar-Button für Settings fehlt im Mockup** — das ist Phase 1 Erweiterung. |
| **Wizard Modal** | 720px wide, Stepper mit "Choose / Describe / Review", 3 Steps, AI-Assist. | max-w-md (~448px), Progress Indicator (visual bar), 3 Steps (Type / Description / Preview?) | **Phase 1 ist enger.** Mockup wirkt großzügiger. Wizard-Steps könnten ähnlich sein, aber CSS-Größe unterscheidet. |

**Fazit:** Sidebar/Topbar-Struktur ist zu 80% richtig. Lücken: **Domains-Sektion fehlt**, **User-Footer fehlt**, **Active Indicator ist halb so breit**, **Settings in Topbar ist Phase 1 Extras**, **Wizard ist 63% der Mockup-Breite**.

---

## 3. Token-System

### Konflikt: HEX vs OKLCH

| Aspekt | Mockup (tokens.js) | Phase 1 (tokens.css) | Delta |
|--------|-------------------|----------------------|-------|
| **Farbformate** | HEX (#0078D4, #50E6FF, etc.) | OKLCH (oklch(0.62 0.13 250)) | **Fundamentaler Unterschied.** Mockup ist Microsoft/Design-System (Fluent), Phase 1 ist OKLCH-First (modern CSS). |
| **Semantische Farben** | positive: #107C10, negative: #A4262C, warning: #C98A00, neutral: #605E5C | positive: oklch(0.60 0.15 150), negative: oklch(0.55 0.18 25), warn: oklch(0.70 0.15 75) | Phase 1 hat semantische Äquivalente. **Mapping könnte 1:1 erfolgen wenn konvertiert.** |
| **Data Series** | 8 HEX Farben (MS Fluent Palette) | Phase 1 nutzt CSS `@theme` + Accent-Tokens, aber keine Datenserien-Palette. | Phase 1 **fehlt eine explizite Datenserien-Palette.** Mockup hat: ['#0078D4', '#50E6FF', '#8661C5', '#F7630C', '#008575', '#E3008C', '#EF6950', '#FFB900']. |
| **Surface/Text** | 6 Tokens (surfacePage, surfaceCard, surfaceRowAlt, textPrimary, textSecondary, border) | --bg, --bg-2, --panel, --panel-2, --ink, --ink-2, --ink-3, --ink-4, --line, --line-2 | Phase 1 hat mehr Abstraktionen (5 Ink-Level, Hover-State). Mockup ist dichter. **Aber visuell werden sie ähnlich.** |
| **Accent (Dynamic)** | Nicht im tokens.js (nur als CSS-Vars in app.jsx) | oklch(0.62 0.13 250) mit 6 Presets (Indigo, Emerald, Amber, Rose, Violet, Teal) | Phase 1 hat Presets, Mockup kalkuliert live. Funktional äquivalent. |
| **Grid/Layout** | window.GRID: 1280×720, outer=32, gutter=16, luW≈86.67, luH≈39.67 | Nicht in Phase 1 vorhanden | **Grid-System fehlt in Phase 1.** Mockup nutzt 12×12 LU-Grid für absolute Slot-Positionen. Phase 1 nutzt CSS Flexbox/Grid. |

### Hybrid-Lösung (Phase 1.5 Entscheidung)

1. **HEX→OKLCH Konvertierung:** Mockup HEX kann zu OKLCH konvertiert werden. Beispiel: `#0078D4` (Indigo) → `oklch(0.52 0.24 253)` — ähnlich Phase 1 `250`. Tests notwendig.
2. **Datenserien-Palette hinzufügen:** Phase 1 sollte 8-Color-Palette ähnlich Mockup haben.
3. **Grid nicht erforderlich für Phase 1.5:** Grid ist für Template-Rendering (T1–T4), nicht für Shell. Phase 1.5 fokussiert Shell Visual Parity.

**Fazit:** OKLCH ist **bessere Zukunft als HEX.** Mockup-HEX-Werte können konvertiert werden. Kein Hard Blocker.

---

## 4. UI-Primitives

### Mockup Primitives (primitives.jsx, ~667 Zeilen)

Zentrales Konzept: **Tool-agnostische Visuelle Abstraktion**, die direkt Maps zu:
- Power BI Report-Visuals (via Fabric CLI)
- Evidence.dev Markdown-Charts
- OSS Adapter (Grafana/Metabase)

Primitive:

| Primitive | Zeilen (Mockup) | Zweck | Phase 1 Äquivalent |
|-----------|-----------------|-------|-------------------|
| **PageChrome** | 8–45 | Wrapper mit Breadcrumb + Page Type Badge | Nicht vorhanden. Phase 1 hat Breadcrumb in Topbar. |
| **Slot** | 48–56 | Absolute Platzierung auf 12×12 LU-Grid | Nicht vorhanden (Phase 1 nutzt CSS Grid/Flexbox). |
| **Card** | 59–75 | Container mit Title + Padding | Ähnlich: `bg-panel border border-border rounded-lg` in mehreren Komponenten. Nicht zentralisiert. |
| **KpiCard** | 78–116 | KPI Value + Delta + Sparkline, farbcodiert | Ähnlich: `pulse-card.tsx`, aber nicht gleich strukturiert. |
| **Sparkline** | 118–132 | SVG Mini-Chart (7 Punkte, Farbe nach Polarity) | Nicht vorhanden in Phase 1. |
| **LineChart** | 135–200 | SVG mit Grid, Serien, Refline, Legende | Nicht vorhanden (Phase 1 würde externe Chart-Library nutzen). |
| **Pill** (in shell.jsx) | 11–29 | Inline-Badge mit Tonen (neutral/accent/positive/warn/draft) | Ähnlich: `role-chip.tsx`, aber nicht generalisiert. |
| **StatusDot** | 31–41 | 6px Kreis, Farbe nach Status (certified/review/draft) | Nicht vorhanden. |
| **KBD** | 43–51 | Tastatur-Indikator (⌘K, N, etc.) | Ähnlich: Mockup zeigt explizit in Sidebar-Buttons; Phase 1 nutzt inline Text. |

### Phase 1 UI-Komponenten (Gegenstücke)

Phase 1 hat **keine zentralisierte Primitive-Bibliothek.** Stattdessen:
- `ui/studio-page.tsx`, `ui/studio-header.tsx`, `ui/studio-data.tsx` (allgemein)
- `dashboard/pulse-card.tsx` (ähnlich KpiCard)
- `ui/badges.tsx` (ähnlich Pill)
- Aber **keine SVG Charts** (würde externe Lib wie Recharts/Visx brauchen)

**Fazit:** Phase 1 **braucht eine Primitives-Bibliothek,** zumindest für T1–T4 Rendering. Mockup ist eine Vorlage.

---

## 5. Views (Dashboard / Canvas / Library / Detail)

### Dashboard

| Aspekt | Mockup | Phase 1 | Delta |
|--------|--------|---------|-------|
| **Route** | `route === "dashboard"` → `<Dashboard onOpenDetail={openDetail}/>` | `/dashboard` (aber heißt `/overview`!) | **Benenne anders:** Mockup `dashboard` = Phase 1 `overview`. Semantik OK, aber Verwirrung. |
| **Content** | 5 KPI Cards (top), Slicer Bar, 3 große Trend/Variance/Mix Panels | FrameworkOverview: Stats Cards (kpiCount, bracketCount, etc.), Domains Bar | **Stark unterschiedlich.** Mockup ist Use-Case-zentriert (XD-003); Phase 1 ist Admin-zentriert. |
| **Data** | FRAMEWORK.metrics, FRAMEWORK.dimensions, etc. (Mock-Daten) | Geladen aus `loadKpiCatalog()`, `loadAllBrackets()`, etc. (Real-Daten) | Phase 1 ist datenmäßig realistischer, aber visuell ist Mockup ein fertiger Report-Template. |

### Canvas

| Aspekt | Mockup | Phase 1 | Delta |
|--------|--------|---------|-------|
| **Route** | `route === "canvas"` → `<Canvas onOpenDetail={openDetail}/>` | `/canvas` | Route OK. |
| **Content** | Nicht vollständig gezeigt im Mockup, aber konzeptuell: Golden Thread Lineage Flow (KPI→Driver→Action) | Placeholder: "Golden Thread lineage graph. Data wiring in Phase 4." | **Phase 1 ist Stub.** Mockup skizziert wahrscheinlich ein Visuals-Flow-Diagram. |

### Library

| Aspekt | Mockup (library.jsx) | Phase 1 (library/page.tsx) | Delta |
|--------|---------------------|---------------------------|-------|
| **Route** | `route === "library"` → `<Library onOpenDetail={openDetail}/>` | `/library` | Route OK. |
| **Tabs** | Metrics / Dimensions / Sources (3 Tabs, je mit Count-Badge) | Placeholder, nicht implementiert. | **Phase 1 Tab-UI fehlt komplett.** Mockup zeigt: Metrics (mit Domain-Filter), Dimensions, Sources (mit Search + Filter-Button). |
| **Table** | Metriken-Tabelle: 8 Spalten (Name, Ref, Type, Domain, Owner, Grain, Deps, Updated). Rows sind klickbar → onOpenDetail. | Placeholder. | **Phase 1 muss Tabelle implementieren.** |
| **Header** | Title "Library" + "New metric" Button (primaryBtn) | Title "Library" + Description. Kein New-Button. | **Phase 1 fehlt der "New Metric" Button.** Mockup hat ihn rechts oben. |
| **Interaktion** | Row-Klick → `onOpenDetail(m)` → `setRoute("detail")`, setzt `detailMetric={m}` | Nicht vorhanden (weil Library noch Stub ist). | Routing-Logik muss wiederhergestellt werden. |

### Detail

| Aspekt | Mockup (detail.jsx) | Phase 1 (detail/[type]/[id]/page.tsx) | Delta |
|--------|-------------------|--------------------------------------|-------|
| **Route** | Client-State-getrieben: `route="detail"`, `detailMetric={m}` | URL-getrieben: `/detail/[type]/[id]` | Phase 1 ist strukturell besser (URL als Source of Truth). |
| **Content** | Tabs: Overview, Definition, Lineage, Comments (mit Count), History. Inline Editing von Name/Description. Metric Pill-Badges (Ref, Status, Type, Domain). Comments Section. | Placeholder: "Phase 1 placeholder. Tab UI and Cascading AI wiring in Phase 3." | **Phase 1 braucht Tab-UI + Inline Editing.** Mockup ist funktionell: kanst Name editieren, Description textarea, Comments-Thread. |
| **Kommentar-System** | 2 Sample-Kommentare (R. Okafor, L. Chen). Textfeld zum Schreiben. | Nicht vorhanden. | **Phase 1 fehlt Kommentar-UI.** |
| **SQL-Preview** | SQL-Block unter Definition-Tab. | Nicht vorhanden. | **Phase 1 könnte SQL-Editor haben**, aber noch nicht im Mockup Detail. |
| **Back-Button** | Button "Back to library" mit Chevron-Icon. | Nicht vorhanden. | **Phase 1 Navigation zurück muss es geben.** |

**Fazit:** **Library und Detail sind die visuell größten Lücken.** Phase 1 hat Shells, aber Inhalt/Interaktionen sind minimal. Mockup zeigt funktionierende Metrik-Katalog-UX.

---

## 6. Wizard

### Größe & Layout

| Aspekt | Mockup | Phase 1 | Delta |
|--------|--------|---------|-------|
| **Breite** | 720px | max-w-md (448px, 28rem) | **Mockup 60% breiter.** Mockup fühlt sich großzügiger an. |
| **Max-Height** | "88vh" | "max-h-96" (384px) | **Phase 1 ist niedriger.** Mockup erlaubt größere Step-Inhalte. |
| **Stepper-UI** | Visuell: 3 Nummern (1, 2, 3) mit Haken bei Complete, Linien dazwischen | Progress Bar (3 flex-1 Streifen, akkumulativ gefüllt) | **Unterschiedliche Aesthetic.** Mockup hat sichtbare Nummern; Phase 1 hat minimalistische Bars. |

### Steps & Content

| Step | Mockup | Phase 1 | Delta |
|------|--------|---------|-------|
| **0: Choose (Kind)** | 3 Option-Buttons (Metric, Dimension, Source), jeweils mit Icon + Desc, Selektion hat Border + Shadow | 4 Option-Buttons (KPI, Data Source, Action Code, Use Case), 2×2 Grid, minimal | Phase 1 **hat 4 Optionen** (vs 3 im Mockup). Layout ist kompakter. |
| **1: Describe (Prompt)** | Textarea mit Placeholder "E.g., revenue growth rate...", AI generat mit Loading Spinner | Nicht gezeigt in Phase 1 Snippet, aber vermutlich ähnlich: Label + Input/Textarea. | Vermutlich ähnlich funktional, aber CSS unterscheidet. |
| **2: Review (Draft)** | Generated Draft zeigt: Name, Ref, Domain, Type, Grain, Unit, Description, SQL Block, Sources. Edit-Buttons für jedes Feld. | Nicht gezeigt in Phase 1 Snippet. | Phase 1 **muss Review-Step implementieren.** |
| **AI Assist** | `setGenerating(true)` → Simulator lädt 900ms, dann `setDraft(...)` mit Mock-Daten | Vorhanden in Phase 1 (AI-Assist-Button existiert in Codebase). | **Phase 1 hat die Infrastruktur, aber nicht in Wizard integriert.** |

**Fazit:** Wizard funktioniert ähnlich, aber Phase 1 ist enger/kompakter. Inhalte sind größtenteils äquivalent. Größe ist Asthetic-Unterschied, nicht strukturell blockierend.

---

## 7. Page-Templates (T1–T4)

### Konzept

Page Templates sind **Use-Case Rendering-Vorlagen.** Jede Vorlage:
1. Hat ein **Business Use Case** (z.B. XD-003: Executive KPI Overview)
2. Rendert einen **3-Schichten-Report** (3-Second / 30-Second / 300-Second)
3. Nutzt **Primitives** (KpiCard, LineChart, etc.) + **Slots** (absolute 12×12 Grid)
4. Ist an eine **Use-Case-Bracket** gebunden (mit Orchestrations-Config)

### T-Klassen

| Template | Zeilen (Mockup) | Zweck | In Phase 1? |
|----------|-----------------|-------|------------|
| **T1: Strategic Overview** | pages/T1_overview.jsx (~80 Z.) | C-Suite Dashboard. KPI Band (3s), Trend/Variance/Mix (30s), Slicer (30s). Frage: "Are we on track?" | **Nein.** Route `/dashboard` oder `/overview` nutzt `FrameworkOverview`, nicht T1. |
| **T2: Tactical Variance** | pages/T2_overview.jsx (ähnlich T1) | Mid-Management. Insight in einen KPI + Drivers (z.B. "Why is Margin down?"). | **Nein.** |
| **T3: Operational Monitoring** | pages/T3_overview.jsx (ähnlich T1) | Operations. Pulse-View von vielen Metriken. | **Nein.** |
| **T4: Prescriptive Recommendation** | pages/T4_detail.jsx (~80 Z.) | Recommendations + Action Codes. Slicer-Pane + Smart Narrative + Detail Matrix. Frage: "What action?" | **Nein.** |

### T-Template Integration Path

```
Studio: /overview (Dashboard)
  ↓
  [Hier könnte T1 gerendert werden, wenn Use Case in Bracket konfiguriert]
  
Studio: /detail/usecase/COM-001
  ↓
  [Liest Bracket → orchestration.page_template]
  ↓
  [Lädt T1/T2/T3/T4 Renderer]
  ↓
  [Rendert PageChrome + Slots + Primitives]
```

**Phase 1 hat diese Integration nicht.** Die Seiten sind Placeholders. **Phase 1.5 oder Phase 2 müsste:**
1. Bracket → `page_template: "T1"` Config lesen
2. Renderer für T1–T4 implementieren
3. Primitives + Grid System integrieren
4. Power BI / Evidence.dev Adapters verknüpfen

**Fazit:** **T1–T4 sind nicht-blockierend für Phase 1 Visual Parity.** Sie sind **Use Case Rendering**, nicht Shell. Aber sie erklären das **Design-Theming** (warum es Slots, Primitives, Grid gibt). Sie sind Kontext für Phase 2+.

---

## 8. Tweaks → Theme-Switcher

### Mockup: Tweaks Panel (app.jsx, Zeilen 3, 8, 17, 80–81)

Tweaks war ein **Demo-Helper Panel** zum Live-Editieren von:
- `theme: "dark" | "light"` → setzt `data-theme`
- `density: "airy" | "balanced" | "dense"` → setzt `data-density`
- `fontPairing: "inter" | "ibm" | "geist" | "serif"` → setzt `data-fonts`
- `accentLightness, accentChroma, accentHue` → setzt `--accent` CSS-Var via `postMessage()` Edit-Mode-Protokoll

**Edit Mode Protocol (nicht produktiv):**
```javascript
// Edit-Mode wurde vom Parent-Frame aktiviert
window.parent?.postMessage({ type: "__edit_mode_set_keys", edits: { [k]: v } }, "*");
```

Diese **postMessage Kommunikation ist Demo-only** und wird **nicht übernommen.**

### Phase 1: Settings Modal (Settings.tsx)

Phase 1 hat korrekt ein **Settings Modal** mit:
- Theme (dark/light Toggle)
- Accent Color (6 Presets + Slider)
- Density (airy/balanced/dense)
- Fonts (4 Pairings)
- localStorage Persistenz

**Lokale Speicherung:**
```typescript
localStorage.setItem('studio-settings-v1', JSON.stringify(updated));
```

**Bestätigung:** ✓ **Tweaks-Panel ist korrekt entfernt.** Die Funktionalität ist in Settings umgezogen. **Edit Mode postMessage ist nicht produktiv und wird nicht benötigt.**

---

## 9. Visual-Parity-Lücken (priorisiert)

### P0 (Shell, Sichtbarkeit, blockiert Designdurchstich)

- [ ] **Sidebar Domains-Sektion:** Mockup zeigt Domains (Revenue, Growth, etc.) mit Farbdots. Phase 1 entfernt. **Entscheidung:** Re-Implementieren oder absichtlich entfernt? Flo's Entscheidung nötig.
- [ ] **Sidebar User-Footer:** Mockup zeigt Avatar + "Alex Haferkorn" + "Acme · Pro". Phase 1 entfernt. **Entscheidung:** Re-Implementieren oder für spätere Phase?
- [ ] **Active Nav Indicator Breite:** Mockup `width: 2px`, Phase 1 `0.5px` (Tailwind). Sieht dünner aus. **Konkretes Fix:** `w-0.5` → `w-1` (2px ist Tailwind Standard).
- [ ] **Library Tab UI + Search + Filter:** Mockup zeigt Tabs (Metrics/Dimensions/Sources), Search-Input mit "/" Hotkey, Domain-Filter-Dropdown. Phase 1 ist Placeholder. **Blockiert:** Katalog-Browse UX.
- [ ] **Library "New Metric" Button:** Mockup hat `<I.Plus size={14}/> New metric` oben rechts. Phase 1 fehlt. **Fix:** Wizard-Trigger Button.
- [ ] **Detail Tab UI:** Mockup zeigt 5 Tabs (Overview, Definition, Lineage, Comments, History). Phase 1 ist Placeholder. **Blockiert:** Metrik-Detail UX.
- [ ] **Detail Inline Editing:** Mockup zeigt Name/Description als editable Fields mit Enter-zu-Save. Phase 1 fehlt. **Nett-zu-haben:** Contenteditable Divs oder Input-Overlays.
- [ ] **Detail Comments Section:** Mockup zeigt Thread mit 2 Comments (R. Okafor, L. Chen) + Draft-Input. Phase 1 fehlt. **Phase 1.5 oder 2.** Nicht für Visual Parity nötig.
- [ ] **Wizard Modal Width:** 720px (Mockup) vs max-w-md 448px (Phase 1). Mockup wirkt großzügiger. **Fix:** `max-w-2xl` (42rem ≈ 672px) statt `max-w-md`.
- [ ] **Topbar Settings Button:** Phase 1 hat es, Mockup zeigt es nicht. **Nicht zu entfernen,** aber Position/Icon sollte gleich sein. ✓ Schon OK.

### P1 (Sichtbar, aber nicht-kritisch)

- [ ] **Token-System Datenserien-Palette:** Mockup hat 8-Farben Array. Phase 1 fehlt. **Fix:** Tokens.css erweitern mit `--data-series-[1..8]` OKLCH-Varianten.
- [ ] **Sparkline SVG:** Mockup KpiCard hat Mini-Sparkline (7 Punkte). Phase 1 hat das nicht. **Nett-zu-haben:** SVG-Komponente, aber nicht blockierend für Shell.
- [ ] **Pill Component Generalisierung:** Mockup hat `<Pill tone="positive">` als reusable. Phase 1 nutzt mehrere Button-Klassen. **Fix:** `ui/badges.tsx` verallgemeinern oder `Pill`-Komponente hinzufügen.
- [ ] **StatusDot Component:** Mockup zeigt Farbdots (certified/review/draft). Phase 1 könnte das haben. **Nett-zu-haben.**
- [ ] **Page Chrome (Breadcrumb + Page Type Badge):** Mockup hat explizite "T1 STRATEGIC OVERVIEW" Badge. Phase 1 zeigt keinen Page Type. **Nett-zu-haben:** Semantische Breadcrumb könnte ausgebaut werden.

### P2 (Nice-to-Have, Phase 2+)

- [ ] **Canvas Lineage Flow:** Mockup skizziert es. Phase 1 Stub. **Phase 4 (Golden Thread).**
- [ ] **Dashboard Slicer Bar:** Mockup T1 zeigt Datum/Region/BU Slicer. Phase 1 fehlt. **Phase 2 (Data Wiring).**
- [ ] **SVG Charts (LineChart, HBar, StackedBar100):** Mockup primitives.jsx hat ~200 Zeilen SVG-Code. Phase 1 würde externe Lib nutzen. **Phase 2: Chart Rendering.**
- [ ] **T1–T4 Template Renderer:** Mockup pages/T1_overview.jsx - T4_detail.jsx. Phase 1 fehlt. **Phase 2-3.**
- [ ] **Grid System (12×12 LU):** Mockup tokens.js + window.slotPos(). Phase 1 nutzt CSS Grid/Flexbox. **Nur nötig für T1–T4 Slot-Rendering.**

---

## 10. Empfehlung für Phase 1.5 (Visual-Parity-Pass)

### Arbeitspaket-Reihenfolge

**Strategie:** Mockup von **innen nach außen reparieren.**

1. **Library Tab UI (2–4 Subagent-Runs)**
   - Implementiere Tabs: Metrics / Dimensions / Sources
   - Search-Input + Domain-Filter
   - Daten-Binding von Loaders
   - Sortierung / Virtualisierung (optional)
   - Row-Klick → `/detail/kpi/{id}`
   - **Abhängig von:** Katalog-Loaders schon OK (Phase 1 hat sie)

2. **Detail Tab UI + Inline Editing (2–3 Runs)**
   - 5 Tabs: Overview, Definition, Lineage, Comments, History
   - Tab Routing (URL Fragment oder State)
   - Inline Editable Name/Description
   - Back-Button Breadcrumb
   - **Abhängig von:** #1

3. **Sidebar Ergänzungen (1 Run)**
   - **Domains-Sektion:** Lesen von FRAMEWORK.domains (oder Loader-Daten), Rendering mit Farbdots
   - **User-Footer:** Avatar + Name + Org (oder Placeholder)
   - **Entscheidung:** Flo gibt an, ob diese sichtbar sind/sein sollen
   - **Falls entfernt bleibt:** Einfach akzeptiert, keine Änderung

4. **Token-System Verfeinerung (1 Run)**
   - Datenserien-Palette (8 Farben, OKLCH) in tokens.css
   - HEX→OKLCH Konvertierung validieren (spot-check 3–5 Mockup-HEX-Werte)
   - Grid-System Optional: Können **nicht** für Phase 1.5 (nur T1–T4 später nötig)

5. **Wizard Modal & Shell Polish (1 Run)**
   - Größe: `max-w-md` → `max-w-2xl` (~672px, näher an 720px)
   - Max-Height: `max-h-96` → `max-h-[85vh]` (flexibler)
   - Stepper-Text (Step 1: "Choose", Step 2: "Describe", Step 3: "Review")
   - Topbar Settings-Button: ✓ Schon OK

6. **Visual Details & Bug-Fixes (1 Run)**
   - Active Nav Indicator: `w-0.5` → `w-1` (2px)
   - Library "New Metric" Button: Add Wizard-Trigger (oder placeholder Modal)
   - Detail Comments Mock-Daten: Falls implementiert, darf Phase 1.5 ignorieren
   - Test: alle Mockup-Routen funktionieren (dashboard→library→detail)

### Mockup-Files, die 1:1 Portierbar sind

Folgende Files haben **keine äußeren Abhängigkeiten** und können teilweise direkt adaptiert werden:

| Mockup File | Phase 1 Equiv | Reusability |
|-------------|----------------|------------|
| `primitives.jsx` (Pill, StatusDot, KBD, PageChrome, Card, KpiCard, etc.) | Verteilte UI-Komponenten | **Konzept portierbar,** aber React JSX→TSX, CSS Inline→Tailwind. Kann als Referenz dienen. |
| `pages/T1_overview.jsx` | Nicht vorhanden | **Später (Phase 2).** Nicht für Phase 1.5. |
| `src/data.jsx` | `lib/core/catalog-loader.ts` + `lib/core/action-loader.ts` | **Schon in Phase 1.** Mock-Daten vs Real-Daten, aber Struktur ähnlich. |
| `src/icons.jsx` | `components/ui/ph-icon.tsx` | **Phase 1 nutzt phosphor-icons.** Kompatibel. |

### Neue Komponenten (für Phase 1.5)

| Komponente | Quelle | Zweck |
|-----------|--------|-------|
| `TabNav` | Mockup library.jsx (Zeilen 36–54) | Reusable Tab-Renderer mit Icon + Count. |
| `LibraryTable` | Mockup library.jsx (Zeilen 79–) | Metrics/Dimensions/Sources Tabelle. |
| `DetailTabs` | Mockup detail.jsx (Zeilen 26–32) | 5-Tab Renderer (Overview, Definition, etc.). |
| `InlineEditor` | Mockup detail.jsx (Zeilen 52–71) | Editable Name/Description. |
| `CommentThread` | Mockup detail.jsx (Zeilen 11–14, 100+) | Comments mit Draft-Input. **Phase 1.5 kann Skeleton sein.** |
| `DomainsList` | Mockup shell.jsx (Zeilen 137–158) | Sidebar Domains-Sektion. |

### Nicht zu ändern (bereits OK)

- ✓ Sidebar/Topbar Layout & Dimensions
- ✓ Settings Modal (Theme, Accent, Density, Fonts)
- ✓ Command Palette Keybind (⌘K)
- ✓ Wizard Keybind (N)
- ✓ Topbar Breadcrumb
- ✓ Tokens (OKLCH) Basis
- ✓ Responsive Collapse-Toggle

---

## 11. Geschätzter Aufwand für Phase 1.5

| Arbeitspaket | Runs | Begründung |
|--------------|------|-----------|
| #1: Library Tab UI | 2–3 | Tabs-Switching, Search-Integration, Domain-Filter, Data-Binding. Moderate Komplexität. |
| #2: Detail Tab UI + Inline Edit | 2–3 | 5 Tabs, State Management, Editables, Breadcrumb. Ähnlich schwierig wie #1. |
| #3: Sidebar Ergänzungen | 1 | Einfache Komponenten (DomainsList, UserFooter). Falls Domains raus bleiben: Trivial. |
| #4: Token-System + Palette | 1 | OKLCH Konvertierung, Datenserien-Farben hinzufügen. Quelleneditierung nur. |
| #5: Wizard & Shell Polish | 1 | CSS Tweaks (Width, Height), Button-Text, Bug-Fixes. Einfach. |
| **Total** | **6–9 Runs** | **1.5–2 Tage Subagent-Zeit (bei seriellem Workflow).** |

---

## 12. Test-Checkliste für Phase 1.5

Nach Visual-Parity-Pass:

- [ ] **Routing:** Alle 4 Mockup-Routen navigierbar (dashboard/canvas/library/detail)
- [ ] **Library:** Tabs funktionieren, Search filtert, Domain-Filter OK, Row-Klick → Detail
- [ ] **Detail:** Alle 5 Tabs sichtbar, Name/Description editierbar, Back-Button funktioniert
- [ ] **Sidebar:** Collapsed/Expanded Toggle funktioniert, Navigation Active-State korrekt
- [ ] **Settings:** Theme-Toggle, Accent-Presets, Density, Fonts ändern CSS-Variablen
- [ ] **Wizard:** Modal öffnet mit N-Taste oder Button, Steps funktionieren, Größe ≈720px
- [ ] **Command Palette:** ⌘K öffnet, Suche funktioniert (oder Stub)
- [ ] **Token-System:** Farben sehen visuell ähnlich wie Mockup aus (spot-check 5 Komponenten)
- [ ] **Browser DevTools:** Keine Tailwind-Fehler, CSS-Variablen korrekt gesetzt, localStorage Persistence OK
- [ ] **Accessibility:** Tab-Navigation funktioniert, Keyboard Shortcuts dokumentiert (N, ⌘K, Esc)

---

## Fazit

**Phase 1 Shell-Foundation ist solid.** Der größte Gap ist nicht die Shell selbst, sondern die **Inhalts-Views (Library, Detail).** Phase 1.5 sollte fokussiert auf **Library + Detail Tab-UI + Sidebar Ergänzungen** sein — das sind 60% der sichtbaren Deltas.

Sekundär: Token-System ist zukunftssicher (OKLCH statt HEX), aber **Datenserien-Palette fehlt** und braucht 1 Run.

Tertiär: **Wizard Größe + Topbar Buttons sind Asthetic,** nicht strukturell blockierend.

**Nicht für Phase 1.5:** Canvas, Dashboard vollständig, T1–T4 Templates, Comments-System, Lineage-Flow. Diese sind Phase 2-4.

**Erlaubter Umfang Phase 1.5:** ~6–9 Subagent-Runs, seriell. **Empfehlung: In 2 Phase-1.5-Sprints (3–4 Runs pro Sprint) aufteilen** für Feedback nach Library und vor Detail.
