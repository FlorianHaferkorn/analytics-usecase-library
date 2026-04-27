// ============================================================================
// <Canvas> — the host container for a page template.
// ============================================================================
// - Reads --canvas-w / --canvas-h from CSS tokens.
// - Establishes a local positioning context for all child <Slot>s.
// - Does NOT use inline pixel widths — reads the tokens via CSS.
// ============================================================================

import type { ReactNode, CSSProperties } from "react";

export interface CanvasProps {
  /** Optional anatomy mode — draws grid lines + slot labels. */
  anatomy?: boolean;
  /** Optional className hook for tests / styling. */
  className?: string;
  children?: ReactNode;
}

export function Canvas({
  anatomy = false,
  className,
  children,
}: CanvasProps): JSX.Element {
  const style: CSSProperties = {
    // Reads canvas size from CSS tokens — no hard-coded px here.
    position: "relative",
    width: "calc(var(--canvas-w) * 1px)",
    height: "calc(var(--canvas-h) * 1px)",
    background: "var(--c-surface-0)",
    overflow: "hidden",
    boxShadow: "var(--shadow-md)",
    borderRadius: "var(--r-lg)",
  };

  return (
    <div
      data-canvas-root
      data-anatomy={anatomy || undefined}
      className={className}
      style={style}
    >
      {anatomy && <AnatomyOverlay />}
      {children}
    </div>
  );
}

/** Renders grid lines + safe-area outline for design reviews. */
function AnatomyOverlay(): JSX.Element {
  const style: CSSProperties = {
    position: "absolute",
    inset: 0,
    pointerEvents: "none",
    backgroundImage: `
      linear-gradient(to right, rgba(0,120,212,0.08) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(0,120,212,0.08) 1px, transparent 1px)
    `,
    backgroundSize: `
      calc(var(--lu-w) + var(--gutter)) 100%,
      100% calc(var(--lu-h) + var(--gutter))
    `,
    backgroundPosition: "var(--outer) var(--outer)",
  };
  return <div aria-hidden style={style} />;
}
