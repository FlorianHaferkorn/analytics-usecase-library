# Penpot Layout Design Guide

## Overview

This guide explains how to create Power BI Fabric page layouts in **Penpot**, a free, open-source alternative to Figma. Penpot designs are exported as JSON and can be used directly by the page scaffold generator to position Power BI visuals with pixel-perfect control.

Penpot is ideal for teams that want:
- **No cost** — completely open-source and free to self-host or use at penpot.app
- **No API rate limits** — full JSON export without subscription tiers
- **Web standards** — uses SVG and JSON, not proprietary formats
- **Same design workflow** — frames, components, and constraints like Figma

## Getting Started with Penpot

### 1. Create a Free Account

1. Go to [penpot.app](https://penpot.app)
2. Sign up with email or OAuth (Google, GitHub, etc.)
3. Create a new team or project

### 2. Create a New File

1. Click **"New File"** in your project
2. Name it something descriptive, e.g., `Analytics_Page_Layouts`
3. You'll be taken to the design canvas

### 3. Set Up Your Canvas

1. **Create a new page**: Right-click in the Layers panel (left side) and select **"New Page"**
   - Name it `Overview_Layouts` or `Detail_Layouts` depending on which page type you're designing

2. **Create a 1920×1080 artboard/frame**:
   - Select the **Frame tool** (keyboard shortcut: `F`)
   - On the canvas, drag to create a frame
   - In the **Design panel** (right side), set:
     - **Width**: 1920
     - **Height**: 1080
   - Name the frame something descriptive, e.g., `Main_Page_Layout`

## Naming Conventions for Layout Slots

Each visual on your Power BI page corresponds to a **named frame** in Penpot. Use these canonical slot IDs:

### Overview Page Slots

| Slot ID | Purpose | Position (pixels) |
|---------|---------|-------------------|
| `KPI_Cards` | Top KPI summary cards (1–6) | y: 32, height: 120–240 |
| `Slicer_Date` | Date/time period filter | y: 168 or after KPI_Cards |
| `Main_1` | Primary 30s chart (trend line) | y: 254+ |
| `Main_2` | Secondary 30s chart (comparison) | Right of or below Main_1 |
| `Main_3` | Tertiary 30s chart (ranking) | Right of or below Main_2 |

### Detail Page Slots

| Slot ID | Purpose | Position |
|---------|---------|----------|
| `Slicer_Pane` | Detail page filter (optional) | Top area |
| `Smart_Narrative` | Context/summary text box | After slicers |
| `Detail_Matrix` | Evidence table | Main content area |
| `ActionPanel` | Recommended actions (optional) | Right or bottom area |

### Complete Slot Registry (All Possible Slots)

```
KPI_Cards
Slicer_Date
Slicer_Entity
Slicer_Pane
Main_1
Main_2
Main_3
Focus_Area
Support_1
Support_2
Smart_Narrative
Detail_Matrix
ActionPanel
```

## Creating Layout Frames in Penpot

### Step 1: Create Named Frames

For the `pulse_asymmetric` layout example:

1. **Create KPI_Cards frame**:
   - Select **Frame tool** (F)
   - Draw a frame at x=32, y=32, width=1856, height=120
   - In the Layers panel, **double-click the frame name** and rename to `KPI_Cards`
   - Press Enter

2. **Create Slicer_Date frame**:
   - Draw at x=32, y=168, width=1856, height=70
   - Rename to `Slicer_Date`

3. **Create Main_1 frame**:
   - Draw at x=32, y=254, width=992, height=794
   - Rename to `Main_1`

4. **Create Main_2 frame**:
   - Draw at x=1040, y=254, width=432, height=385
   - Rename to `Main_2`

5. **Create Main_3 frame**:
   - Draw at x=1040, y=655, width=432, height=393
   - Rename to `Main_3`

### Step 2: Add Visual Type Hints (Optional but Recommended)

To make it explicit what type of Power BI visual goes in each slot, annotate the frame names:

**Format**: `<SLOT_ID> [<VISUAL_TYPE>]`

Examples:
- `Main_1 [lineChart]` — trend line
- `Main_2 [clusteredBarChart]` — comparison bar chart
- `KPI_Cards [cardVisual]` — summary cards

**Supported visual type hints**:
- `lineChart` — line/area chart
- `clusteredBarChart` — column/bar chart (grouped)
- `stackedBarChart` — stacked column/bar
- `waterfallChart` — waterfall
- `scatterChart` — scatter/bubble
- `funnelChart` — funnel
- `cardVisual` — KPI card
- `tableEx` — table
- `matrixVisual` — matrix
- `slicer` — filter/slicer
- `textbox` — text/narrative

To rename a frame with a type hint:
1. In Layers, **double-click the frame name**
2. Change `Main_1` to `Main_1 [lineChart]`
3. Press Enter

### Step 3: Organize Your Layout

- Place all frames inside a **parent frame** (e.g., `Main_Page_Layout`) to keep them grouped
- Use the **Alignment tools** (right panel) to snap frames to a pixel grid (e.g., 8px snap)
- Preview your layout at **100% zoom** to see pixel-perfect positioning

## Exporting Your Layout as JSON

Once your layout is complete:

1. **Click File → Export** (or keyboard shortcut: Ctrl+E / Cmd+E)
2. Select your root frame (e.g., `Main_Page_Layout`)
3. Choose format: **JSON** (not PNG or SVG)
4. Click **Download** to save `Main_Page_Layout.json` to your computer

The JSON file will contain:
```json
{
  "penpot:objects": {
    "uuid-1": {
      "name": "KPI_Cards",
      "type": "frame",
      "x": 32,
      "y": 32,
      "width": 1856,
      "height": 120,
      "children": [],
      ...
    },
    ...
  }
}
```

## Using the Exported Layout

### Option 1: Direct File Load (Recommended for Development)

1. Place your exported JSON in:
   ```
   <repo_root>/designs/penpot_exports/<file_id>_<page_id>_<frame_id>.json
   ```

2. Reference it in your `UseCase_Bracket.yaml`:
   ```yaml
   ux_layout_rules:
     layout_source: "penpot://file-id/page-id/frame-id"
     page_template: pulse  # fallback template
   ```

3. The config loader will automatically find and load the JSON.

### Option 2: Penpot Cloud API (For Production)

If you store designs in Penpot Cloud:

1. Get your Penpot API token:
   - Settings → Account → API token → Generate

2. Set environment variable:
   ```bash
   export PENPOT_API_TOKEN=your-token-here
   ```

3. Reference the design via URI:
   ```yaml
   ux_layout_rules:
     layout_source: "penpot://FILE_ID/PAGE_ID/FRAME_ID"
   ```

The config loader will fetch the design from Penpot REST API automatically.

## Available Layout Templates

The repository includes three pre-defined layout variants in `core/templates/page_templates/grid_templates/`:

### 1. pulse_asymmetric.json

**Purpose**: Diagnostic pulse — dominant trend + 2 stacked support charts

**Composition**:
- KPI Cards: 32, 32, 1856×120 (top bar)
- Slicer Date: 32, 168, 1856×70
- **Main_1 (Trend)**: 32, 254, 992×794 (52% left) — primary chart
- **Main_2 (Support)**: 1040, 254, 432×385 (right top) — secondary comparison
- **Main_3 (Support)**: 1040, 655, 432×393 (right bottom) — tertiary ranking

**Best for**: Executive dashboards where one dominant trend drives narrative (e.g., Sales Forecast vs. Actuals)

### 2. investigator_focus.json

**Purpose**: Root cause investigation — large primary chart + compact support panels

**Composition**:
- KPI Cards: 32, 32, 1856×120
- Slicer Date: 32, 168, 1856×70
- **Main_1 (Primary)**: 32, 254, 1232×794 (64% left) — large deep-dive chart
- **Main_2 (Support)**: 1280, 254, 608×385 (right top) — context chart
- **Main_3 (Support)**: 1280, 655, 608×393 (right bottom) — comparison/ranking

**Best for**: Detail pages or investigative reports where a large scatter/waterfall dominates (e.g., Order Issue Root Cause Analysis)

### 3. executive_kpi.json

**Purpose**: Strategic dashboard — tall KPI strip + large trend + compact comparisons

**Composition**:
- **KPI Cards**: 32, 32, 1856×240 (tall — 6+ cards)
- Slicer Date: 32, 288, 1856×70
- **Main_1 (Trend)**: 32, 374, 1232×674 (64%) — large executive-level trend
- **Main_2 (Support)**: 1280, 374, 608×328 (compact top)
- **Main_3 (Support)**: 1280, 718, 608×330 (compact bottom)

**Best for**: C-level dashboards with emphasis on KPI cards and high-level trends (e.g., Quarterly Business Review)

### Pixel Specifications

All templates assume a **1920×1080 canvas** (standard Power BI page size).

**Layout Rules**:
- Left margin: 32px
- Right margin: 32px (total usable width: 1856px)
- Top margin: 32px
- Gaps between sections: 8px or 16px (multiples of 8)
- All positions are absolute (not relative grids)

**Creating Your Own**:

Use the template JSON as a starting point. To create a custom layout:

1. Copy one of the above JSON files
2. Modify the `slots` array with new positions
3. Update `template_id` and `description`
4. Save as `<your_layout>.json` in `grid_templates/`
5. Reference in `UseCase_Bracket.yaml`:
   ```yaml
   ux_layout_rules:
     page_template: your_layout
   ```

## Penpot vs. Figma: Key Differences

| Aspect | Penpot | Figma |
|--------|--------|-------|
| **Cost** | Free (open-source) | $12/mo per editor |
| **Export** | Full JSON export | API (rate-limited) |
| **Standards** | SVG + JSON | Proprietary |
| **Self-hosting** | Yes | No |
| **Collaboration** | Real-time (cloud) | Real-time (cloud) |
| **Learning curve** | Similar to Figma | — |

Both tools produce equivalent absolute-position layouts. Use whichever your team prefers.

## Troubleshooting

### Issue: Frame names not recognized

**Cause**: Typo in slot ID or frame is not a Penpot frame.

**Fix**:
1. Double-click the frame in Layers
2. Verify the name matches exactly: `Main_1`, not `main_1` or `Main 1`
3. Ensure it's a **frame** (type: "frame" in JSON), not a group or component

### Issue: Layout loads but positions are wrong

**Cause**: Canvas size mismatch or frame positioned off-canvas.

**Fix**:
1. Verify your root frame is exactly **1920×1080**
2. Ensure all child frames are **inside** the root frame
3. Check that all x/y positions are positive and within bounds

### Issue: JSON export is empty

**Cause**: Wrong export format or no frames selected.

**Fix**:
1. Ensure you export as **JSON** (not PNG/SVG)
2. Select the **root frame** (containing all slots) before export
3. Try exporting from the menu: File → Export → JSON

### Issue: Visual type hints not recognized

**Cause**: Bracket syntax error in frame name.

**Fix**:
- Use square brackets exactly: `Main_1 [lineChart]`
- No spaces between slot ID and bracket: `Main_1[lineChart]` is also OK
- Supported types: `lineChart`, `clusteredBarChart`, `waterfallChart`, `stackedBarChart`, `scatterChart`, `funnelChart`, `cardVisual`, `tableEx`, `matrixVisual`, `slicer`, `textbox`

## Integration with Page Scaffold Generator

The page scaffold generator uses layouts to position Power BI visuals automatically:

1. **Bracket YAML** specifies `layout_source: penpot://...` or `page_template: pulse_asymmetric`
2. **ConfigLoader** loads the JSON (from file or API)
3. **PageBuilder** creates visuals at exact pixel positions (no grid calculation needed)
4. **Power BI** renders the report with layouts matching your design

Result: Your Penpot design becomes your Power BI page layout without manual repositioning.

## Next Steps

1. **Create your first layout**: Go to penpot.app, create a 1920×1080 frame, add named slots
2. **Export as JSON**: File → Export → JSON
3. **Place JSON** in `designs/penpot_exports/`
4. **Update Bracket YAML**: Add `layout_source: penpot://file-id/page-id/frame-id`
5. **Run scaffold generator**: Generate your PBIP with exact layouts from your design

Happy designing!
