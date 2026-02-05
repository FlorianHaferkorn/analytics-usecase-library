"""
Mockup Generator

Generates HTML/CSS mockups to visualize page layouts.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from .layout_calculator import LayoutCalculator


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
            decision_html = f'<p class="decision-question"><strong>Decision question:</strong> {decision_question}</p>'
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Scaffold Preview - {use_case_id} - {page_name}</title>
    <style>
        {self._get_css()}
    </style>
</head>
<body class="page-type-{page_type.lower()}">
    <div class="header">
        <h1>Page Scaffold Preview</h1>
        <p><strong>Use Case:</strong> {use_case_id} | <strong>Page:</strong> {page_name} | <strong>Type:</strong> {page_type}</p>
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
        <button onclick="exportImage()">Export as Image</button>
    </div>
    <script>
        {self._get_javascript()}
    </script>
</body>
</html>"""
        
        return html
    
    def _get_css(self) -> str:
        """Get CSS styles."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        
        .header {
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #252423;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #4A4948;
            margin: 5px 0;
        }
        
        .canvas-container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: auto;
        }
        
        .canvas {
            position: relative;
            width: 1920px;
            height: 1080px;
            background: #FBFBFB;
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
            background-size: 20px 20px;
            pointer-events: none;
        }
        
        .visual {
            position: absolute;
            border: 2px solid #0078D4;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 4px;
            padding: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }
        
        .visual.kpi-card {
            border-color: #519872;
            background: rgba(81, 152, 114, 0.1);
        }
        
        .visual.chart {
            border-color: #0078D4;
        }
        
        .visual.table {
            border-color: #EC4E20;
        }
        
        .visual.slicer {
            border-color: #F6AE2D;
            background: rgba(246, 174, 45, 0.1);
        }
        
        .visual.action-panel {
            border-color: #2E7D5B;
            background: rgba(46, 125, 91, 0.1);
        }
        
        .visual-label {
            font-size: 12px;
            font-weight: bold;
            color: #252423;
            margin-bottom: 4px;
        }
        
        .visual-dims {
            font-size: 10px;
            color: #6E6D6B;
            font-family: 'Courier New', monospace;
        }
        
        .visual-slot {
            font-size: 10px;
            color: #939290;
            font-style: italic;
            margin-top: 4px;
        }
        
        .controls {
            margin-top: 20px;
            text-align: center;
        }
        
        .controls button {
            background: #0078D4;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 0 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .controls button:hover {
            background: #106EBE;
        }
        
        .visual:hover {
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        }
        """
    
    def _get_javascript(self) -> str:
        """Get JavaScript for interactivity."""
        return """
        function toggleGrid() {
            const canvas = document.getElementById('canvas');
            canvas.classList.toggle('grid');
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
        
        # Get slot name from visual (if available)
        slot_name = self._get_slot_name(visual_type)
        
        return f"""
        <div class="visual {css_class}" style="left: {x}px; top: {y}px; width: {width}px; height: {height}px;">
            <div class="visual-label">{visual_type}</div>
            <div class="visual-dims">{int(width)}×{int(height)}px</div>
            <div class="visual-slot">{slot_name}</div>
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
