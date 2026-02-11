# V1 Finalization — Best Practices Research Results

## Overview

This document synthesizes research findings on best practices for Power BI dashboard design, data visualization, and prescriptive analytics. Each section provides **research-backed recommendations** that can be incorporated into the framework's specifications.

---

## 1. Layout Grid System

### Research Findings

**Power BI Built-in Tools:**
- Power BI provides **gridlines**, **snap-to-grid**, and **smart guides** for visual alignment
- Default canvas size: **1280×720 pixels** (16:9 aspect ratio)
- Can be customized via Format Page > Canvas Settings > Custom

**Best Practices:**
- Use **pixel-level positioning** via Properties panel (Position: X, Y, Width, Height)
- **Align elements symmetrically or intentionally asymmetrically** using pixel alignment
- Use **borders, colored backgrounds, or white space** to group related elements
- Add **dividers** to distinguish different report sections
- Position **related elements close together** to imply relationships

### Recommendations

**Grid System:**
- **Use pixel-based positioning** (not column-based grid) for precise control
- **Standard canvas size:** 1920×1080px (Full HD) for desktop, 1280×720px (HD) as minimum
- **Enable snap-to-grid** in scaffold generator output (set `snapToGrid: true` in page metadata)
- **Standard spacing:** 20px padding from edges, 20px gaps between visuals

**Layout Rules:**
- **KPI Cards Row:** y=0-160px, equal width distribution, max 6 per row
- **Main Visuals Row:** y=180px+, full width (minus slicer column if side placement)
- **Group related visuals** with consistent spacing (20px gaps)
- **Use visual hierarchy:** Larger visuals for primary metrics, smaller for supporting context

---

## 2. Slicer Placement and Behavior

### Research Findings

**Placement Considerations:**
- **No universal "correct" choice** — depends on analysis, user preferences, and report layout
- Power BI's **Filter Pane** always appears on the right side (cannot be repositioned)
- **Custom slicers** can be placed anywhere (top, side, or integrated into layout)
- **Mobile considerations:** Use responsive slicers that adapt from horizontal to vertical layouts

**UX Best Practices:**
- Place slicers **intuitively** so users can filter without overwhelming interface
- **Maintain selection state** — slicers retain selections until explicitly changed
- **Align with audience needs:**
  - Executives: Quick filters for KPIs
  - Operational staff: Real-time filters
  - Analysts: Granular filtering options

### Recommendations

**Default Placement Rules:**
- **Top slicers:** Use when filtering affects most visuals on the page (common for time/date filters)
- **Side slicers:** Use when filtering affects a subset of visuals or when space is limited
- **Default width:** 200px for side slicers, full width (divided equally) for top slicers
- **Default height:** 40px for top slicers (single row), 300px+ for side slicers (multi-row)

**Behavior Rules:**
- **Default state:** Expanded (not collapsed) for immediate visibility
- **Multi-select:** Enabled by default for most slicers (except single-select for mutually exclusive options)
- **Default values:**
  - Time/Date: Current month or last 3 months
  - Categorical: All selected (unless business rule specifies otherwise)
- **Responsive:** Enable responsive slicer settings for mobile layouts

**Framework Default:**
- **Top placement** for time/date slicers (most common)
- **Side placement** for categorical slicers (org, product, region) when space allows
- **Collapsible:** Optional, but default to expanded

---

## 3. Visual Sizing and Spacing

### Research Findings

**Spacing Principles:**
- **Consistent spacing** creates professional appearance
- **Padding around visuals** for clear separation
- **Padding around canvas edges** to frame charts
- **Equal spacing between visual elements** for balanced layout
- **Fill report page appropriately** — enlarge visuals or reduce canvas if excess white space

**Technical Implementation:**
- Use **Properties panel > Position** for pixel-level control
- Define visual **height and width at pixel level**
- Use **spacing calculator tools** to determine starting positions

### Recommendations

**Standard Visual Sizes:**

