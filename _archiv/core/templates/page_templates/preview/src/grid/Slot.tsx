// ============================================================================
// <Slot> — the single positioning primitive for every page template.
// ============================================================================
// All page elements MUST be wrapped in a <Slot>. No other positioning is
// allowed. The grid validator scans the source tree for slotPos() calls and
// verifies overflow + overlap constraints at build time.
// ============================================================================

import type { CSSProperties, ReactNode } from "react";
import { slotPos, validateSlot, type SlotCoords } from "./slot-pos.js";

export interface SlotProps extends SlotCoords {
  /** Machine-readable slot identifier (e.g. "KPI_1", "Main_2", "ActionPanel"). */
  slotId: string;
  /** Optional visible label for anatomy view. */
  label?: string;
  /** Optional extra style (merged AFTER slotPos() — never use for position). */
  extraStyle?: CSSProperties;
  /** Optional className (e.g. "anatomy", "clean"). */
  className?: string;
  children?: ReactNode;
}

export function Slot({
  col,
  row,
  cs,
  rs,
  slotId,
  label,
  extraStyle,
  className,
  children,
}: SlotProps): JSX.Element {
  // Dev-mode guard: fail loudly in the console if a slot is malformed.
  if (import.meta.env?.DEV) {
    const errors = validateSlot({ col, row, cs, rs });
    if (errors.length > 0) {
      console.error(
        `[Slot] Invalid coords for slotId="${slotId}":`,
        errors.map((e) => e.message).join(", "),
      );
    }
  }

  const style: CSSProperties = {
    ...slotPos({ col, row, cs, rs }),
    ...extraStyle,
  };

  return (
    <div
      data-slot-id={slotId}
      data-slot-col={col}
      data-slot-row={row}
      data-slot-cs={cs}
      data-slot-rs={rs}
      className={className}
      style={style}
    >
      {label && <span className="slot-anatomy-label">{label}</span>}
      {children}
    </div>
  );
}
