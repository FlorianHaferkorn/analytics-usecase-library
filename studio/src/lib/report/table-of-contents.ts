/**
 * Table of Contents — generates an HTML TOC for board pack reports.
 */

import type { ReportData } from './html-report-builder';

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

export function renderTableOfContents(reports: ReportData[]): string {
  if (reports.length <= 1) return '';

  const items = reports.map((r, i) => {
    const title = r.bracketTitle ?? `Section ${i + 1}`;
    const kpiCount = r.kpis.length;
    return `
      <li>
        <a href="#section-${i}" style="color: inherit; text-decoration: none;">
          ${escapeHtml(title)}
          <span style="color: #999; margin-left: 8px;">(${kpiCount} KPIs)</span>
        </a>
      </li>
    `;
  }).join('');

  return `
    <nav style="margin-bottom: 32px; padding: 16px; background: #f9fafb; border-radius: 8px;">
      <h2 style="font-size: 1rem; margin-bottom: 12px;">Contents</h2>
      <ol style="padding-left: 24px; line-height: 2;">
        ${items}
      </ol>
    </nav>
  `;
}