| Visual Type | Standard Width | Standard Height | Compact Width | Compact Height |
|-------------|----------------|-----------------|---------------|----------------|
| KPI Card | 280px | 140px | 200px | 120px |
| Trend Chart | 800px+ | 400px | 600px | 300px |
| Variance (Waterfall) | 800px+ | 400px | 600px | 300px |
| Ranking (Bar) | 400px+ | 300px | 300px | 250px |
| Mix (Stacked Bar) | 400px+ | 300px | 300px | 250px |
| Table/Matrix | Full width (minus padding) | 300px+ | — | — |
| Exception Table | Full width | 400px+ | — | — |
| Prescriptive Table | Full width (minus Action Panel) | 400px+ | — | — |

**Spacing Rules:**
- **Page padding:** 20px from all edges
- **Gap between visuals:** 20px (horizontal and vertical)
- **KPI Card spacing:** 20px between cards, 20px from edges
- **Visual grouping:** Related visuals grouped with 20px gaps, 40px gap between groups

**Aspect Ratios:**
- **Charts:** Maintain 2:1 aspect ratio (width:height) for readability
- **KPI Cards:** ~2:1 aspect ratio (280×140px)
- **Tables:** Flexible height, minimum 300px

**Framework Defaults:**
- Use **standard sizes** for overview pages
- Use **compact sizes** only when space is constrained (mobile layouts)
- **Full-width visuals** for primary metrics (Trend, Variance, Prescriptive)
- **Half-width visuals** for supporting context (Ranking, Mix)

---

## 4. Color Semantics and Formatting Rules

### Research Findings

**Color Semantics:**
- **Red-Green pairing:** Avoid on same visualization (4.5% of people have color-vision deficiency)
- **Cultural variations:** Meanings vary by culture; clear legends essential
- **Temperature conventions:** Blue-red scales (cold-warm), green-brown scales (altitude)
- **Use color sparingly:** 3-5 categories optimal; 8+ becomes difficult to match visually

**Design Principles:**
- **Contrast and analogy:** Contrasting colors draw attention; analogous colors group items
- **Three dimensions:** Hue (color name), value (lightness), chroma (saturation)
- **Purpose:** Color should "label" and distinguish elements, not create decorative patterns
- **Above all, do no harm:** Color used well enhances clarity; used poorly, obscures

### Recommendations

**Color Semantics (Framework Standard):**

| Color | Meaning | Usage |
|-------|---------|-------|
| **Red** | Below target, negative variance, critical exception | KPI below target, negative variance bars, critical exceptions |
| **Green** | Above target, positive variance, good performance | KPI above target, positive variance bars, good status |
| **Yellow/Orange** | Warning, near threshold, caution | KPI near threshold, warning exceptions, caution status |
| **Gray** | Neutral, no data, inactive | Neutral KPIs, missing data, inactive items |
| **Blue** | Baseline, reference, informational | Target lines, reference values, informational context |

**Formatting Rules:**

**KPI Cards:**
- **Trend arrows:** Show when comparing to previous period (up/down/neutral)
- **Percentage vs absolute:** Show percentage when KPI is a ratio (%), absolute when count/amount
- **Currency:** Format with currency symbol, thousands separator, 2 decimal places
- **Large numbers:** Use K/M/B abbreviations (e.g., 1.2M, 45K)
- **Color coding:** Red if below target, green if above target, yellow if near threshold

**Charts:**
- **Default color palette:** From theme (Monochromatic, Analog, Divergent, NeutralAccent)
- **Target line:** Blue dashed line (from theme accent color)
- **Grid lines:** Light gray, subtle (not prominent)
- **Axis labels:** 10-12pt font, horizontal orientation (rotate only if necessary)
- **Data labels:** Show on key points only (not all points)

**Tables:**
- **Conditional formatting:** Red background for critical exceptions, yellow for warnings
- **Alternating row colors:** Light gray/white for readability
- **Header formatting:** Bold, background color from theme

**Framework Default:**
- **Use theme colors** for all visuals (from Theme Generator)
- **Avoid red-green pairs** — use red-blue or green-blue instead
- **Color-blind friendly:** Use patterns/textures in addition to color for critical distinctions

---

## 5. Exception Table Structure

### Research Findings

**Essential Columns:**
- **Exception metadata:** Type, Message, Method, Assembly
- **Exception hierarchy:** OuterType, OuterMessage, InnermostType, InnermostMessage
- **Application context:** AppRoleName, AppVersion, ClientIP, ClientOS
- **Operational context:** OperationId, OperationName, SessionId
- **Severity and handling:** SeverityLevel, HandledAt, ProblemId
- **Timing:** Timestamp, ItemCount

