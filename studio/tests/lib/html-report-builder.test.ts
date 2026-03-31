/**
 * Tests for HTML Report Builder.
 */

import { describe, it, expect } from 'vitest';
import { buildHtmlReport, buildBoardPackReport } from '../../src/lib/report/html-report-builder';
import { renderPulseSection, renderTrendSection, renderWaterfallSection, renderEvidenceSection } from '../../src/lib/report/report-sections';
import { generateReportStyles } from '../../src/lib/report/report-styles';
import type { ThemeConfig } from '../../src/lib/store/project-store';
import { SAMPLE_KPIS, SAMPLE_TREND, SAMPLE_WATERFALL, SAMPLE_EVIDENCE } from '../../src/lib/dashboard/sample-data';

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

const REPORT_DATA = {
  projectName: 'Test Corp',
  kpis: SAMPLE_KPIS,
  trend: SAMPLE_TREND,
  trendLabel: 'Gross Margin',
  waterfall: SAMPLE_WATERFALL,
  evidence: SAMPLE_EVIDENCE,
};

describe('generateReportStyles', () => {
  it('includes theme primary color', () => {
    const css = generateReportStyles(MOCK_THEME);
    expect(css).toContain('#00D4AA');
    expect(css).toContain('8px');
    expect(css).toContain('Inter');
  });

  it('includes print media query', () => {
    const css = generateReportStyles(MOCK_THEME);
    expect(css).toContain('@media print');
  });
});

describe('renderPulseSection', () => {
  it('renders all KPI cards', () => {
    const html = renderPulseSection(SAMPLE_KPIS);
    expect(html).toContain('Gross Margin');
    expect(html).toContain('Net Sales');
    expect(html).toContain('CCC Days');
    expect(html).toContain('OEE %');
  });

  it('includes status classes', () => {
    const html = renderPulseSection(SAMPLE_KPIS);
    expect(html).toContain('status-at-risk');
    expect(html).toContain('status-on-track');
    expect(html).toContain('status-off-track');
  });
});

describe('renderTrendSection', () => {
  it('renders all 12 months', () => {
    const html = renderTrendSection('GM', SAMPLE_TREND);
    expect(html).toContain('Jan');
    expect(html).toContain('Dec');
  });
});

describe('renderWaterfallSection', () => {
  it('renders positive and negative bars', () => {
    const html = renderWaterfallSection(SAMPLE_WATERFALL);
    expect(html).toContain('bar-positive');
    expect(html).toContain('bar-negative');
    expect(html).toContain('Price');
    expect(html).toContain('Volume');
  });
});

describe('renderEvidenceSection', () => {
  it('renders evidence table with priorities', () => {
    const html = renderEvidenceSection(SAMPLE_EVIDENCE);
    expect(html).toContain('DACH Region');
    expect(html).toContain('priority-P1');
    expect(html).toContain('priority-P2');
  });
});

describe('buildHtmlReport', () => {
  it('produces valid HTML document', () => {
    const html = buildHtmlReport(REPORT_DATA, MOCK_THEME);
    expect(html).toContain('<!DOCTYPE html>');
    expect(html).toContain('<html');
    expect(html).toContain('</html>');
    expect(html).toContain('Test Corp');
  });

  it('includes all sections', () => {
    const html = buildHtmlReport(REPORT_DATA, MOCK_THEME);
    expect(html).toContain('KPI Pulse');
    expect(html).toContain('12-Month Trend');
    expect(html).toContain('Margin Bridge');
    expect(html).toContain('Evidence Matrix');
  });
});

describe('buildBoardPackReport', () => {
  it('produces board pack with page breaks', () => {
    const html = buildBoardPackReport([REPORT_DATA], MOCK_THEME, 'Test Corp');
    expect(html).toContain('Board Pack');
    expect(html).toContain('page-break-before');
    expect(html).toContain('Test Corp');
  });
});
