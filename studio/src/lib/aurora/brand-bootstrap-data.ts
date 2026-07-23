import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { parseYaml } from '@/lib/core/yaml-loader';
import type { ThemeConfig } from '@/lib/store/project-store';

interface BrandSpecYaml {
  color?: {
    primary?: string;
    secondary?: string;
    neutral_scale?: Record<string, string>;
  };
  typography?: {
    font_family?: { primary?: string };
  };
  border?: {
    radius?: { md?: number };
  };
}

/** Server-side theme seed from Aurora brand_spec.yaml (showcase — not user override). */
export function getBrandBootstrapTheme(): Partial<ThemeConfig> | null {
  const specPath = join(process.cwd(), '..', 'showcases', 'aurora_group', 'brand', 'brand_spec.yaml');
  try {
    const raw = readFileSync(specPath, 'utf-8');
    const spec = parseYaml<BrandSpecYaml>(raw);
    const primaryFont = spec.typography?.font_family?.primary?.split(',')[0]?.trim();
    return {
      primary: spec.color?.primary ?? '#2ECDE7',
      secondary: spec.color?.secondary ?? '#44B396',
      accent: spec.color?.primary ?? '#2ECDE7',
      background: spec.color?.neutral_scale?.['900'] ?? '#00396B',
      surface: spec.color?.neutral_scale?.['700'] ?? '#004E7A',
      text: '#F5FBFC',
      fontFamily: primaryFont ?? 'Segoe UI',
      borderRadius: spec.border?.radius?.md ?? 4,
    };
  } catch {
    return null;
  }
}