**Formatting Best Practices:**
- **Column-specific formatting** for readability
- **Width optimization** to show all relevant columns without excessive scrolling
- **Color coding by severity** to quickly identify critical exceptions
- **Consistent formatting** for timestamps and numeric values

### Recommendations

**Required Columns (Framework Standard):**

| Column | Type | Format | Purpose |
|--------|------|--------|---------|
| **Entity** | Text | — | Entity name (e.g., "Product A", "Region North") |
| **Metric** | Text | — | KPI/metric name (e.g., "Sales Revenue", "On-Time Delivery") |
| **Threshold** | Number | Format per metric | Target/threshold value |
| **Actual** | Number | Format per metric | Current actual value |
| **Deviation** | Number | Percentage or absolute | Deviation from threshold |
| **Severity** | Text | — | Critical / Warning / Info |
| **Owner** | Text | — | Responsible person/team |
| **Last Updated** | DateTime | MM/DD/YYYY HH:MM | Timestamp of last update |

**Optional Columns:**
- **Trend** (up/down/neutral arrow)
- **Action Taken** (text description)
- **Status** (Open / In Progress / Resolved)

**Formatting Rules:**
- **Critical exceptions:** Red background (#FFE6E6), bold text
- **Warning exceptions:** Yellow background (#FFF9E6), normal text
- **Info exceptions:** Gray background (#F5F5F5), normal text
- **Max rows:** 50 rows before pagination (show "Show more" button)
- **Sorting:** Default by severity (Critical > Warning > Info), then by deviation (descending)

**Framework Default:**
- **Show all required columns** by default
- **Conditional formatting** by severity level
- **Pagination** after 50 rows
- **Sorting** by severity, then deviation

---

## 6. Prescriptive Table Structure

### Research Findings

**Prescriptive Analytics Components:**
- **Defining the objective**
- **Collecting and preparing data**
- **Analyzing and modeling data**
- **Performing scenario analysis**
- **Generating recommendations**
- **Implementing recommendations**

**Key Elements:**
- **Suggested action** (what to do)
- **Supporting rationale** (why, based on predictive analysis)
- **Expected outcomes** (what will happen)
- **Implementation steps** (how to execute)

### Recommendations

**Required Columns (Framework Standard):**

| Column | Type | Format | Purpose |
|--------|------|--------|---------|
| **Action** | Text | — | Recommended action description |
| **Owner** | Text | — | Responsible person/team |
| **Impact** | Number | Percentage or score (1-10) | Expected impact magnitude |
| **Effort** | Number | Score (1-10) or hours | Required effort/resources |
| **Priority** | Text | — | High / Medium / Low (or 1-5) |
| **Confidence** | Number | Percentage | Confidence level in recommendation |
| **Due Date** | DateTime | MM/DD/YYYY | Recommended completion date |
| **Rationale** | Text | — | Why this action is recommended |

**Optional Columns:**
- **Alternatives** (other options considered)
- **Dependencies** (prerequisites or blockers)
- **Cost** (estimated cost/ROI)
- **Status** (Not Started / In Progress / Completed)

**Formatting Rules:**
- **Highlight "best next action":** Bold, highlighted background (theme accent color)
- **Priority color coding:** High = Red, Medium = Yellow, Low = Green
- **Impact/Effort visualization:** Show as bar charts or icons within cells
- **Max recommendations:** Show top 10 by default (sorted by priority × impact)
- **Sorting:** Default by priority (High > Medium > Low), then by impact (descending)

**Framework Default:**
- **Show all required columns** by default
- **Highlight top recommendation** (highest priority × impact)
- **Pagination** after 10 rows (or show all if <10)
- **Sorting** by priority, then impact

---

## 7. Scatter Plot Axes and Quadrants

### Research Findings

**Impact-Effort Matrix Structure:**
- **Y-axis (Vertical):** Impact (value/benefit delivered)
- **X-axis (Horizontal):** Effort (time/energy/resources required)
- **Four quadrants:**
  1. **High Impact, Low Effort (Quick Wins)** — Tackle first
  2. **High Impact, High Effort (Major Projects)** — Plan carefully
  3. **Low Impact, Low Effort (Fill-ins)** — Complete during spare time
  4. **Low Impact, High Effort (Thankless Tasks)** — Avoid or minimize

**Visualization:**
- Scatter plot with tasks/initiatives as points
- Grid divides space into quadrants
- Items annotated to show what they represent

### Recommendations

**Axes Structure (Framework Standard):**

| Axis | Dimension | Range | Label |
|------|-----------|-------|-------|
| **X-axis** | Effort | 1-10 (or Low/Medium/High) | "Effort Required" |
| **Y-axis** | Impact | 1-10 (or Low/Medium/High) | "Expected Impact" |

**Quadrant Labels:**

| Quadrant | Label | Color | Action |
|----------|-------|-------|--------|
| **Top-Left** | Quick Wins | Green | Do First |
| **Top-Right** | Major Projects | Blue | Plan Carefully |
| **Bottom-Left** | Fill-ins | Gray | Do Later |
| **Bottom-Right** | Thankless Tasks | Red | Avoid |

**Formatting Rules:**
- **Quadrant lines:** Dashed lines at midpoint (5.5 if 1-10 scale)
- **Quadrant labels:** Positioned in center of each quadrant
- **Data points:** Sized by confidence or priority, colored by quadrant
- **Tooltips:** Show Action, Impact, Effort, Priority, Confidence, Owner
- **Max data points:** 50 before aggregation (group similar items)

**Framework Default:**
- **X-axis:** Effort (1-10 scale)
- **Y-axis:** Impact (1-10 scale)
- **Quadrant labels:** Show in center of each quadrant
- **Color coding:** By quadrant (Green/Blue/Gray/Red)

---

## 8. Table vs Matrix Visual

### Research Findings

**Key Differences:**
- **Tables:** Flat, row-based data, no grouping, no drill-down
- **Matrices:** Pivot-table style, automatic aggregation, hierarchical grouping, drill-down support

**When to Use:**
- **Tables:** Detailed transactional data, raw data without aggregation, simple spreadsheet-like view
- **Matrices:** Compare values across categories/subcategories, hierarchical data, totals/subtotals, multi-dimensional analysis

### Recommendations

**Use Table When:**
- Showing **detailed transaction records** (e.g., individual sales orders, exceptions)
- **No aggregation needed** (raw data display)
- **Simple list view** for audits or performance tracking
- **Detail Matrix slot** on detail pages (showing individual records)

**Use Matrix When:**
- Showing **aggregated data across dimensions** (e.g., Sales by Region × Product × Month)
- **Hierarchical grouping** needed (Year > Quarter > Month)
- **Totals and subtotals** required
- **Drill-down capabilities** needed for deeper analysis

**Framework Default:**
- **Detail Matrix slot:** Use **Table** for detail pages (showing individual records)
- **Summary views:** Use **Matrix** when aggregation and grouping are needed
- **Exception tables:** Use **Table** (individual exception records)
- **Prescriptive tables:** Use **Table** (individual recommendations)

---

## 9. Funnel Chart Structure

### Research Findings

**Data Structure:**
- **Minimum:** Category/Stage column + Values column
- **Optional:** Sort Order column (to maintain proper sequence)

**Visualization:**
- Stages as progressively narrower bars
- Wide top = total starting volume
- Narrow bottom = final completion numbers
- Drop-offs between stages immediately visible

**Best Practices:**
- Clean, properly structured data
- Categorical dimension for stage labels
- Appropriate measure columns (counts, sums)
- Calculate percentages relative to top stage

### Recommendations

**Required Columns (Framework Standard):**

| Column | Type | Format | Purpose |
|--------|------|--------|---------|
| **Stage** | Text | — | Funnel stage name (e.g., "Lead", "Qualified", "Closed") |
| **Value** | Number | Integer or decimal | Count or measure for each stage |
| **Sort Order** | Number | Integer (1, 2, 3...) | Maintain proper stage sequence |

**Optional Columns:**
- **Target** (target value for each stage)
- **Conversion Rate** (percentage from previous stage)
- **Owner** (responsible person/team per stage)

**Formatting Rules:**
- **Orientation:** Upright (top = start, bottom = end)
- **Gap spacing:** 10px between stages
- **Color:** Use theme colors (gradient from top to bottom)
- **Labels:** Show stage name and value on each bar
- **Percentages:** Show conversion rate from top stage (e.g., "45% of initial leads")
- **Max stages:** 10 stages before aggregation (group similar stages)

**Framework Default:**
- **Show stage name and value** on each bar
- **Calculate conversion rates** relative to top stage
- **Color gradient** from theme (darker at top, lighter at bottom)
- **Sort by Sort Order** column (not alphabetically)

---

## 10. KPI Card Formatting

### Research Findings

**Core Requirements:**
- **Base measure** (current value)
- **Target measure** or value
- **Threshold** or goal

**Best Practices:**
- **Less is more** — avoid too many KPI visuals
- **Clear, measurable goals** aligned with business objectives
- **Directional arrows** and color codes improve understanding
- **Finely tune deviation representation** for adaptability

**Visualization Options:**
- Dedicated KPI visual (KPI, target, trend over time)
- Gauge visuals
- Card visuals with custom formatting

### Recommendations

**Required Elements (Framework Standard):**

| Element | Format | Purpose |
|---------|--------|---------|
| **KPI Name** | Text | Metric name (e.g., "Sales Revenue") |
| **Current Value** | Number | Formatted per metric type | Current period value |
| **Target Value** | Number | Formatted per metric type | Target/goal value |
| **Variance** | Number | Percentage or absolute | Deviation from target |
| **Trend Arrow** | Icon | Up/Down/Neutral | Comparison to previous period |

**Formatting Rules:**

**Value Formatting:**
- **Currency:** $1,234.56 (2 decimal places, thousands separator)
- **Percentage:** 45.2% (1 decimal place)
- **Large numbers:** 1.2M, 45K (K/M/B abbreviations)
- **Counts:** 1,234 (no decimal places, thousands separator)

**Trend Arrows:**
- **Show when:** Comparing to previous period (e.g., "vs Last Month")
- **Up arrow:** Green if positive change, Red if negative change (context-dependent)
- **Down arrow:** Red if negative change, Green if positive change (context-dependent)
- **Neutral:** Gray horizontal line

**Color Coding:**
- **Above target:** Green background or border
- **Below target:** Red background or border
- **Near target (±5%):** Yellow background or border
- **No target:** Gray (neutral)

**Framework Default:**
- **Show KPI name, current value, target, variance, trend arrow**
- **Format values** per metric type (currency, percentage, count)
- **Color code** by performance vs target
- **Trend arrow** shows comparison to previous period

---

## Summary of Framework Defaults

### Layout
- **Canvas:** 1920×1080px (Full HD), 1280×720px minimum
- **Padding:** 20px from edges
- **Gaps:** 20px between visuals
- **Snap-to-grid:** Enabled

### Slicers
- **Placement:** Top for time/date, side for categorical
- **Width:** 200px (side), full width divided equally (top)
- **Height:** 40px (top), 300px+ (side)
- **Default:** Expanded, multi-select enabled
- **Default values:** Current month or last 3 months (time), All selected (categorical)

### Visual Sizing
- **KPI Card:** 280×140px (standard), 200×120px (compact)
- **Charts:** 800×400px minimum (standard), 600×300px (compact)
- **Tables:** Full width, 300px+ height
- **Aspect ratio:** 2:1 for charts

### Color Semantics
- **Red:** Below target, negative variance, critical
- **Green:** Above target, positive variance, good
- **Yellow/Orange:** Warning, near threshold
- **Gray:** Neutral, no data
- **Blue:** Baseline, reference

### Tables
- **Exception Table:** Entity, Metric, Threshold, Actual, Deviation, Severity, Owner, Last Updated
- **Prescriptive Table:** Action, Owner, Impact, Effort, Priority, Confidence, Due Date, Rationale
- **Max rows:** 50 (exceptions), 10 (prescriptive)
- **Sorting:** By severity/priority, then by deviation/impact

### Charts
- **Scatter Plot:** X=Effort, Y=Impact, 4 quadrants labeled
- **Funnel Chart:** Stage, Value, Sort Order columns
- **Color palette:** From theme (no red-green pairs)

---

## Next Steps

1. **Incorporate these recommendations** into formal governance files
2. **Create visual-to-slot mapping** YAML file with these defaults
3. **Update page scaffold spec** with concrete sizing and spacing rules
4. **Create formatting standards** document for developers
5. **Test with COM-001** scaffold generation
