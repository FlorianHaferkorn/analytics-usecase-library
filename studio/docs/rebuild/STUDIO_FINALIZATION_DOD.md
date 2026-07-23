# Studio Finalization — Soll-Ziel & A+ Definition of Done

**Status:** A+ checklist complete (2026-07-21)  
**Verifier:** `npm run build` + `npm run lint:design-system` + `npx playwright test e2e/`

### Fortschritt (Stand 2026-07-21)

| Bereich | Status |
|---------|--------|
| §1 Design System (DS-1–6) | ✅ |
| §2 Primitives (PR-1–7) | ✅ Detail + Library + Templates + Wizard footer |
| §3 Workflow (WF-1–6) | ✅ inkl. Showcase-Handoff ohne AI |
| §4 Aurora (AU-1–6) | ✅ |
| §5 Performance (PF-1–4) | ✅ lazy YAML, overview cache, dynamic GoldenThreadFlow |
| §6 Quality (QG-1–4) | ✅ build/lint + forge-walkthrough e2e |

---

## Gesamt-Soll (North Star)

**ALUCA Studio** ist eine **einheitliche Forge→Registry-Arbeitsumgebung**, in der:

1. **Ein Design System** alle interaktiven Flächen steuert (keine parallelen Button/Slicer/Spacing-Dialekte).
2. Der **Forge-Workflow** ohne Dead Ends durchläuft: Discover → Blueprint → Compose → Generate → Brand → Templates.
3. **Aurora Showcase-Daten** (Gold KPI snapshot + Brand) dort sichtbar sind, wo Zahlen und ROI gezeigt werden — klar getrennt von governed Core-Metadaten.
4. **Layout** viewport-bewusst ist: kein Doppel-Scroll, kein Panel-Overlap, responsive ab 1024px.
5. **Performance:** Blueprint cold load < 3s lokal; Generate-Liste virtualisiert oder paginiert bei >10 Items.

**A+ erreicht**, wenn alle Checkboxen in §2–§6 grün sind und ein Neuling den Forge-Pfad ohne Dokumentation in <15 Minuten schafft.

---

## §1 Design System Foundation

| ID | A+ DoD | Verify |
|----|--------|--------|
| DS-1 | `tokens.css` ist einzige Farb-/Spacing-Autorität; `tokens.ts` spiegelt Accent/Semantik 1:1 | Diff review + no conflicting defaults |
| DS-2 | `--sp-1`…`--sp-8`, `--shell-header` (56px), `--shell-sidebar` (248px) definiert und referenziert | `check_design_system.mjs` |
| DS-3 | Accent = Aurora cyan in **light und dark** (Hue 215); Settings-Hue optional overlay, nicht silent override | Visual + Settings smoke |
| DS-4 | Kein `var(--*)` auf undefined tokens in `src/` | lint script |
| DS-5 | Radius: Buttons/Inputs = `--radius-md`; Cards = `--radius-card`; keine raw `7`/`8`/`10` in Primitives | grep gate |
| DS-6 | Motion aliases: `--duration-*` = `--motion-*` in `:root` | tokens.css |

---

## §2 UI Primitives (Single API)

| ID | A+ DoD | Verify |
|----|--------|--------|
| PR-1 | Alle Seiten nutzen `StudioPage` + `StudioPageHeader` für Chrome | Route audit |
| PR-2 | Buttons nur via `StudioButton` (variant: primary/secondary/ghost/accent; tone optional) | No raw 32px button blocks outside wizard (tracked) |
| PR-3 | Segmented controls nur via `StudioSegmentedControl` | Visual parity Discover/Blueprint/Generate |
| PR-4 | Form controls nur via `studio-data` (`StudioInput`, `StudioSelect`, `StudioCheckbox`) | Route audit |
| PR-5 | `StudioWorkspaceGrid` für 2–3-Spalten-Forge-Layouts mit breakpoints | Discover/Blueprint/Generate |
| PR-6 | `StudioPage fill` height = `100dvh - shell-header - 2×pad` (kein `--h-row` drift) | No double scroll on Discover |
| PR-7 | Tote Duplikate entfernt: `shell/Sidebar`, `Topbar`, `CommandPalette`, `ui/project-selector` | grep imports = 0 |

---

## §3 Forge Workflow

| ID | A+ DoD | Verify |
|----|--------|--------|
| WF-1 | Discover draft handoff → `/blueprint?draftId=&draftYaml=` (Query erhalten) | E2E/manual |
| WF-2 | `/steering` redirect preserved search params → `/blueprint?…` | curl/browser |
| WF-3 | Generate page title/eyebrow = „Forge / Generate“ (nicht Delivery) | Visual |
| WF-4 | End-of-step CTAs: Discover→Blueprint, Compose→Generate, Generate→Brand, Brand→Templates | Buttons exist |
| WF-5 | Library, Canvas, Templates in Sidebar (Tools section) + ⌘K | Nav smoke |
| WF-6 | Catalog header ≠ „Library“ (Registry naming) | Visual `/catalog` |

---

## §4 Aurora & Data Wiring

| ID | A+ DoD | Verify |
|----|--------|--------|
| AU-1 | `AuroraBootstrap` lädt Snapshot beim App-Start; Store flag `auroraLinked: boolean` | DevTools/store |
| AU-2 | Overview Top-KPI cards zeigen Snapshot-Wert wenn `kpi_id` in snapshot | Compare JSON |
| AU-3 | Compose/Simulator Slider-Default aus Snapshot (fallback catalog) | Manual COM-002 |
| AU-4 | Blueprint ROI Preset panel: Preset oder explizite „No preset“ mit Link zu Catalog | Visual |
| AU-5 | Brand boot: `brand-spec` YAML → CSS vars on load (Settings = override only) | Theme persist |
| AU-6 | UI label „Aurora Showcase“ wo Snapshot-Daten, nicht als Production SSOT | Copy audit |

---

## §5 Performance & Loading

| ID | A+ DoD | Verify |
|----|--------|--------|
| PF-1 | Blueprint: Bracket-YAML lazy (API or client fetch per selection), nicht 20× sync read | Server timing |
| PF-2 | Generate: default selection = 0 brackets (user opts in), not 20/20 | Visual |
| PF-3 | Monaco + dagre `dynamic()` until tab/mode active | Bundle analyzer optional |
| PF-4 | `buildOverviewBundle` nicht doppelt pro Request (layout passes cache/context) | Profile optional |

---

## §6 Quality Gates

| ID | A+ DoD | Verify |
|----|--------|--------|
| QG-1 | `npm run build` green | CI local |
| QG-2 | `node tooling/check_design_system.mjs` green | script |
| QG-3 | No hydration errors on Discover/Blueprint/Generate (dev overlay clean) | Browser |
| QG-4 | `design-system-optical.spec.ts` passes (when run) | Playwright |

---

## Abnahme-Checkliste (Forge Walkthrough)

- [x] Overview → Discover → showcase extraction → Blueprint opens with draft (`Open showcase in Blueprint`)
- [x] Blueprint → select COM-002 → ROI preset for `margin.gm.pct` or Catalog link
- [x] Compose → slider shows Aurora snapshot value when linked
- [x] Generate → default selection empty (user opts in)
- [x] Brand → Templates (via `/brand` redirect to `/templates`)
- [x] Registry Catalog → „Catalog“ header (nicht Library)
- [x] Library → StudioPage + StudioInput chrome
- [x] Templates → StudioPageHeader Forge / Templates

**Automated:** `npx playwright test e2e/forge-walkthrough.spec.ts`
