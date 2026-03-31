/**
 * Tests for Theme Export generators.
 */

import { describe, it, expect } from 'vitest';
import { generateCssCustomProperties } from '../../src/lib/theme/export-css';
import { generateTailwindConfig } from '../../src/lib/theme/export-tailwind';
import { generateJsonConfig } from '../../src/lib/theme/export-json';
import type { ThemeConfig } from '../../src/lib/store/project-store';

const MOCK_THEME: ThemeConfig = {
  primary: '#00D4AA',
  secondary: '#FFB800',
  accent: '#3B82F6',
  background: '#1E293B',
  surface: '#0F172A',
  text: '#F1F5F9',
  fontFamily: 'Inter',
  borderRadius: 8,
};

describe('generateCssCustomProperties', () => {
  it('contains all custom properties', () => {
    const css = generateCssCustomProperties(MOCK_THEME);
    expect(css).toContain('--ar-primary: #00D4AA');
    expect(css).toContain('--ar-secondary: #FFB800');
    expect(css).toContain('--ar-accent: #3B82F6');
    expect(css).toContain('--ar-background: #1E293B');
    expect(css).toContain('--ar-surface: #0F172A');
    expect(css).toContain('--ar-text: #F1F5F9');
    expect(css).toContain('--ar-font-family: Inter, sans-serif');
    expect(css).toContain('--ar-border-radius: 8px');
  });

  it('generates opacity variants', () => {
    const css = generateCssCustomProperties(MOCK_THEME);
    expect(css).toContain('--ar-primary-10:');
    expect(css).toContain('--ar-primary-20:');
    expect(css).toContain('--ar-secondary-10:');
    expect(css).toContain('--ar-accent-10:');
  });

  it('derives sm and lg radius', () => {
    const css = generateCssCustomProperties(MOCK_THEME);
    expect(css).toContain('--ar-border-radius-sm: 4px');
    expect(css).toContain('--ar-border-radius-lg: 12px');
  });

  it('handles font family with spaces', () => {
    const theme = { ...MOCK_THEME, fontFamily: 'Plus Jakarta Sans' };
    const css = generateCssCustomProperties(theme);
    expect(css).toContain('"Plus Jakarta Sans", sans-serif');
  });

  it('clamps sm radius to 0', () => {
    const theme = { ...MOCK_THEME, borderRadius: 2 };
    const css = generateCssCustomProperties(theme);
    expect(css).toContain('--ar-border-radius-sm: 0px');
  });
});

describe('generateTailwindConfig', () => {
  it('outputs valid TypeScript structure', () => {
    const tw = generateTailwindConfig(MOCK_THEME);
    expect(tw).toContain('import type { Config }');
    expect(tw).toContain('const config: Partial<Config>');
    expect(tw).toContain('export default config;');
  });

  it('includes color definitions', () => {
    const tw = generateTailwindConfig(MOCK_THEME);
    expect(tw).toContain('primary:');
    expect(tw).toContain('secondary:');
    expect(tw).toContain('accent:');
    expect(tw).toContain('background:');
    expect(tw).toContain('surface:');
    expect(tw).toContain('text:');
  });

  it('includes border radius tokens', () => {
    const tw = generateTailwindConfig(MOCK_THEME);
    expect(tw).toContain('"8px"');
    expect(tw).toContain('"4px"');
    expect(tw).toContain('"12px"');
  });

  it('handles font family with spaces', () => {
    const theme = { ...MOCK_THEME, fontFamily: 'DM Sans' };
    const tw = generateTailwindConfig(theme);
    expect(tw).toContain('"DM Sans"');
  });
});

describe('generateJsonConfig', () => {
  it('produces valid JSON that round-trips', () => {
    const json = generateJsonConfig(MOCK_THEME);
    const parsed = JSON.parse(json);
    expect(parsed.name).toBe('ActionReady Theme');
    expect(parsed.version).toBe('1.0.0');
  });

  it('contains all color values', () => {
    const parsed = JSON.parse(generateJsonConfig(MOCK_THEME));
    expect(parsed.colors.primary).toBe('#00D4AA');
    expect(parsed.colors.secondary).toBe('#FFB800');
    expect(parsed.colors.accent).toBe('#3B82F6');
    expect(parsed.colors.background).toBe('#1E293B');
    expect(parsed.colors.surface).toBe('#0F172A');
    expect(parsed.colors.text).toBe('#F1F5F9');
  });

  it('includes status (RAG) colors', () => {
    const parsed = JSON.parse(generateJsonConfig(MOCK_THEME));
    expect(parsed.colors.status.red).toBe('#EF4444');
    expect(parsed.colors.status.amber).toBe('#FFB800');
    expect(parsed.colors.status.green).toBe('#10B981');
  });

  it('includes typography and layout', () => {
    const parsed = JSON.parse(generateJsonConfig(MOCK_THEME));
    expect(parsed.typography.fontFamily).toBe('Inter');
    expect(parsed.layout.borderRadius).toBe(8);
    expect(parsed.layout.borderRadiusSm).toBe(4);
    expect(parsed.layout.borderRadiusLg).toBe(12);
  });
});
