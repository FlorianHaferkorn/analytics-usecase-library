/**
 * Theme Export API — Generates downloadable theme files.
 *
 * POST { theme, format: 'css' | 'tailwind' | 'json' | 'bundle' }
 */

import type { ThemeConfig } from '@/lib/store/project-store';
import { generateCssCustomProperties } from '@/lib/theme/export-css';
import { generateTailwindConfig } from '@/lib/theme/export-tailwind';
import { generateJsonConfig } from '@/lib/theme/export-json';
import { generateThemeBundle } from '@/lib/theme/export-bundle';
import { apiValidationError } from '@/lib/api/response';

type ExportFormat = 'css' | 'tailwind' | 'json' | 'bundle';

export async function POST(request: Request) {
  const body = await request.json();
  const { theme, format } = body as { theme: ThemeConfig; format: ExportFormat };

  if (!theme || !format) {
    return apiValidationError(['theme and format required']);
  }

  switch (format) {
    case 'css':
      return new Response(generateCssCustomProperties(theme), {
        headers: {
          'Content-Type': 'text/css',
          'Content-Disposition': 'attachment; filename="theme.css"',
        },
      });

    case 'tailwind':
      return new Response(generateTailwindConfig(theme), {
        headers: {
          'Content-Type': 'text/typescript',
          'Content-Disposition': 'attachment; filename="tailwind.config.ts"',
        },
      });

    case 'json':
      return new Response(generateJsonConfig(theme), {
        headers: {
          'Content-Type': 'application/json',
          'Content-Disposition': 'attachment; filename="theme.json"',
        },
      });

    case 'bundle': {
      const zip = generateThemeBundle(theme);
      return new Response(Buffer.from(zip), {
        headers: {
          'Content-Type': 'application/zip',
          'Content-Disposition': 'attachment; filename="actionready-theme.zip"',
        },
      });
    }

    default:
      return apiValidationError([`Unknown format: ${format}`]);
  }
}
