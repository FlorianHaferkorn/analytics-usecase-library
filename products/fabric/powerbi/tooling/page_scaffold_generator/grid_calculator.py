"""
Grid Calculator (Master Grid 12×12)

Calculates visual positions from logical grid units (LU) to pixel coordinates.
BPA-style: outer margin, gutter between slots. All visuals align to grid boundaries (integer pixels).
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class GridPosition:
    """Pixel position and size of a visual (aligned to grid)."""
    x: float
    y: float
    width: float
    height: float
    z: int = 10000


# Zone 0: der Big-Idea-Header ueber dem Raster (Layout_Grid_System.md, Zeile 0).
# Hoehe nach R1.1-Praezedenz auf dem Produktionsraster. Beide Positionierer -- der
# Seitenbauer beim Erzeugen und apply_page_layout beim Nachziehen -- lesen diese eine
# Stelle; zwei Kopien derselben Regel haetten sich beim naechsten Lauf gegenseitig
# ueberschrieben, und genau das war am 23.09.2026 der Fall.
ZONE0_HEADER_HEIGHT = 56


def zone0_offset(has_header: bool, gutter: float, height: float = ZONE0_HEADER_HEIGHT) -> int:
    """Wie weit das Raster unter den Header rutscht: Headerhoehe plus ein Gutter.

    ``height``: Hoehe des Headers. Der Titelblock (A-34, ``title_block.TITLE_BLOCK_HEIGHT``) ist
    hoeher als die einzeilige Big-Idea-Kopfzeile; beide Positionierer lesen die Hoehe des Headers.
    """
    return int(height + gutter) if has_header else 0


# Mindesthoehe eines Dropdown-Slicers, laut offiziellem Validator (powerbi-report-author
# 0.1.1, PBIR_SLICER_HEIGHT_BELOW_FLOOR): Kopf 28 + Auswahl 32 + Innenabstand 8/8. Eine
# Rasterzeile ergibt auf dem Produktionsraster 70 px, unter einem Big-Idea-Header 64 --
# darunter schneidet Power BI Kopf oder Auswahl ab.
SLICER_DROPDOWN_FLOOR = 76


def _is_dropdown_slicer(visual: dict) -> bool:
    v = visual.get("visual") or {}
    if v.get("visualType") != "slicer":
        return False
    return "Dropdown" in str((v.get("objects") or {}).get("data", ""))


def enforce_slicer_floor(visuals: list, page_bottom: float) -> bool:
    """Hebt Dropdown-Slicer auf SLICER_DROPDOWN_FLOOR und schiebt, was darunter liegt, nach.

    Je Slicer-Zeile waechst die Zeile um die Differenz; jedes Visual, das unterhalb der
    alten Zeilenkante beginnt, rutscht um diese Differenz nach unten und wird um sie
    kuerzer, sobald es sonst ueber die untere Kante ragt. Beide Positionierer rufen diese
    Funktion auf -- dieselbe Regel an zwei Stellen waere die Dublette, die hier am
    23.09.2026 schon einmal den Header unter das KPI-Band geschoben hat.
    """
    zu_klein = [v for v in visuals
                if _is_dropdown_slicer(v) and v["position"]["height"] < SLICER_DROPDOWN_FLOOR]
    geaendert = False
    for oben in sorted({v["position"]["y"] for v in zu_klein}):
        zeile = [v for v in zu_klein if v["position"]["y"] == oben]
        alt = max(v["position"]["height"] for v in zeile)
        delta = SLICER_DROPDOWN_FLOOR - alt
        kante = oben + alt
        for v in zeile:
            v["position"]["height"] = SLICER_DROPDOWN_FLOOR
        for v in visuals:
            if any(v is z for z in zeile):
                continue
            pos = v["position"]
            if pos["y"] >= kante:
                pos["y"] += delta
                if pos["y"] + pos["height"] > page_bottom:
                    pos["height"] -= delta
        geaendert = True
    return geaendert


class GridCalculator:
    """
    12×12 Master Grid. Content area = canvas minus 2× outer_margin;
    cell size derived from (content - (n-1)*gutter) / n.
    """

    GRID_COLS = 12
    GRID_ROWS = 12

    def __init__(
        self,
        canvas_width: int | None = None,
        canvas_height: int | None = None,
        outer_margin: int | None = None,
        gutter: int | None = None,
        internal_padding: int = 8,
    ):
        # Defaults aus dem governten Raster statt als Literale (Konsolidierung
        # 02.08.2026). Diese Klasse fuehrte vorher eine VOLLSTAENDIGE zweite Kopie von
        # layout_grid.yaml — Spalten, Zeilen, Raender, Gutter, Leinwand. Zwei Kopien
        # derselben Zahlen driften nicht vielleicht, sondern sicher; die Frage ist nur,
        # wann es jemand merkt.
        from tooling.superversion.layer_tools.layout_grid import load

        _g = load("production")
        canvas_width = _g.width if canvas_width is None else canvas_width
        canvas_height = _g.height if canvas_height is None else canvas_height
        outer_margin = int(_g.outer) if outer_margin is None else outer_margin
        gutter = int(_g.gutter) if gutter is None else gutter
        """
        Args:
            canvas_width: Page width in pixels.
            canvas_height: Page height in pixels.
            outer_margin: Safety margin from canvas edge (e.g. 24 or 32).
            gutter: Gap between slots (e.g. 16).
            internal_padding: Reserved for future use (e.g. 8).
        """
        self._canvas_width = canvas_width
        self._canvas_height = canvas_height
        self._outer_margin = outer_margin
        self._gutter = gutter
        self._internal_padding = internal_padding
        self._lu_width: float = 0.0
        self._lu_height: float = 0.0
        self._recompute_lu()

    def _recompute_lu(self) -> None:
        """Recompute LU dimensions from current canvas and spacing."""
        cw = self._canvas_width - 2 * self._outer_margin
        ch = self._canvas_height - 2 * self._outer_margin
        n_cols, n_rows = self.GRID_COLS, self.GRID_ROWS
        self._lu_width = (cw - (n_cols - 1) * self._gutter) / n_cols
        self._lu_height = (ch - (n_rows - 1) * self._gutter) / n_rows

    def set_canvas(self, width: int, height: int) -> None:
        """Set canvas size and recompute LU (for proportional scaling)."""
        self._canvas_width = width
        self._canvas_height = height
        self._recompute_lu()

    def get_canvas_size(self) -> Tuple[int, int]:
        """Return (width, height) of canvas."""
        return (self._canvas_width, self._canvas_height)

    def get_lu_size(self) -> Tuple[float, float]:
        """Return (lu_width, lu_height) in pixels."""
        return (self._lu_width, self._lu_height)

    def calculate_visual_rect(
        self,
        col_start: int,
        row_start: int,
        col_span: int,
        row_span: int,
    ) -> GridPosition:
        """
        Compute pixel rectangle for a slot given grid coordinates (0-based).

        Args:
            col_start: Start column (0..11).
            row_start: Start row (0..11).
            col_span: Number of columns (1..12).
            row_span: Number of rows (1..12).

        Returns:
            GridPosition with x, y, width, height (integer-aligned to grid).
        """
        lu_w, lu_h = self._lu_width, self._lu_height
        g = self._gutter
        m = self._outer_margin

        x = m + col_start * (lu_w + g)
        y = m + row_start * (lu_h + g)
        width = col_span * lu_w + (col_span - 1) * g
        height = row_span * lu_h + (row_span - 1) * g

        # Align to integer pixel (grid boundaries)
        return GridPosition(
            x=round(x),
            y=round(y),
            width=round(width),
            height=round(height),
        )


def calculate_visual_rect(
    col_start: int,
    row_start: int,
    col_span: int,
    row_span: int,
    canvas_width: int | None = None,
    canvas_height: int | None = None,
    outer_margin: int = 32,
    gutter: int = 16,
) -> Tuple[float, float, float, float]:
    """
    Standalone helper: (x, y, width, height) for a grid slot.

    Args:
        col_start, row_start: 0-based grid start.
        col_span, row_span: Span in grid cells.
        canvas_width, canvas_height: Canvas size.
        outer_margin: Margin (e.g. 32).
        gutter: Gutter between cells (e.g. 16).

    Returns:
        (x, y, width, height) in pixels.
    """
    calc = GridCalculator(
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        outer_margin=outer_margin,
        gutter=gutter,
    )
    pos = calc.calculate_visual_rect(col_start, row_start, col_span, row_span)
    return (pos.x, pos.y, pos.width, pos.height)
