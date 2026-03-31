/**
 * Tests for WCAG 2.1 Contrast Checker.
 */

import { describe, it, expect } from 'vitest';
import {
  contrastRatio,
  meetsAA,
  meetsAAA,
  meetsAALargeText,
  getContrastGrade,
  relativeLuminance,
} from '@/lib/theme/contrast-checker';

describe('contrast-checker', () => {
  it('black on white achieves maximum contrast (21:1)', () => {
    const ratio = contrastRatio('#000000', '#FFFFFF');
    expect(ratio).toBeCloseTo(21, 0);
  });

  it('white on black achieves maximum contrast (21:1)', () => {
    const ratio = contrastRatio('#FFFFFF', '#000000');
    expect(ratio).toBeCloseTo(21, 0);
  });

  it('same color has 1:1 contrast', () => {
    const ratio = contrastRatio('#333333', '#333333');
    expect(ratio).toBeCloseTo(1, 0);
  });

  it('black on white meets AAA', () => {
    expect(meetsAAA('#000000', '#FFFFFF')).toBe(true);
    expect(meetsAA('#000000', '#FFFFFF')).toBe(true);
  });

  it('low contrast pair fails AA', () => {
    // Light gray on white
    expect(meetsAA('#CCCCCC', '#FFFFFF')).toBe(false);
    expect(getContrastGrade('#CCCCCC', '#FFFFFF')).toBe('Fail');
  });

  it('mint on dark slate meets AA for large text', () => {
    expect(meetsAALargeText('#00D4AA', '#1E293B')).toBe(true);
  });

  it('getContrastGrade returns correct grades', () => {
    expect(getContrastGrade('#000000', '#FFFFFF')).toBe('AAA');
    // Medium contrast — AA but not AAA
    expect(getContrastGrade('#767676', '#FFFFFF')).toBe('AA');
    // Low contrast — Fail
    expect(getContrastGrade('#AAAAAA', '#FFFFFF')).toBe('Fail');
  });

  it('relativeLuminance for black is 0, white is 1', () => {
    expect(relativeLuminance('#000000')).toBeCloseTo(0);
    expect(relativeLuminance('#FFFFFF')).toBeCloseTo(1);
  });

  it('handles 3-character hex shorthand', () => {
    const ratio = contrastRatio('#000', '#FFF');
    expect(ratio).toBeCloseTo(21, 0);
  });

  it('text on studio background meets AA', () => {
    // Studio: text #F1F5F9 on background #1E293B
    expect(meetsAA('#F1F5F9', '#1E293B')).toBe(true);
  });
});
