// ============================================================================
// slot-pos.ts — CSS-calc-based grid positioning
// ----------------------------------------------------------------------------
// slotPos() returns CSS calc() strings that reference --lu-w, --lu-h, --outer
// and --gutter. When any of those tokens change at runtime (density switch,
// canvas resize), every slot reflows automatically — no JS re-render needed.
//
// Mathematical contract (must mirror tokens.css):
//   left   = outer + col * (lu-w + gutter)
//   top    = outer + row * (lu-h + gutter)
//   width  = cs  * lu-w + (cs - 1) * gutter
//   height = rs  * lu-h + (rs - 1) * gutter
// ============================================================================

import { GRID } from "../tokens/tokens.js";

export interface SlotCoords {
  /** 0-indexed column, may be fractional (e.g. 2.2) */
  col: number;
  /** 0-indexed row, may be fractional (e.g. 3.4) */
  row: number;
  /** column span */
  cs: number;
  /** row span */
  rs: number;
}

export interface SlotStyle {
  position: "absolute";
  left: string;
  top: string;
  width: string;
  height: string;
}

export interface SlotValidationError {
  field: "col" | "row" | "cs" | "rs" | "colOverflow" | "rowOverflow";
  message: string;
}

/** Validate a slot coord against the 12x12 grid. Returns list of errors; [] if OK. */
export function validateSlot(coords: SlotCoords): SlotValidationError[] {
  const errors: SlotValidationError[] = [];
  const { col, row, cs, rs } = coords;

  if (!Number.isFinite(col) || col < 0)
    errors.push({ field: "col", message: `col must be >= 0 (got ${col})` });
  if (!Number.isFinite(row) || row < 0)
    errors.push({ field: "row", message: `row must be >= 0 (got ${row})` });
  if (!Number.isFinite(cs) || cs <= 0)
    errors.push({ field: "cs", message: `cs must be > 0 (got ${cs})` });
  if (!Number.isFinite(rs) || rs <= 0)
    errors.push({ field: "rs", message: `rs must be > 0 (got ${rs})` });

  // Overflow check (allow tiny float tolerance)
  const EPS = 0.001;
  if (col + cs > GRID.COLS + EPS)
    errors.push({
      field: "colOverflow",
      message: `col + cs exceeds grid width: ${col} + ${cs} = ${col + cs} > ${GRID.COLS}`,
    });
  if (row + rs > GRID.ROWS + EPS)
    errors.push({
      field: "rowOverflow",
      message: `row + rs exceeds grid height: ${row} + ${rs} = ${row + rs} > ${GRID.ROWS}`,
    });

  return errors;
}

/**
 * Build a CSS-calc-based positioning style for a slot.
 * Does NOT validate — call validateSlot() first in development / CI.
 */
export function slotPos(coords: SlotCoords): SlotStyle {
  const { col, row, cs, rs } = coords;
  return {
    position: "absolute",
    left: `calc(var(--outer) + ${col} * (var(--lu-w) + var(--gutter)))`,
    top: `calc(var(--outer) + ${row} * (var(--lu-h) + var(--gutter)))`,
    width: `calc(${cs} * var(--lu-w) + ${cs - 1} * var(--gutter))`,
    height: `calc(${rs} * var(--lu-h) + ${rs - 1} * var(--gutter))`,
  };
}

/**
 * Check whether two slots overlap on the grid (ignoring z-order).
 * Used by the grid validator in CI.
 */
export function slotsOverlap(a: SlotCoords, b: SlotCoords): boolean {
  const EPS = 0.001;
  const horizOverlap =
    a.col < b.col + b.cs - EPS && b.col < a.col + a.cs - EPS;
  const vertOverlap =
    a.row < b.row + b.rs - EPS && b.row < a.row + a.rs - EPS;
  return horizOverlap && vertOverlap;
}
