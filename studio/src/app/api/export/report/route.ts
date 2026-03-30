/**
 * Report Export API — Generates downloadable HTML board reports.
 *
 * POST { theme, mode: 'single' | 'board-pack', projectName? }
 */

import type { ThemeConfig } from '@/lib/store/project-store';
import {
  SAMPLE_KPIS,
  SAMPLE_TREND,
  SAMPLE_WATERFALL,
  SAMPLE_EVIDENCE,
} from '@/lib/dashboard/sample-data';
import { buildHtmlReport, buildBoardPackReport } from '@/lib/report/html-report-builder';
import type { ReportData } from '@/lib/report/html-report-builder';
import { auditWithActor } from '@/lib/db/audit-helpers';

export async function POST(request: Request) {
  const body = await request.json();
  const { theme, mode = 'single', projectName = 'Aurora Group' } = body as {
    theme: ThemeConfig;
    mode?: 'single' | 'board-pack';
    projectName?: string;
  };

  if (!theme) {
    return new Response(JSON.stringify({ error: 'theme required' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const reportData: ReportData = {
    projectName,
    kpis: SAMPLE_KPIS,
    trend: SAMPLE_TREND,
    trendLabel: 'Gross Margin',
    waterfall: SAMPLE_WATERFALL,
    evidence: SAMPLE_EVIDENCE,
  };

  let html: string;
  if (mode === 'board-pack') {
    html = buildBoardPackReport([reportData], theme, projectName);
  } else {
    html = buildHtmlReport(reportData, theme);
  }

  await auditWithActor('export', 'report', 'export', {
    before: null,
    after: { format: 'html-report', mode, projectName },
  });

  return new Response(html, {
    headers: {
      'Content-Type': 'text/html',
      'Content-Disposition': `attachment; filename="report-${mode}.html"`,
    },
  });
}
