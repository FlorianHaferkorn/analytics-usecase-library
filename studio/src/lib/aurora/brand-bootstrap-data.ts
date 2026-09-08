/**
 * Server-side bootstrap of the governed brand into the Studio theme.
 *
 * `core/brand/` is the SSOT for brand identity (BrandSpec.schema.yaml); the Studio theme
 * is a *projection* of it, never a second definition. This module maps a BrandSpec onto
 * the store's `ThemeConfig` so the running app renders in the governed brand instead of
 * the hardcoded default.
 *
 * Server-only (`node:fs`). Returns `null` when no spec is present, so the store keeps
 * `DEFAULT_THEME` rather than being blanked by a half-filled object.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { parseYaml } from '@/lib/core/yaml-loader';
import type { ThemeConfig } from '@/lib/store/project-store';

/** Only the BrandSpec fields the Studio theme projects — not the whole schema. */
interface BrandSpec {
  color?: {
    primary?: string;
    secondary?: string;
    semantic?: { positive?: { color?: string } };
    neutral_scale?: Record<string, string>;
  };
  typography?: { font_family?: { primary?: string } };
  border?: { radius?: Record<string, number> };
  shadow?: Record<string, string>;
}

let cached: Partial<ThemeConfig> | null | undefined;

function specPath(): string {
  // Studio runs with cwd=studio/; the brand lives one level up in the repo.
  const configured = process.env.STUDIO_BRAND_SPEC;
  if (configured) {
    return join(/*turbopackIgnore: true*/ process.cwd(), '..', configured);
  }
  return join(process.cwd(), '..', 'core', 'brand', 'samples', 'generic_brand.yaml');
}

function project(spec: BrandSpec): Partial<ThemeConfig> {
  const neutral = spec.color?.neutral_scale ?? {};
  const theme: Partial<ThemeConfig> = {};

  // Only assign what the spec actually carries — an undefined value would otherwise
  // overwrite a good default via the store's shallow merge.
  if (spec.color?.primary) theme.primary = spec.color.primary;
  if (spec.color?.secondary) theme.secondary = spec.color.secondary;
  // `--accent` marks the positive/improvement state across the shell, so it projects
  // from the semantic positive colour, not from a second brand hue.
  if (spec.color?.semantic?.positive?.color) theme.accent = spec.color.semantic.positive.color;
  if (neutral['50']) theme.background = neutral['50'];
  if (neutral['100']) theme.surface = neutral['100'];
  if (neutral['900']) theme.text = neutral['900'];
  if (spec.typography?.font_family?.primary) theme.fontFamily = spec.typography.font_family.primary;
  if (typeof spec.border?.radius?.md === 'number') theme.borderRadius = spec.border.radius.md;
  if (spec.shadow?.low) theme.shadow = spec.shadow.low;

  return theme;
}

/**
 * The governed brand projected onto `ThemeConfig`, or `null` when unavailable.
 *
 * A missing or malformed spec is not an error state for the app — the Studio still runs
 * on its default theme — so this never throws.
 */
export function getBrandBootstrapTheme(): Partial<ThemeConfig> | null {
  if (cached !== undefined) return cached;

  try {
    const spec = parseYaml<BrandSpec>(readFileSync(specPath(), 'utf-8'));
    const theme = project(spec);
    cached = Object.keys(theme).length > 0 ? theme : null;
  } catch {
    cached = null;
  }
  return cached;
}
