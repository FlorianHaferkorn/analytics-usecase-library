"""
Mockup Generator

Generates HTML/CSS mockups to visualize page layouts.
"""

import html
from pathlib import Path
from typing import Dict, Any, List, Optional
from .layout_calculator import LayoutCalculator


def _escape_html(text: str) -> str:
    """Escape string for safe interpolation into HTML (prevents XSS)."""
    if not text:
        return ""
    return html.escape(str(text), quote=True)


class MockupGenerator:
    """Generates HTML/CSS mockups for page scaffolds."""
    
    def __init__(self):
        """Initialize mockup generator."""
        self.layout_calculator = LayoutCalculator()
    
    def generate_mockup(
        self,
        page_structure: Dict[str, Any],
        use_case_id: str,
        page_name: str,
        output_path: Path,
        page_type: Optional[str] = None,
        decision_question: Optional[str] = None,
    ):
        """
        Generate HTML mockup.
        
        Args:
            page_structure: Page structure from scaffold generator (same layout engine as PBIP)
            use_case_id: Use case ID
            page_name: Page name
            output_path: Output HTML file path
            page_type: Page type T1/T2/T3/T4 (from scaffold; used for hierarchy/CSS). If None, read from page_structure.
            decision_question: Optional primary decision question for header/banner
        """
        if page_type is None:
            page_type = page_structure.get("page_type") or "T2"
        html_content = self._build_html(
            page_structure=page_structure,
            use_case_id=use_case_id,
            page_name=page_name,
            page_type=page_type,
            decision_question=decision_question,
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _build_html(
        self,
        page_structure: Dict[str, Any],
        use_case_id: str,
        page_name: str,
        page_type: str = "T2",
        decision_question: Optional[str] = None,
    ) -> str:
        """Build HTML content. Uses same layout as PBIP (positions from page_structure)."""
        visuals = page_structure.get("visuals", [])
        slicers = page_structure.get("slicers", [])
        
        # Build visual HTML
        visual_html = []
        for visual in visuals:
            visual_html.append(self._render_visual(visual))
        
        for slicer in slicers:
            visual_html.append(self._render_slicer(slicer))
        
        decision_html = ""
        if decision_question:
            decision_html = f'<p class="decision-question"><strong>Decision question:</strong> {_escape_html(decision_question)}</p>'
        safe_use_case_id = _escape_html(use_case_id)
        safe_page_name = _escape_html(page_name)
        safe_page_type = _escape_html(page_type)
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Scaffold Preview - {safe_use_case_id} - {safe_page_name}</title>
    <style>
        {self._get_css()}
    </style>
</head>
<body class="page-type-{safe_page_type.lower()}">
    <div class="header">
        <h1>Page Scaffold Preview</h1>
        <p><strong>Use Case:</strong> {safe_use_case_id} | <strong>Page:</strong> {safe_page_name} | <strong>Type:</strong> {safe_page_type}</p>
        {decision_html}
        <p><strong>Canvas:</strong> {self.layout_calculator.CANVAS_WIDTH}×{self.layout_calculator.CANVAS_HEIGHT}px</p>
    </div>
    <div class="canvas-container">
        <div class="canvas" id="canvas">
            {''.join(visual_html)}
        </div>
    </div>
    <div class="controls">
        <button onclick="toggleGrid()">Toggle Grid</button>
        <button onclick="toggleDimensions()">Toggle Dimensions</button>
        <button onclick="exportImage()">Export as Image</button>
    </div>
    <script>
        {self._get_javascript()}
    </script>
</body>
</html>"""
        
        return html
    
    def _get_css(self) -> str:
        """Get CSS styles. Uses design spec: CSS variables, typography, hierarchy."""
        return """
        :root {
            --canvas-bg: #FBFBFB;
            --kpi-band-bg: rgba(81, 152, 114, 0.08);
            --font-title: 1.25rem;
            --font-slot: 0.75rem;
            --font-dims: 0.65rem;
            --space-unit: 20px;
            --radius: 6px;
            --shadow: 0 2px 8px rgba(0,0,0,0.12);
            --shadow-hover: 0 4px 12px rgba(0,0,0,0.2);
            --color-text: #252423;
            --color-muted: #6E6D6B;
            --color-slot: #939290;
            --color-accent: #0078D4;
            --color-kpi: #519872;
            --color-chart: #0078D4;
            --color-table: #EC4E20;
            --color-slicer: #F6AE2D;
            --color-action: #2E7D5B;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f0f0f0;
            padding: var(--space-unit);
        }
        
        .header {
            background: white;
            padding: var(--space-unit);
            margin-bottom: var(--space-unit);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
        }
        
        .header h1 {
            font-size: var(--font-title);
            font-weight: 600;
            color: var(--color-text);
            margin-bottom: 0.5rem;
        }
        
        .header p {
            color: var(--color-muted);
            margin: 0.25rem 0;
            font-size: var(--font-slot);
        }
        
        .header .decision-question {
            margin-top: 0.5rem;
            padding: 0.5rem;
            background: var(--kpi-band-bg);
            border-left: 4px solid var(--color-kpi);
            border-radius: 0 var(--radius) var(--radius) 0;
        }
        
        .canvas-container {
            background: white;
            padding: var(--space-unit);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            overflow: auto;
        }
        
        .canvas {
            position: relative;
            width: 1920px;
            height: 1080px;
            background: var(--canvas-bg);
            border: 1px solid #E6E6E6;
            margin: 0 auto;
        }
        
        .canvas.grid::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(to right, rgba(0,0,0,0.05) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(0,0,0,0.05) 1px, transparent 1px);
            background-size: var(--space-unit) var(--space-unit);
            pointer-events: none;
        }
        
        .visual {
            position: absolute;
            border: 2px solid var(--color-chart);
            background: rgba(255, 255, 255, 0.95);
            border-radius: var(--radius);
            padding: 8px;
            box-shadow: var(--shadow);
        }
        
        .visual.kpi-card {
            border-color: var(--color-kpi);
            background: var(--kpi-band-bg);
        }
        
        .visual.chart {
            border-color: var(--color-chart);
        }
        
        .visual.table {
            border-color: var(--color-table);
        }
        
        .visual.slicer {
            border-color: var(--color-slicer);
            background: rgba(246, 174, 45, 0.08);
        }
        
        .visual.action-panel {
            border-color: var(--color-action);
            background: rgba(46, 125, 91, 0.08);
        }
        
        .visual-label {
            font-size: var(--font-slot);
            font-weight: 600;
            color: var(--color-text);
            margin-bottom: 4px;
        }
        
        .visual-dims {
            font-size: var(--font-dims);
            color: var(--color-muted);
            font-family: 'Courier New', monospace;
        }
        
        .visual-slot {
            font-size: var(--font-dims);
            color: var(--color-slot);
            font-style: italic;
            margin-top: 4px;
        }
        
        .controls {
            margin-top: var(--space-unit);
            text-align: center;
        }
        
        .controls button {
            background: var(--color-accent);
            color: white;
            border: none;
            padding: 10px var(--space-unit);
            margin: 0 10px;
            border-radius: var(--radius);
            cursor: pointer;
            font-size: var(--font-slot);
        }
        
        .controls button:hover {
            filter: brightness(0.92);
        }
        
        .visual:hover {
            z-index: 10000;
            box-shadow: var(--shadow-hover);
        }
        
        body.hide-dimensions .visual-dims,
        body.hide-dimensions .visual-slot {
            display: none;
        }
        """
    
    def _get_javascript(self) -> str:
        """Get JavaScript for interactivity (grid, developer/presentation mode)."""
        return """
        function toggleGrid() {
            document.getElementById('canvas').classList.toggle('grid');
        }
        
        function toggleDimensions() {
            document.body.classList.toggle('hide-dimensions');
        }
        
        function exportImage() {
            const canvas = document.getElementById('canvas');
            html2canvas(canvas, {
                backgroundColor: '#FBFBFB',
                scale: 1
            }).then(canvas => {
                const link = document.createElement('a');
                link.download = 'page-scaffold-preview.png';
                link.href = canvas.toDataURL();
                link.click();
            });
        }
        """
    
    def _render_visual(self, visual: Dict[str, Any]) -> str:
        """Render visual as HTML div."""
        position = visual.get("position", {})
        visual_type = visual.get("visual", {}).get("visualType", "unknown")
        
        x = position.get("x", 0)
        y = position.get("y", 0)
        width = position.get("width", 0)
        height = position.get("height", 0)
        
        # Map visual types to CSS classes
        type_to_class = {
            "cardVisual": "kpi-card",
            "lineChart": "chart",
            "waterfallChart": "chart",
            "clusteredBarChart": "chart",
            "hundredPercentStackedBarChart": "chart",
            "tableEx": "table",
            "pivotTable": "table",
            "scatterChart": "chart",
            "funnelChart": "chart",
            "textbox": "action-panel",
            "slicer": "slicer"
        }
        
        css_class = type_to_class.get(visual_type, "visual")
        
        slot_name = self._get_slot_name(visual_type)
        # Prefer speaking name from scaffold (e.g. KPI_1, Trend, Slicer_Date)
        display_label = visual.get("name") or visual_type

        return f"""
        <div class="visual {_escape_html(css_class)}" style="left: {x}px; top: {y}px; width: {width}px; height: {height}px;">
            <div class="visual-label">{_escape_html(display_label)}</div>
            <div class="visual-dims">{int(width)}x{int(height)}px</div>
            <div class="visual-slot">{_escape_html(slot_name)}</div>
        </div>
        """
    
    def _render_slicer(self, slicer: Dict[str, Any]) -> str:
        """Render slicer as HTML div."""
        return self._render_visual(slicer)
    
    def _get_slot_name(self, visual_type: str) -> str:
        """Get slot name from visual type."""
        type_to_slot = {
            "cardVisual": "KPI Summary",
            "lineChart": "Trend",
            "waterfallChart": "Variance",
            "clusteredBarChart": "Ranking",
            "hundredPercentStackedBarChart": "Mix",
            "tableEx": "Exceptions/Prescriptive/Detail Matrix",
            "pivotTable": "Detail Matrix",
            "scatterChart": "Root Cause",
            "funnelChart": "Funnel",
            "textbox": "Action Panel",
            "slicer": "Slicer"
        }
        
        return type_to_slot.get(visual_type, "Unknown")
