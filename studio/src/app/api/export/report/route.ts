/**
 * Report Export API — Generates downloadable HTML board reports.
 *
 * POST { theme, mode: 'single' | 'board-pack', projectName?, bracketId? }
 *
 * When bracketId is provided, builds report from bracket KPIs.
 * Otherwise falls back to sample data for demo/preview.
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
import { loadBracket } from '@/lib/core/bracket-loader';
import { loadKpiMap } from '@/lib/core/catalog-loader';
import { buildReportDataFromBracket } from '@/lib/report/report-data-builder';

export async function POST(request: Request) {
  const body = await request.json();
  const { theme, mode = 'single', projectName = 'Aurora Group', bracketId } = body as {
    theme: ThemeConfig;
    mode?: 'single' | 'board-pack';
    projectName?: string;
    bracketId?: string;
  };

  if (!theme) {
    return new Response(JSON.stringify({ error: 'theme required' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  let reportData: ReportData;

  if (bracketId) {
    const bracket = await loadBracket(bracketId);
    if (bracket) {
      const kpiMap = await loadKpiMap();
      const allKpiIds = [
        bracket.orchestration.strategic_kpi_id,
        ...bracket.orchestration.influencing_kpi_ids,
        ...(bracket.orchestration.supporting_kpi_ids ?? []),
      ];
      reportData = buildReportDataFromBracket(bracketId, kpiMap, allKpiIds, projectName);
    } else {
      reportData = buildSampleReportData(projectName);
    }
  } else {
    reportData = buildSampleReportData(projectName);
  }

  let html: string;
  if (mode === 'board-pack') {
    html = buildBoardPackReport([reportData], theme, projectName);
  } else {
    html = buildHtmlReport(reportData, theme);
  }

  await auditWithActor('export', 'report', 'export', {
    before: null,
    after: { format: 'html-report', mode, projectName, bracketId: bracketId ?? null },
  });

  return new Response(html, {
    headers: {
      'Content-Type': 'text/html',
      'Content-Disposition': `attachment; filename="report-${mode}.html"`,
    },
  });
}

function buildSampleReportData(projectName: string): ReportData {
  return {
    projectName,
    kpis: SAMPLE_KPIS,
    trend: SAMPLE_TREND,
    trendLabel: 'Gross Margin',
    waterfall: SAMPLE_WATERFALL,
    evidence: SAMPLE_EVIDENCE,
  };
}
