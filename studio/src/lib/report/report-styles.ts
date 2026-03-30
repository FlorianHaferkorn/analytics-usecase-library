/**
 * Report Styles — Print-optimized CSS for exported HTML reports.
 *
 * Reuses theme tokens and generates inline styles for the report document.
 */

import type { ThemeConfig } from '@/lib/store/project-store';

export function generateReportStyles(theme: ThemeConfig): string {
  return `
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: ${theme.fontFamily.includes(' ') ? `"${theme.fontFamily}"` : theme.fontFamily}, sans-serif;
      background: #fff;
      color: #1a1a2e;
      padding: 40px;
      max-width: 1100px;
      margin: 0 auto;
    }
    header {
      display: flex; justify-content: space-between; align-items: center;
      border-bottom: 3px solid ${theme.primary}; padding-bottom: 16px; margin-bottom: 32px;
    }
    header h1 { font-size: 1.5rem; color: #1a1a2e; }
    header .date { font-size: 0.875rem; color: #666; }
    h2 { font-size: 1.125rem; color: #1a1a2e; margin: 24px 0 12px; }
    .pulse-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-bottom: 24px; }
    .pulse-card {
      padding: 16px; border-radius: ${theme.borderRadius}px;
      border: 1px solid #e5e7eb; border-left: 4px solid ${theme.primary};
    }
    .pulse-card .label { font-size: 0.75rem; color: #666; margin-bottom: 4px; }
    .pulse-card .value { font-size: 1.5rem; font-weight: 700; }
    .pulse-card .delta { font-size: 0.75rem; margin-top: 4px; }
    .pulse-card .target { font-size: 0.6875rem; color: #999; margin-top: 2px; }
    .status-on-track { color: #10B981; }
    .status-at-risk { color: #FFB800; }
    .status-off-track { color: #EF4444; }
    .trend-container { margin-bottom: 24px; }
    .trend-bars { display: flex; align-items: flex-end; gap: 4px; height: 120px; }
    .trend-bar {
      flex: 1; background: ${theme.primary}; border-radius: 3px 3px 0 0;
      display: flex; flex-direction: column; align-items: center; justify-content: flex-end;
    }
    .trend-bar .val { font-size: 0.5625rem; color: #666; margin-bottom: 2px; }
    .trend-labels { display: flex; gap: 4px; margin-top: 4px; }
    .trend-labels span { flex: 1; text-align: center; font-size: 0.5625rem; color: #999; }
    .waterfall-container { margin-bottom: 24px; }
    .waterfall-bars { display: flex; gap: 8px; align-items: flex-end; height: 100px; }
    .waterfall-item { flex: 1; text-align: center; }
    .waterfall-item .bar {
      margin: 0 auto; width: 32px; border-radius: 3px;
      min-height: 4px;
    }
    .waterfall-item .driver { font-size: 0.625rem; color: #666; margin-top: 4px; }
    .waterfall-item .delta-val { font-size: 0.6875rem; font-weight: 600; margin-top: 2px; }
    .bar-positive { background: #10B981; }
    .bar-negative { background: #EF4444; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 24px; }
    th { text-align: left; padding: 8px 12px; background: #f9fafb; border-bottom: 2px solid #e5e7eb; font-size: 0.75rem; text-transform: uppercase; color: #666; }
    td { padding: 8px 12px; border-bottom: 1px solid #f3f4f6; font-size: 0.8125rem; }
    .priority-P1 { color: #EF4444; font-weight: 600; }
    .priority-P2 { color: #FFB800; font-weight: 600; }
    .priority-P3 { color: #64748B; }
    footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid #e5e7eb; font-size: 0.75rem; color: #999; text-align: center; }
    @media print {
      @page {
        margin: 20mm;
        @bottom-center { content: counter(page) " / " counter(pages); font-size: 9pt; color: #999; }
      }
      body { padding: 0; orphans: 3; widows: 3; }
      .pulse-grid { break-inside: avoid; }
      table { break-inside: avoid; }
      .trend-container { break-inside: avoid; }
      .waterfall-container { break-inside: avoid; }
      h2 { break-after: avoid; }
      footer { break-before: always; }
    }
  `;
}
