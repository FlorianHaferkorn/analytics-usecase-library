/**
 * WCAG 2.1 Contrast Checker — pure functions for accessibility validation.
 *
 * Computes luminance and contrast ratios for hex color pairs.
 * AA requires 4.5:1 for normal text, 3:1 for large text.
 * AAA requires 7:1 for normal text, 4.5:1 for large text.
 *
 * Note: contrastRatio() and getContrastGrade() are used in production.
 * meetsAA(), meetsAALargeText(), meetsAAA(), relativeLuminance() are
 * currently only used in tests — TODO: wire into brand/theme validation UI.
 */

/** Parse a hex color (#RGB or #RRGGBB) into [r, g, b] 0-255. */
function parseHex(hex: string): [number, number, number] {
  const h = hex.replace('#', '');
  if (h.length === 3) {
    return [
      parseInt(h[0] + h[0], 16),
      parseInt(h[1] + h[1], 16),
      parseInt(h[2] + h[2], 16),
    ];
  }
  return [
    parseInt(h.slice(0, 2), 16),
    parseInt(h.slice(2, 4), 16),
    parseInt(h.slice(4, 6), 16),
  ];
}

/** Relative luminance per WCAG 2.1. */
export function relativeLuminance(hex: string): number {
  const [r, g, b] = parseHex(hex).map((c) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/** Contrast ratio between two hex colors (1:1 to 21:1). */
export function contrastRatio(fg: string, bg: string): number {
  const l1 = relativeLuminance(fg);
  const l2 = relativeLuminance(bg);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

/** Does the pair meet WCAG 2.1 AA for normal text (4.5:1)? */
export function meetsAA(fg: string, bg: string): boolean {
  return contrastRatio(fg, bg) >= 4.5;
}

/** Does the pair meet WCAG 2.1 AA for large text (3:1)? */
export function meetsAALargeText(fg: string, bg: string): boolean {
  return contrastRatio(fg, bg) >= 3;
}

/** Does the pair meet WCAG 2.1 AAA for normal text (7:1)? */
export function meetsAAA(fg: string, bg: string): boolean {
  return contrastRatio(fg, bg) >= 7;
}

/** Get accessibility grade for a color pair. */
export function getContrastGrade(fg: string, bg: string): 'AAA' | 'AA' | 'Fail' {
  const ratio = contrastRatio(fg, bg);
  if (ratio >= 7) return 'AAA';
  if (ratio >= 4.5) return 'AA';
  return 'Fail';
}
